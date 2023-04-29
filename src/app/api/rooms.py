from typing import List, Union

from aredis_om.model import NotFoundError
from fastapi import APIRouter, HTTPException, status
from pydantic import UUID4, BaseModel, Field, HttpUrl
from starlette.responses import Response

from app.services import room_service
from infra import ai
from infra.redis import Room

router = APIRouter(prefix='/rooms')

class CreateRoomRequest(BaseModel):
    # TODO:
    # partner_uuid: UUID4
    title: str = Field(title="챗봇명")

    urls: List[HttpUrl] = Field(title="챗봇이 학습할 사이트들", description="POST /pages에서 url들을 추출하여 전달하면 된다.")
    
    prompt: Union[str, None] = Field(
        default=ai.DEFAULT_PROMPT_TEMPLATE, 
        title="챗봇이 QA할 prompt",
    )


class CreateRoomResponse(BaseModel):
    room_uuid: UUID4


@router.post(
        "/", 
        status_code=status.HTTP_202_ACCEPTED,
        response_model=CreateRoomResponse,
        )
async def create(room_in: CreateRoomRequest,):
    docs, metadatas = await ai.get_docs_and_metadatas(room_in.urls)
    room_uuid = await room_service.create_a_room(
        room_in.title,
        room_in.prompt,
        docs,
        metadatas,
        )
    return CreateRoomResponse(room_uuid=room_uuid)


@router.get("/{pk}", status_code=200)
async def room(pk: str, response: Response):
    try:
        return await Room.get(pk)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Room not found: {pk}")

