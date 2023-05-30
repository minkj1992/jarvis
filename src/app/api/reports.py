
from typing import List

from aredis_om.model import NotFoundError
from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import UUID4, BaseModel
from starlette.responses import Response
from typing_extensions import Annotated

from app.exceptions import RoomNotFoundException
from app.services import report_service
from app.services.report_service import RelationType
from infra.redis import Room

router = APIRouter(prefix='/reports')


class ReportResponse(BaseModel):
    report_uuid: UUID4


@router.get("/{pk}", status_code=200)
async def get_a_report(pk: str, response: Response):
    try:
        return await Room.get(pk)
    except NotFoundError:
        raise RoomNotFoundException(room_pk=pk)



@router.post(
        "/file", 
        status_code=status.HTTP_201_CREATED,
        response_model=ReportResponse,
        )
async def create_a_report(
        me: Annotated[str, Form(description="내 채팅방 닉네임")], 
        others: Annotated[List[str], Form(description="나를 제외한 채팅방 닉네임들")],
        rt: Annotated[RelationType, Form(description="나와 상대방들의 관계")]=RelationType.COUPLE,
        file: UploadFile=File(...),
    ):
    report_uuid = await report_service.generate_a_report(me, others, rt, file)
    return ReportResponse(report_uuid=report_uuid)
