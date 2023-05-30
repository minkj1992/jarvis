import uuid
from enum import Enum, auto
from typing import List

from fastapi import UploadFile
from langchain.docstore.document import Document

from app.exceptions import InvalidRelationTypeException
from app.logger import get_logger
from app.services import room_service
from infra import loader, redis

logger = get_logger(__name__)

class RelationType(Enum):
    CRUSH = 'crush' # 썸
    COUPLE = 'couple' # 커플, 결혼    
    FRIEND = 'friend' # 친구
    FAMILY = 'family' # 가족
    BUSINESS = 'business' # 비즈니스

async def create_a_report_chain(report_uuid:uuid.UUID, docs: List[Document]):
    await redis.from_documents(
        index_name=report_uuid,
        docs=docs,       
    )




async def generate_a_report(me: str, others: List[str], rt: RelationType, file: UploadFile):
    # Based on chat history, generate a report based on 4 components.
    report_uuid = uuid.uuid4()
    docs:List[Document] = await loader.from_file(file.filename, file.file)
    
    if rt == RelationType.CRUSH:
        ...
    elif rt == RelationType.COUPLE:
        await redis.from_documents_with_palm(report_uuid, docs)
    else:
        raise InvalidRelationTypeException(rt)
    
    return report_uuid
    