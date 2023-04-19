import logging
from typing import List, Tuple, Union

import requests
import xmltodict
from bs4 import BeautifulSoup
from langchain.text_splitter import CharacterTextSplitter

from infra.config import get_config

cfg = get_config()

def get_sitemap(url) :
    if url[-1] == '/':
        sitemap = f'{url}sitemap.xml'
    else:
        sitemap = f'{url}/sitemap.xml'

    xml = requests.get(sitemap).text
    return xml

def _parse_sitemap(xml:str):
    return xmltodict.parse(xml)
    

def get_urls(xml: str, filter_str: Union[str,None]=None):
    max_crawl_page = cfg.max_crawl_page
    raw_xml = _parse_sitemap(xml)
    urls = raw_xml['urlset']['url']

    if filter_str:
        return [r for r in urls if filter_str in r.get('loc', '')][:max_crawl_page]
    return urls[:max_crawl_page]


# TODO: task with background task
def _extract_text_from(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    return '\n'.join(line for line in lines if line)

# TODO: add quota system
def _is_over_limit(cnt: int)-> bool:
    return cnt >= cfg.max_text_limit 
        

def _get_txts_and_metadata(pages):
    text_splitter = CharacterTextSplitter(chunk_size=1500, separator="\n")
    txts, metadatas = [], []

    text_limit_counter = 0
    for page in pages:
        splits = text_splitter.split_text(page['text'])
        txt_len = sum([len(s) for s in splits])

        if _is_over_limit(text_limit_counter + txt_len):
            break
        txts.extend(splits)
        metadatas.extend([dict(source=page['source'])]* len(splits))
        text_limit_counter += txt_len    
        
    # type hint: tuple(List[str],List[dict])
    return txts, metadatas


def crawl(urls: List[str]):
    pages = []
    for i, url in enumerate(urls):
        logging.info(f"{i}th crawl: {url}")
        p = {'text': _extract_text_from(url), 'source': url} 
        pages.append(p)
    
    return _get_txts_and_metadata(pages)
