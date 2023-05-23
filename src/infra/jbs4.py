
from typing import Union

import requests
import xmltodict
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from infra.config import get_config

cfg = get_config()


def get_fake_user_agent_header():
    ua = UserAgent()
    return {
        'User-Agent': ua.random
    }

headers = get_fake_user_agent_header()

def get_sitemap(url) :
    if url[-1] == '/':
        sitemap = f'{url}sitemap.xml'
    else:
        sitemap = f'{url}/sitemap.xml'
    
    xml = requests.get(sitemap, headers=get_fake_user_agent_header()).text
    return xml



def _parse_sitemap(xml:str):
    return xmltodict.parse(xml)
    

def get_urls(xml: str, filter_str: Union[str,None]=None):
    max_crawl_page = cfg.max_crawl_page
    raw_xml = _parse_sitemap(xml)
    raw_urls = raw_xml['urlset']['url']

    if filter_str:
        urls = [r for r in raw_urls if filter_str in r.get('loc', '')][:max_crawl_page]
    else:
        urls = raw_urls[:max_crawl_page]
    
    return [u.get('loc', '') for u in urls]

def _get_content(raw_content):
    # TypeError: 'NoneType' object is not subscriptable
    try:
        return raw_content['content']
    except TypeError:
        return None


async def extract_doc_metadata_from_url(url):
    # URL에서 HTML 문서를 가져옵니다.
    response = requests.get(url, headers=headers)
    html = response.content

    # HTML 문서에서 metadata를 추출합니다.
    soup = BeautifulSoup(html, 'html.parser')
    try:
        title = soup.find('title').get_text()
    except AttributeError:
        title = ''

    # HTML에서 javascript, css 태그 제거
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()


    # 줄 바꿈 문자 제거 및 스페이스로 대체
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    doc = '\n'.join(chunk for chunk in chunks if chunk)


    # 추출한 문서와 metadata를 반환합니다.
    metadata = {
        "source": url,
        "title": title
    }
    return doc, metadata
