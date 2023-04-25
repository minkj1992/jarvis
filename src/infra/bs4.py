import logging
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


# TODO: task with background task
def _extract_text_from(url, headers):
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    return '\n'.join(line for line in lines if line)



def crawl(urls: List[str]):
    headers = get_fake_user_agent_header()
    pages = []
    for i, url in enumerate(urls):
        logging.info(f"{i}th crawl: {url}")
        p = {'text': _extract_text_from(url, headers), 'source': url} 
        pages.append(p)
    return pages
