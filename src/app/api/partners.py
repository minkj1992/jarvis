import logging
from typing import List, Union

from aredis_om.model import NotFoundError
from fastapi import APIRouter, Request, status
from pydantic import UUID4, BaseModel, Field, HttpUrl
from starlette.responses import JSONResponse, Response

router = APIRouter(prefix='/partners')

class CreatePartnerRequest(BaseModel):
    partner_uuid: str = Field(title="유저 uuid")

    email: List[HttpUrl] = Field(title="유저 email")
    
    name: Union[str, None] = Field(
        title="유저 이름",
    )


class RoomResponse(BaseModel):
    room_uuid: UUID4


@router.post("/signin", status_code=status.HTTP_200_OK)
async def signin(partner_in: CreatePartnerRequest):
    logging.error(partner_in)
    ...

@router.post("/signout", status_code=status.HTTP_201_CREATED)
async def signout(pk: str, response: Response):
    ...


@router.post("/pay/callback", status_code=status.HTTP_200_OK)
async def pay_callback(request: Request):
    # i.g) b'state=1&errorMessage=&mul_no=2000&payurl=http%3A%2F%2Fpayapp.kr%2F000000000000'
    pay_in = await request.body()
    logging.error(pay_in)
    return JSONResponse("SUCCESS")



@router.post("/signin", status_code=status.HTTP_200_OK)
async def pay_callback(partner_in: CreatePartnerRequest):
    
    ...


@router.post("/refund/callback", status_code=status.HTTP_200_OK)
async def refund_callback(pk: str, response: Response):
    # update token 갯수 /month
    # acc
    ...

