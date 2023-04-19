import logging
import uuid
from datetime import datetime
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, status
from pydantic import UUID4, BaseModel, Field, HttpUrl

from infra import bs4, gpt

router = APIRouter(prefix='/rooms')

class CreateRoomRequest(BaseModel):
    # TODO:
    # partner_uuid: UUID4
    title: str = Field(title="챗봇명")

    urls: List[HttpUrl] = Field(title="챗봇이 학습할 사이트들", description="POST /pages에서 url들을 추출하여 전달하면 된다.")
    
    # TODO: enum
    kind_of_site: Union[str, None] = Field(
        default="blog", title="챗봇이 학습할 사이트 형태", description="예를 들면 블로그, 뉴스, 회사소개 등과 같이 전달해주면 된다."
    )
    domains: List[str] = Field(
        default=[], 
        title="챗봇이 학습할 사이트가 다루고 있는 키워드 또는 관련 주제", 
        description='예를들면 다음과 같이 전달해주면 된다. ["blockchain", "IT trend", "software develop"]'
    )
    dont_know_message: Union[str, None] = Field(
        default="Hmm, I'm not sure.", title="챗봇이 잘 모를때 반응 문구", description="챗봇이 학습한 내용과 관련이 없거나, 챗봇이 알 수 없는 질문을 할 경우 답변 양식입니다."
    )


class CreateRoomResponse(BaseModel):
    room_uuid: UUID4


@router.post(
        "/", 
        status_code=status.HTTP_202_ACCEPTED,
        response_model=CreateRoomResponse,
        )
async def create(room_in: CreateRoomRequest,):
    txt, metadatas = bs4.crawl(room_in.urls)
    vec_store = gpt.to_faiss(txt, metadatas)
    room_template: str = gpt.to_room_template(
        room_in.kind_of_site,
        room_in.domains,
        room_in.dont_know_message,
    )

    # TODO: save to redis
    # 1. generate uuid
    # 2. input all
    # 3. generate question format
    # 4. save it to redis
    
    # TODO: with background
    # room_uuid = room_service.create_a_room(
    #     room_uuid, 
    #     room_in.title,
    #     room_template,
    #     vec_store,
    #     )

    # TODO: change room_uuid
    return CreateRoomResponse(room_uuid=uuid.uuid4())

    
