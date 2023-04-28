from datetime import datetime

from fastapi import APIRouter, status

from infra.config import get_config

router = APIRouter()
cfg = get_config()


@router.get("/", status_code=status.HTTP_200_OK)
async def greet():
    current_time = datetime.utcnow()
    return {'message':f"Jarvis API Server ({cfg.phase}) 🤖(UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})"}


@router.get("/ping", status_code=status.HTTP_200_OK)
async def pong():
    return {"ping": "pong!"}
