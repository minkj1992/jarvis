import asyncio
import json
import logging
import time
from typing import Dict, List, Union
from uuid import UUID

import aioredis
import openai
from fastapi import (BackgroundTasks, FastAPI, HTTPException, Request,
                     WebSocket, WebSocketDisconnect, status)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.services import room_service
from app.wss.callback import (QuestionGenCallbackHandler,
                              StreamingLLMCallbackHandler)
from app.wss.schemas import ChatResponse
from infra.config import get_config

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
    return templates.TemplateResponse("index.html", {"request": request, "room_title": room.title,"base_url": cfg.base_url, "room_uuid": json.dumps(room_uuid)})

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

    user: User
    utterance: str = Field(title="봇 시스템에 전달된 사용자의 발화입니다.")

class KakaoMessageRequest(BaseModel):
    userRequest: UserRequest

class KakaoMessageResponse(BaseModel):
    msg: str
    chat_id: str



# 채팅 uuid = userUUID + room_uuid
# @router.post(
#         "/kakao/{room_uuid}", 
#         status_code=status.HTTP_202_ACCEPTED,
#         response_model=,
#         )
# async def add_(room_uuid:str, chat_in:KakaoMessageRequest):
#     room = await room_service.get_a_room(room_uuid)
#     if room is None:
#         raise HTTPException(status_code=400, detail=f"Chat room not found  room_uuid : {room_uuid}")
#     return templates.TemplateResponse("index.html", {"request": request, "room_title": room.title,"base_url": cfg.base_url, "room_uuid": json.dumps(room_uuid)})



# REFS: https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
# REFS: https://github.com/hwchase17/chat-langchain/blob/master/main.py
@chat_server.websocket("/{room_uuid}")
async def websocket_endpoint(websocket: WebSocket, room_uuid:str):
    room = await room_service.get_a_room(room_uuid)
    if room is None:
        raise HTTPException(status_code=400, detail=f"Chat room not found  room_uuid : {room_uuid}")
    
    await websocket.accept()
    question_handler = QuestionGenCallbackHandler(websocket)
    stream_handler = StreamingLLMCallbackHandler(websocket)
    chat_history = []

    qa_chain = await room_service.get_a_chat_room_chain(room, question_handler, stream_handler)
    while True:
        try:
            # Receive and send back the client message
            question = await websocket.receive_text()
            resp = ChatResponse(sender="Human", message=question, type="stream")
            await websocket.send_json(resp.dict())

            # Construct a response
            start_resp = ChatResponse(sender="Assistant", message="", type="start")
            await websocket.send_json(start_resp.dict())
            try:
                result = await qa_chain.acall(
                    {"question": question, "chat_history": chat_history}
                )
            except openai.error.InvalidRequestError as err:
                # handle 4097 error clear chat_history and retry once again
                logging.error(err)
                chat_history = []
                result = await qa_chain.acall(
                    {"question": question, "chat_history": chat_history}
                )


            chat_history.append((question, result["answer"]))

            end_resp = ChatResponse(sender="Assistant", message="", type="end")
            await websocket.send_json(end_resp.dict())
        except WebSocketDisconnect:
            logging.info("websocket disconnect")
            break
        except Exception as e:
            logging.error(e, exc_info=True)
            resp = ChatResponse(
                sender="Assistant",
                message="Sorry, something went wrong. Try again.",
                type="error",
            )
            await websocket.send_json(resp.dict())


# 418f786c-5981-481f-bddf-8d0e6f1f07bb
tmp = """

"""


# Redis 클라이언트를 생성합니다.
redis = aioredis.from_url(
    url=cfg.redis_uri, 
    password=cfg.redis_password, 
    encoding="utf-8", 
    decode_responses=True
)



# OpenAI API 키를 설정합니다.
openai.api_key = cfg.openai_api_key
TIME_OUT = 3.5

# OpenAI API를 호출하여 GPT 모델의 응답을 받아옵니다.
async def get_response(redis: aioredis.Redis, chat_id: str, user_message: str,t ) -> str:
    await asyncio.sleep(10)
    response = "10초 뒤의 gpt 응답 테스트"
    await save_chat_response(redis, chat_id, response,t)
    return response

async def get_response_and_store(redis: aioredis.Redis, chat_id: str, user_message: str, t, background_tasks:BackgroundTasks) -> str:
    task = asyncio.ensure_future(get_response(redis, chat_id, user_message,t))
    # 5초 이내에 task가 완료되면 결과를 반환하고,
    # 그렇지 않으면 timeout 예외를 발생시킴
    try:
        chat_response = await asyncio.wait_for(task, timeout=TIME_OUT)
    except asyncio.TimeoutError:
        # timeout이 발생한 경우에 대한 처리
        # 백그라운드로 openai에 다시 요청하고, redis에 저장
        background_tasks.add_task(get_response, redis, chat_id, user_message,t)
        return {'msg': "다시 시도해주세요", 'chat_id': chat_id}
    else:
        # task가 timeout초 이내에 완료된 경우에 대한 처리
        return {'msg': chat_response, 'chat_id': chat_id}


async def save_question(redis: aioredis.Redis, chat_id: str, question: str) -> None:
    redis_chat_id = f"chat:{chat_id}"
    await redis.lpush(redis_chat_id, question)
    await redis.expire(redis_chat_id, 3600)  # 1시간 TTL 설정        

async def save_chat_response(redis: aioredis.Redis, chat_id: str, response: str, t=None) -> None:
    if t:
        print(response, time.time() - t)
    # for background task
    redis_chat_id = f"chat:{chat_id}"
    async with redis.pipeline() as pipe:
        await pipe.lpush(redis_chat_id, response)
        await pipe.execute()


# API endpoint를 정의합니다.
@chat_server.post(
        "/kakao/{room_uuid}", 
        status_code=status.HTTP_202_ACCEPTED,
        response_model=KakaoMessageResponse,
        )
async def chat(room_uuid:str, chat_in:KakaoMessageRequest, background_tasks:BackgroundTasks) -> str:
    start_time = time.time()
    user_id = chat_in.userRequest.user.properties['appUserId']
    user_message = chat_in.userRequest.utterance
    chat_id = f"{room_uuid}:{user_id}"
    
    await save_question(redis, chat_id, user_message)
    response = await get_response_and_store(redis, chat_id, user_message, start_time, background_tasks)
    print(response, time.time() - start_time)
    return KakaoMessageResponse(**response)















async def get_chat_history(chat_id:str):
    # 10 history
    redis_chat_id = f"chat:{chat_id}"
    return await redis.lrange(redis_chat_id, 0, 9)


@chat_server.get("/kakao/{chat_id}/history")
async def chat_history(chat_id: str) -> List[str]:
    chat_history = await get_chat_history(chat_id)
    return [msg for msg in chat_history]
