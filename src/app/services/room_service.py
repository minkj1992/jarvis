import asyncio
import logging
import uuid

from infra import redis

logger = logging.getLogger(__name__)

async def create_a_room(title, room_template, docs, metadatas):
    room_uuid = uuid.uuid4()
    room = redis.Room(uuid=room_uuid, title=title, room_template=room_template)
    
    await asyncio.gather(
            redis.from_texts(docs, metadatas, index_name=str(room_uuid)), 
            room.save())

    return room_uuid

