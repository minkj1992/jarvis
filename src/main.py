import logging

import uvicorn
from fastapi import FastAPI

from app.api import crawl, greet, rooms
from infra.config import get_config

logger = logging.getLogger(__name__)
cfg = get_config()


app = FastAPI(title='Jarvis api server')
# TODO: cors and middleware and logging
app.include_router(greet.router)
app.include_router(crawl.router)
app.include_router(rooms.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Strating Jarvis server...")



@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing Jarvis server...")




if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
