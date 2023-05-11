# https://python-dependency-injector.ets-labs.org/examples/fastapi-redis.html

from functools import lru_cache
from typing import Any, Iterable, List, Optional

from aredis_om.connections import get_redis_connection
from aredis_om.model import Field, HashModel
from fastapi.concurrency import run_in_threadpool
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import BaseRetriever, Document
from langchain.vectorstores.redis import Redis as RedisVectorStore
from langchain.vectorstores.redis import RedisVectorStoreRetriever
from pydantic import UUID4

from infra import config

cfg = config.get_config()


class RedisVectorStoreForAsync(RedisVectorStore):
    def as_retriever(self, **kwargs: Any) -> BaseRetriever:
        return RedisVectorStoreForAysncRetriever(vectorstore=self, **kwargs)

class RedisVectorStoreForAysncRetriever(RedisVectorStoreRetriever):

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return self.get_relevant_documents(query)


@lru_cache
def _get_redis_url() -> str:
    return f"redis://:{cfg.redis_password}@{cfg.redis_host}:6379"



async def from_texts(docs, metadatas, index_name:UUID4):
    return await run_in_threadpool(
        func=RedisVectorStoreForAsync.from_texts, 
        texts=docs,
        metadatas=metadatas,
        embedding=OpenAIEmbeddings(
            model=cfg.openai_model,
            openai_api_key=cfg.openai_api_key, 
            max_retries=3
        ),
        index_name=str(index_name),
        redis_url=_get_redis_url())

async def drop_vectorstore(index_name:UUID4):
    return await run_in_threadpool(
        func=RedisVectorStoreForAsync.drop_index,
        index_name=str(index_name),
        delete_documents=True,
        redis_url=_get_redis_url()
    )


async def get_vectorstore(index_name:UUID4):
    return await run_in_threadpool(
        func=RedisVectorStoreForAsync.from_existing_index,
        embedding=OpenAIEmbeddings(
            model=cfg.openai_model,
            openai_api_key=cfg.openai_api_key, 
            max_retries=3
        ),
        index_name=str(index_name),
        redis_url=_get_redis_url()
    )


async def update_vectorstore(index_name:UUID4, texts: Iterable[str], metadatas: Optional[List[dict]] = None):
    vs = await get_vectorstore(index_name)
    await run_in_threadpool(
        func=vs.add_texts,
        texts=texts,
        metadatas=metadatas,
    )


class Room(HashModel):
    uuid: UUID4 = Field(primary_key=True, index=True)
    title: str
    prompt: str

    class Meta:
        database = get_redis_connection(
            url=_get_redis_url(),
            encoding="utf-8", 
            decode_responses=True
        )
    