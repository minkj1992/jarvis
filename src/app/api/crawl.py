import logging
from datetime import datetime
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from infra import bs4

router = APIRouter(prefix='/pages')


class CrawlingPageRequest(BaseModel):
    url: HttpUrl
    filter_str: Union[str, None] = Field(
        default=None, title="Include urls when matches with filter_str."
    )

@router.post(
        "", 
        status_code=status.HTTP_200_OK,
        response_model=List[str],
        )
async def get_pages(crawl_in: CrawlingPageRequest,):
    xml = bs4.get_sitemap(crawl_in.url)
    if xml is None:
        raise HTTPException(status_code=400, detail=f"sitemap을 찾을 수 없습니다. url: {crawl_in.url}")
    urls = bs4.get_urls(xml, crawl_in.filter_str)
    return urls
