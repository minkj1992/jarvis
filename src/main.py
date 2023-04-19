import aioredis
import uvicorn
from fastapi import FastAPI

from app.api import crawl, greet, rooms
from infra.config import get_config

cfg = get_config()
app = FastAPI(title='Jarvis api server')

redis = aioredis.from_url(cfg.redis_uri, decode_responses=True)
app.include_router(greet.router)
app.include_router(crawl.router)
app.include_router(rooms.router)


@app.on_event("startup")
async def startup():
    aioredis.from_url(cfg.redis_uri, encoding="utf8", decode_responses=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
