import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Union

import aioredis
import openai
import websockets
from fastapi import (BackgroundTasks, FastAPI, HTTPException, Request,
                     WebSocket, WebSocketDisconnect, status)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.services import room_service
from app.wss.callback import (QuestionGenCallbackHandler,
                              StreamingLLMCallbackHandler)
from app.wss.schemas import ChatResponse
from infra.config import get_config

DEFAULT_CALLBACK_MSG = '생각이다 정리됐니 🤔?'
DEFAULT_KAKAO_TIMEOUT_MSG = f"⚠️ 죄송합니다 5초만 더 생각할 시간을 주세요.\n5초가 지났으면 저를 클릭해주시고, 아래버튼에서 아래 문구를 눌러주세요.\n\n'{DEFAULT_CALLBACK_MSG}'"
DEFAULT_CALLBACK_UNPREPARED_MSG = '⚠️ 아직 생각이 정리되지 않았습니다. 혹시 5초가 지났을까요?'
cfg = get_config()
chat_server = FastAPI()
chat_server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory="templates")


@chat_server.get("/{room_uuid}")
async def get(request: Request, room_uuid:str):
    room = await room_service.get_a_room(room_uuid)
    if room is None:
        raise HTTPException(status_code=400, detail=f"Chat room not found  room_uuid : {room_uuid}")
    return templates.TemplateResponse("index.html", {"request": request, "room_title": room.title,"base_url": cfg.base_url, "room_uuid": str(room_uuid)})

@chat_server.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class UserRequest(BaseModel):
    class User(BaseModel):
        id: str = Field(
            title="사용자를 식별할 수 있는 key.", 
            description="1. 사용자를 식별할 수 있는 key로 최대 70자의 값을 가지고 있습니다.\n2. 이 값은 특정한 bot에서 사용자를 식별할 때 사용할 수 있습니다.\n3. 동일한 사용자더라도, 봇이 다르면 다른 id가 발급됩니다.")
        type: str = Field("챗봇 skil 타입", description="현재는 botUserKey만 제공합니다.")
        properties: Dict[str, str]  = Field(
            default={},
            title="추가적으로 제공하는 사용자의 속성 정보입니다.",
            description="https://i.kakao.com/docs/skill-response-format#userproperties"
    )
        
    class Block(BaseModel):
        id: str = Field(title="블록을 식별할 수 있는 id")

    user: User
    callback_url: Union[str, None] = Field(
        default=None, 
        title="kakao callback url",
        description="callback인 경우, url이 담겨져 옵니다.",
    )
    utterance: str = Field(title="봇 시스템에 전달된 사용자의 발화입니다.")


class KakaoMessageRequest(BaseModel):
    userRequest: UserRequest


# Redis 클라이언트를 생성합니다.
redis = aioredis.from_url(
    url=cfg.redis_uri, 
    password=cfg.redis_password, 
    encoding="utf-8", 
    decode_responses=True
)


# OpenAI API를 호출하여 GPT 모델의 응답을 받아옵니다.
# 시간 절약을 위해 chat_history는 비웁니다.
async def get_response(redis: aioredis.Redis, chat_id: str, user_message: str, room_uuid:str, retry=False) -> str:
    chain = await room_service.get_a_room_chain(room_uuid)
    result = await chain.acall({"question": user_message, "chat_history": []})
    answer = result.get('answer')
    if retry:
        await save_chat_response(redis, chat_id, answer)
    return answer

async def get_response_callback(redis: aioredis.Redis, chat_id: str, user_message: str, background_tasks:BackgroundTasks, room_uuid:str, start_time=None) -> str:
    redis_response = await get_chat_response(redis, chat_id)
    if redis_response:
        return f'✅ {redis_response}'
    return DEFAULT_CALLBACK_UNPREPARED_MSG

async def get_response_and_store(redis: aioredis.Redis, chat_id: str, user_message: str, background_tasks:BackgroundTasks, room_uuid:str, start_time=None) -> str:
    task = asyncio.ensure_future(get_response(redis, chat_id, user_message, room_uuid))
    # 5초 이내에 task가 완료되면 결과를 반환하고,
    # 그렇지 않으면 timeout 예외를 발생시킴
    timeout=(start_time+cfg.kakao_time_out)-time.time()
    logging.error(f"timeout: {timeout}")
    try:
        chat_response = await asyncio.wait_for(task, timeout=timeout)
    except asyncio.TimeoutError:
        # timeout이 발생한 경우에 대한 처리
        # 백그라운드로 openai에 다시 요청하고, redis에 저장
        # TODO: 이걸 막기위해서는 처음부터 background task로 처리하면서 callback으로 이 시점에 알아야 하는데 마땅치 않기 때문에 while로 redis에 값이 있는지 확인해야 한다.
        background_tasks.add_task(get_response, redis, chat_id, user_message, room_uuid, True)
        return DEFAULT_KAKAO_TIMEOUT_MSG
    else:
        # task가 timeout초 이내에 완료된 경우에 대한 처리
        return f'✅ {chat_response}'


