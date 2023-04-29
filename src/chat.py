import json
import logging
from uuid import UUID

import openai
from fastapi import (FastAPI, HTTPException, Request, WebSocket,
                     WebSocketDisconnect)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

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
    return templates.TemplateResponse("index.html", {"request": request, "room_title": room.title,"room_title": cfg.base_url, "room_uuid": json.dumps(room_uuid)})


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
                logging.error(err)
                # handle 4097 error clear chat_history and retry once again
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
