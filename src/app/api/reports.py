
from typing import Union

from aredis_om.model import NotFoundError
from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import BaseModel, Field

from app.exceptions import RoomNotFoundException
from app.services import report_service, room_service
from app.services.report_service import RelationType
from infra.redis import Room

router = APIRouter(prefix='/reports')


DEFAULT_QUERY = """You will receive a conversation. The conversation format is 'year month day time, speaker: message'.
For example, in '2000, May 3, 3:00 AM, A: Hello', the conversation content is Hello. 
The content of the conversation is the most important. 
View conversation transcripts, analyze content related to the relationship, personality, and intimacy between the two of you, and answer related questions. 
Please answer with reference to all your knowledge in addition to the information given. 
!IMPORTANT Even if you can't analyze it, guess based on your knowledge. answer unconditionally.
"""

DEFAULT_QUESTION = "View conversation transcripts, analyze content related to the relationship, personality, and intimacy between the two of you."

class ReportResponse(BaseModel):
    report: str



class CreateReportRequest(BaseModel):
    query: Union[str, None] = Field(
        default=DEFAULT_QUERY, 
        title="보고서에 질문한 내용",
    )


# TODO: delete room_uuid
@router.post("/{room_uuid}", status_code=200)
async def create_a_report(room_uuid: str, report_in: CreateReportRequest):
    report = await report_service.generate_a_report(room_uuid, report_in.query)
    return ReportResponse(report=report)



# @router.post(
#         "/file", 
#         status_code=status.HTTP_201_CREATED,
#         response_model=ReportResponse,
#         )
# async def create_a_report(
#         me: Annotated[str, Form(description="내 채팅방 닉네임")], 
#         others: Annotated[List[str], Form(description="나를 제외한 채팅방 닉네임들")],
#         rt: Annotated[RelationType, Form(description="나와 상대방들의 관계")]=RelationType.COUPLE,
#         file: UploadFile=File(...),
#     ):
#     report_uuid = await report_service.generate_a_report(me, others, rt, file)
#     return ReportResponse(report_uuid=report_uuid)
