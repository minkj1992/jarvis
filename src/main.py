import logging

import aioredis
import uvicorn
from fastapi import FastAPI
from pydantic import BaseSettings

from app.api import greet


class Config(BaseSettings):
    # The default URL expects the app to run using Docker and docker-compose.
    redis_url: str = 'redis://redis:6379'


logger = logging.getLogger(__name__)
cfg = Config()

app = FastAPI(title='Jarvis api server')
redis = aioredis.from_url(cfg.redis_url, decode_responses=True)
app.include_router(greet.router)


@app.on_event("startup")
async def startup():
    aioredis.from_url(cfg.redis_url, encoding="utf8", decode_responses=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
