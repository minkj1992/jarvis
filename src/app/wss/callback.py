"""Callback handlers used in the app."""
from typing import Any, Dict, List

from fastapi import WebSocketDisconnect
from langchain.callbacks.base import AsyncCallbackHandler
from starlette.websockets import WebSocketDisconnect
from websockets import ConnectionClosed

from app.logger import get_logger
from app.utils import wss_close_ignore_exception
from app.wss.schemas import ChatResponse

logger = get_logger(__name__)


class StreamingLLMCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming LLM responses."""

    def __init__(self, websocket):
        self.websocket = websocket

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        # chat gpt에게 응답이 오는 token 갯수 만큼 호출된다.
        resp = ChatResponse(sender="Assistant", message=token, type="stream")
        try:
            await self.websocket.send_json(resp.dict())
        except (WebSocketDisconnect, ConnectionClosed):
            pass
        except Exception as ex:
            await logger.exception(ex)



class QuestionGenCallbackHandler(AsyncCallbackHandler):
    """Callback handler for question generation."""

    def __init__(self, websocket):
        self.websocket = websocket

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        resp = ChatResponse(
            sender="Assistant", message="Synthesizing question...", type="info"
        )
        try:
            await self.websocket.send_json(resp.dict())
        except (WebSocketDisconnect, ConnectionClosed):
            pass
        except Exception as e:
            await logger.exception(e)

