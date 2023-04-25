import asyncio
import logging
import uuid

from pydantic import UUID4

from infra import ai, redis

logger = logging.getLogger(__name__)

async def create_a_room(title, room_template, docs, metadatas):
    room_uuid = uuid.uuid4()
    room = redis.Room(uuid=room_uuid, title=title, room_template=room_template)
    
    await asyncio.gather(
            redis.from_texts(docs, metadatas, index_name=room_uuid), 
            room.save())

    return room_uuid

async def is_room_exist(room_uuid):
    try:
        room_uuid = uuid.UUID(room_uuid)
    except ValueError:
        return False

    try:
        _ = await redis.Room.get(room_uuid)
    except Exception as err:
        logging.error(err)
        return False
    
    return True



async def get_a_chat_room(room_uuid: UUID4, question_handler, stream_handler):
    # 1. get a room template from redis
    # 2. get a room vectore store from redis
    room = await redis.Room.get(room_uuid)
    vectorstore = await redis.get_vectorstore(room_uuid)

    return await ai.get_chain(vectorstore, room.room_template, question_handler, stream_handler)
