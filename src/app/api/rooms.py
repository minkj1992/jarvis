import uuid
from typing import List, Union

from aredis_om.model import NotFoundError
from fastapi import APIRouter, HTTPException, status
from pydantic import UUID4, BaseModel, Field, HttpUrl
from starlette.responses import Response

from app.services import room_service
from infra import ai
from infra.redis import Room, update_vectorstore

router = APIRouter(prefix='/rooms')

class CreateRoomUrlRequest(BaseModel):
    # TODO:
    # partner_uuid: UUID4
    title: str = Field(title="챗봇명")

    urls: List[HttpUrl] = Field(title="챗봇이 학습할 사이트들", description="POST /pages에서 url들을 추출하여 전달하면 된다.")
    
    prompt: Union[str, None] = Field(
        default=ai.DEFAULT_PROMPT_TEMPLATE, 
        title="챗봇이 QA할 prompt",
    )


class RoomResponse(BaseModel):
    room_uuid: UUID4


@router.get("/{pk}", status_code=200)
async def room(pk: str, response: Response):
    try:
        return await Room.get(pk)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Room not found: {pk}")




@router.post(
        "/url", 
        status_code=status.HTTP_202_ACCEPTED,
        response_model=RoomResponse,
        )
async def create_with_url(room_in: CreateRoomUrlRequest,):
    docs, metadatas = await ai.get_docs_and_metadatas_from_urls(room_in.urls)
    room_uuid = await room_service.create_a_room(
        room_in.title,
        room_in.prompt,
        docs,
        metadatas,
        )
    return RoomResponse(room_uuid=room_uuid)



class CreateRoomTextRequest(BaseModel):
    title: str = Field(title="챗봇명")
    texts: str = Field(title="챗봇에게 더 학습시킬 정보")
    
    prompt: Union[str, None] = Field(
        default=ai.DEFAULT_PROMPT_TEMPLATE, 
        title="챗봇이 QA할 prompt",
    )


@router.post(
        "/text", 
        status_code=status.HTTP_202_ACCEPTED,
        response_model=RoomResponse,
        )
async def create_with_text(room_in: CreateRoomTextRequest,):
    docs = await ai.get_docs_from_texts(room_in.texts)
    room_uuid = await room_service.create_a_room(
        room_in.title,
        room_in.prompt,
        docs,
        )
    return RoomResponse(room_uuid=room_uuid)



class UpdateChatRoomRequest(BaseModel):
    texts: str = Field(title="챗봇에게 더 학습시킬 정보")
    


@router.put(
        "/text/{room_uuid}", 
        status_code=status.HTTP_202_ACCEPTED,
        response_model=RoomResponse,)
async def update_a_chat_room(room_uuid: str, chat_in: UpdateChatRoomRequest):
    room_uuid = uuid.UUID(room_uuid)
    texts = await ai.get_docs_from_texts(chat_in.texts)
    await update_vectorstore(
        room_uuid,
        texts
    )
    return RoomResponse(room_uuid=room_uuid)