import logging
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.services import room_service
from app.wss.callback import (QuestionGenCallbackHandler,
                              StreamingLLMCallbackHandler)
from app.wss.schemas import ChatResponse

chat_server = FastAPI()
chat_server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO: https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
# TODO: https://github.com/hwchase17/chat-langchain/blob/master/main.py
@chat_server.websocket("/{room_uuid}")
async def websocket_endpoint(websocket: WebSocket, room_uuid:str):
    await websocket.accept()
    question_handler = QuestionGenCallbackHandler(websocket)
    stream_handler = StreamingLLMCallbackHandler(websocket)
    chat_history = []
    room_uuid = UUID(room_uuid)

    # chat uuid
    qa_chain = await room_service.get_a_chat_room(room_uuid, question_handler, stream_handler)
    

    while True:
        try:
            # Receive and send back the client message
            question = await websocket.receive_text()
            resp = ChatResponse(sender="you", message=question, type="stream")
            await websocket.send_json(resp.dict())

            # Construct a response
            start_resp = ChatResponse(sender="bot", message="", type="start")
            await websocket.send_json(start_resp.dict())

            # result = qa_chain(
            #                 {"question": question, "chat_history": chat_history}
            #             )

            result = await qa_chain.acall(
                {"question": question, "chat_history": chat_history}
            )
            chat_history.append((question, result["answer"]))

            end_resp = ChatResponse(sender="bot", message="", type="end")
            await websocket.send_json(end_resp.dict())
        except WebSocketDisconnect:
            logging.info("websocket disconnect")
            break
        except Exception as e:
            logging.error(e)
            resp = ChatResponse(
                sender="bot",
                message="Sorry, something went wrong. Try again.",
                type="error",
            )
            await websocket.send_json(resp.dict())
