import asyncio
import logging
import uuid

from infra import ai, redis
from pydantic import UUID4

logger = logging.getLogger(__name__)

async def create_a_room(title, prompt, docs, metadatas=None):
    room_uuid = uuid.uuid4()
    room = redis.Room(uuid=room_uuid, title=title, prompt=prompt)
    
    await asyncio.gather(
        redis.from_texts(docs, metadatas, index_name=room_uuid), 
        room.save()
    )
    return room_uuid

async def get_a_room(room_uuid):
    try:
        room_uuid = uuid.UUID(room_uuid)
    except ValueError:
        return None
    try:
        room = await redis.Room.get(pk=room_uuid)
    except Exception as err:
        logging.error(err)
        return None
    return room



async def get_a_chat_room_stream_chain(room: redis.Room, question_handler, stream_handler):
    vectorstore = await redis.get_vectorstore(room.uuid)
    qa_cahin = await ai.get_chain_stream(vectorstore, room.prompt, question_handler, stream_handler)
    return qa_cahin


async def get_a_chat_room_chain(room_uuid):
    room = await get_a_room(room_uuid)
    vectorstore = await redis.get_vectorstore(room.uuid)
    return await ai.get_chain(vectorstore, room.prompt)