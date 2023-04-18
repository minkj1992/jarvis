from datetime import datetime

from fastapi import APIRouter, status

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def greet():
    current_time = datetime.utcnow()
    return {'message':f"Jarvis API Server 🤖(UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})"}


@router.get("/ping", status_code=status.HTTP_200_OK)
async def pong():
    return {"ping": "pong!"}