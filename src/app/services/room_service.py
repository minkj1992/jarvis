import asyncio
import uuid
from enum import Enum, auto
from typing import Any, Dict

from app.exceptions import InvalidRoomInputTypeException
from app.logger import get_logger
from infra import llm, redis
from infra.redis import Room, update_vectorstore

logger = get_logger(__name__)

class RoomInputType(Enum):
    TEXT = auto()
    URL = auto()
    FILE = auto()


async def create_a_room(room_uuid, title, prompt):
    room = redis.Room(uuid=room_uuid, title=title, prompt=prompt)
    await room.save()
    return room_uuid

async def get_a_room(room_uuid) -> Room:
    try:
        room_uuid = uuid.UUID(room_uuid)
    except ValueError:
        return None
    try:
        room = await redis.Room.get(pk=room_uuid)
    except Exception as err:
        await logger.exception(err)
        return None
    return room


async def update_a_room(room_uuid, patch_room_data:Dict[str,str]) -> Room:
    room: Room = await get_a_room(room_uuid)
    for k, v in patch_room_data.items():
        setattr(room, k, v)
    await room.save()
    
    return room


async def delete_a_room(room_uuid) -> int:
    return await redis.Room.delete(pk=room_uuid)

async def get_a_room_chain(room_uuid):
    room = await get_a_room(room_uuid)
    vectorstore = await redis.get_vectorstore(room.uuid)
    return await llm.get_chain(vectorstore, room.prompt)


async def get_a_room_chain_for_stream(room: redis.Room, question_handler, stream_handler):
    vectorstore = await redis.get_vectorstore(room.uuid)
    qa_cahin = await llm.get_chain_stream(vectorstore, room.prompt, question_handler, stream_handler)
    return qa_cahin


async def create_a_room_chain(room_uuid:uuid.UUID, t:RoomInputType, data: Any):
    if t == RoomInputType.TEXT:
        texts = await llm.get_docs_from_texts(data)
        await redis.from_texts(
            docs=texts, 
            metadatas=None, 
            index_name=room_uuid
        )
    elif t == RoomInputType.URL:
        docs, metadatas = await llm.get_docs_and_metadatas_from_urls(data)
        await redis.from_texts(
            docs=docs, 
            metadatas=metadatas, 
            index_name=room_uuid
        )
    elif t == RoomInputType.FILE:
        await redis.from_documents(
            index_name=room_uuid,
            docs=data
        )
    else:
        raise InvalidRoomInputTypeException(t)
    
    return room_uuid
    

async def append_a_room_chain(room_uuid, input_type: RoomInputType, data: str) -> Room:
    if input_type == RoomInputType.TEXT:
        texts = await llm.get_docs_from_texts(data)
        await update_vectorstore(
            room_uuid,
            texts
        )
    elif input_type == RoomInputType.URL:
        docs, metadatas = await llm.get_docs_and_metadatas_from_urls(data)
        await update_vectorstore(
            room_uuid,
            docs,
            metadatas,
        )
    elif input_type == RoomInputType.FILE:
        ...
    else:
        raise Exception("INVALID ROOM INPUT TYPE")    
    return room_uuid


async def change_a_room_chain(room_uuid, input_type: RoomInputType, data: str) -> Room:
    # keep room_uuid for url link 3rd party
    if input_type == RoomInputType.TEXT:
        (texts,_) = await asyncio.gather(
            llm.get_docs_from_texts(data),
            delete_a_room_chain(room_uuid),
        )
        await redis.from_texts(
            docs=texts, 
            metadatas=None, 
            index_name=room_uuid
        )
    elif input_type == RoomInputType.URL:
        ((docs, metadatas), _) = await asyncio.gather(
            llm.get_docs_and_metadatas_from_urls(data),
            delete_a_room_chain(room_uuid),
        )
        await redis.from_texts(
            docs=docs, 
            metadatas=metadatas, 
            index_name=room_uuid
        )
    elif input_type == RoomInputType.FILE:
        ...
    else:
        raise Exception("INVALID ROOM INPUT TYPE")    
    return room_uuid


async def delete_a_room_chain(room_uuid) -> bool:
    return await redis.drop_vectorstore(room_uuid)