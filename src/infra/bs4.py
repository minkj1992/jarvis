import logging
import re
from typing import List, Union

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





def extract_doc_metadata_from_url(url):
    # URL에서 HTML 문서를 가져옵니다.
    response = requests.get(url, headers=headers)
    html = response.text

    # HTML 문서에서 metadata를 추출합니다.
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title').get_text()

    r_author = soup.find('meta', attrs={'name': 'author'})
    r_date = soup.find('meta', attrs={'name': 'date'})
    r_category = soup.find('meta', attrs={'name': 'category'})
    tags = [_get_content(tag) for tag in soup.find_all('meta', attrs={'name': 'tags'})]


    # HTML 문서에서 본문을 추출합니다.
    # 본문 추출을 위해, HTML 태그들을 제거합니다.
    text = soup.get_text()
    text = re.sub(r'<.*?>', '', text)

    # 추출한 문서와 metadata를 반환합니다.
    doc = text.strip()
    metadata = [
        title, 
        _get_content(r_author), 
        _get_content(r_date), 
        _get_content(r_category)
    ] + tags
    metadata = [m for m in metadata if m]
    metadata = ' '.join(metadata)

    return doc, metadata

