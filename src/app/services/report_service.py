import asyncio
import uuid
from enum import Enum, auto
from typing import List

from fastapi import UploadFile

from app.exceptions import InvalidRelationTypeException
from app.logger import get_logger
from app.services import room_service
from infra import llm, redis

logger = get_logger(__name__)

class RelationType(Enum):
    COURTSHIP = 'courtship' # 썸
    COUPLE = 'couple' # 커플, 결혼    
    FRIEND = 'friend' # 친구
    FAMILY = 'family' # 가족
    BUSINESS = 'business' # 비즈니스




async def generate_a_report(room_uuid:str, query: str):
    # TODO: creat a vectorstore with embedding
    vectorstore = await redis.get_vectorstore(room_uuid)
    summary = await llm.get_a_summerize_report(vectorstore, topic=query)
    await logger.info(summary)

    report = await llm.get_a_relationship_report_from_llm(vectorstore, topic=query)
    await logger.info(report)
    return f'summary:{summary}\n\n########################report:{report}'

    
    # flare = await llm.get_a_flare_chain(vectorstore,room.prompt)
    # report = flare.run(query)
    # await logger.info(report)
    # return report

    # if rt == RelationType.COURTSHIP:
    #     ...
    # elif rt == RelationType.COUPLE:
        ## Based on chat history, generate a report based on 4 components.
        # report_uuid = uuid.uuid4()
        # docs:List[Document] = await loader.from_file(file.filename, file.file)
        # await redis.from_documents(report_uuid, docs)
    # else:
    #     raise InvalidRelationTypeException(rt)
    
    