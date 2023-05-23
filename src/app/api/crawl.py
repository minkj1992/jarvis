from typing import List, Union

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from infra import jbs4

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
    xml = jbs4.get_sitemap(crawl_in.url)
    if xml is None:
        raise HTTPException(status_code=400, detail=f"sitemap을 찾을 수 없습니다. url: {crawl_in.url}")
    urls = jbs4.get_urls(xml, crawl_in.filter_str)
    return urls
