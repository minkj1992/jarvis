# https://python-dependency-injector.ets-labs.org/examples/fastapi-redis.html

from functools import lru_cache

from aredis_om.connections import get_redis_connection
from aredis_om.model import Field, HashModel
from fastapi.concurrency import run_in_threadpool
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.redis import Redis as RedisVectorStore
from pydantic import UUID4, HttpUrl

from infra import config

cfg = config.get_config()
embeddings = OpenAIEmbeddings(
            model=cfg.openai_model,
            openai_api_key=cfg.openai_api_key, 
            max_retries=3
            )

@lru_cache
def _get_redis_url() -> str:
    return f"redis://:{cfg.redis_password}@{cfg.redis_host}:6379"



async def from_texts(docs, metadatas, index_name):
    return await run_in_threadpool(
        func=RedisVectorStore.from_texts, 
        texts=docs,
        metadatas=metadatas,
        embedding=embeddings,
        index_name=index_name,
        redis_url=_get_redis_url())
    



class Room(HashModel):
    uuid: UUID4 = Field(primary_key=True, index=True)
    title: str
    room_template: str

    class Meta:
        database = get_redis_connection(
            url=_get_redis_url(),
            encoding="utf-8", 
            decode_responses=True
        )

    
    def room_index(self):
        return f'rooms-{self.uuid}'
    
    