async def save_chat_response(redis: aioredis.Redis, chat_id: str, response: str) -> None:
    # for background task
    redis_chat_id = f"chat:{chat_id}"
    async with redis.pipeline() as pipe:
        await pipe.lpush(redis_chat_id, response)
        await pipe.expire(redis_chat_id, 600) # 10분
        await pipe.execute()

async def get_chat_response(redis: aioredis.Redis, chat_id: str) -> None:
    redis_chat_id = f"chat:{chat_id}"
    return await redis.lpop(redis_chat_id)

class KakaoMessageResponse(BaseModel):
    version: str
    template: Any


# API endpoint를 정의합니다.
@chat_server.post(
        "/kakao/{room_uuid}", 
        status_code=status.HTTP_202_ACCEPTED,
        response_model=KakaoMessageResponse,
        )
async def chat(room_uuid:str, chat_in:KakaoMessageRequest, background_tasks:BackgroundTasks) -> str:
    #     room = await room_service.get_a_room(room_uuid)
    #     if room is None:
    #         raise HTTPException(status_code=400, detail=f"Chat room not found  room_uuid : {room_uuid}")
    #     return templates.TemplateResponse("index.html", {"request": request, "room_title": room.title,"base_url": cfg.base_url, "room_uuid": json.dumps(room_uuid)})

    # TODO: 친구가 아닐 경우, 로직처리
    start_time = time.time()
    
    is_friend = True if chat_in.userRequest.user.properties.get('isFriend') else False
    user_id = chat_in.userRequest.user.properties.get('botUserKey', "UERkbohv5xgP")
    user_message = chat_in.userRequest.utterance
    chat_id = f"{room_uuid}:{user_id}"

    logging.error("Kakao User properties: %s", chat_in.userRequest.user.properties)
    logging.error(f"Kakao Chat id: {chat_id}")

    response = await get_response_and_store(redis, chat_id, user_message, background_tasks, room_uuid, start_time=start_time)
    return KakaoMessageResponse(
        version="2.0",
        template= {
            "outputs": [
                {
                    "simpleText": {
                        "text": response,
                        
                    }
                }
            ]
        }
    )

# API endpoint를 정의합니다.
@chat_server.post(
        "/kakao/{room_uuid}/callback", 
        status_code=status.HTTP_202_ACCEPTED,
        response_model=KakaoMessageResponse,
        )
async def callback_chat(room_uuid:str, chat_in:KakaoMessageRequest, background_tasks:BackgroundTasks) -> str:    
    user_id = chat_in.userRequest.user.properties.get('botUserKey', "UERkbohv5xgP")
    user_message = chat_in.userRequest.utterance
    is_callback = True if chat_in.userRequest.callback_url else False
    chat_id = f"{room_uuid}:{user_id}"

    logging.error("Kakao User properties: %s", chat_in.userRequest.user.properties)
    logging.error(f"Kakao Chat id: {chat_id}")
    logging.error(f"Kakao is_callback: {is_callback}")

    response = await get_response_callback(redis, chat_id, user_message, background_tasks, room_uuid)
    return KakaoMessageResponse(
        version="2.0",
        template= {
            "outputs": [
                {
                    "simpleText": {
                        "text": response,
                        
                    }
                }
            ]
        }
    )



async def get_chat_history(chat_id:str):
    # 10 history
    redis_chat_id = f"chat:{chat_id}"
    return await redis.lrange(redis_chat_id, 0, 9)


@chat_server.get("/kakao/{chat_id}/history")
async def chat_history(chat_id: str) -> List[str]:
    chat_history = await get_chat_history(chat_id)
    return [msg for msg in chat_history]


@chat_server.websocket("/{room_uuid}")
async def websocket_endpoint(websocket: WebSocket, room_uuid:str):
    room = await room_service.get_a_room(room_uuid)
    if room is None:
        raise HTTPException(status_code=400, detail=f"Chat room not found  room_uuid : {room_uuid}")
    
    await websocket.accept()
    question_handler = QuestionGenCallbackHandler(websocket)
    stream_handler = StreamingLLMCallbackHandler(websocket)

    qa_chain = await room_service.get_a_room_chain_for_stream(room, question_handler, stream_handler)
    
    try:
        while websocket.client_state == WebSocketState.CONNECTED:        
            # Receive and send back the client message
            client_msg = await websocket.receive_text()

            resp = ChatResponse(sender="Human", message=client_msg, type="stream")
            await websocket.send_json(resp.dict())

            # 1. Send Chat start message
            start_resp = ChatResponse(sender="Assistant", message="", type="start")
            await websocket.send_json(start_resp.dict())
            
            # 2. Generate Chat Response

            result = await qa_chain.acall(
                {"question": client_msg, "chat_history": []}
            )

            # 3. Send Chat end message
            end_resp = ChatResponse(sender="Assistant", message="", type="end")
            await websocket.send_json(end_resp.dict())
    except WebSocketDisconnect:
        logging.error("websocket disconnect")
    except Exception as e:
        logging.error(e, exc_info=True)

