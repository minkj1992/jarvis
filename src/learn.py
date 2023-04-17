import pickle
from pprint import pprint
from typing import OrderedDict

import requests
import xmltodict
from bs4 import BeautifulSoup
from dotenv import dotenv_values
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS

CFG:OrderedDict = dotenv_values(".env")

def extract_text_from(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    return '\n'.join(line for line in lines if line)

def get_xml():
    sitemap = CFG.get("SITEMAP")
    xml = requests.get(sitemap).text
    return xmltodict.parse(xml)
    
def get_doc_and_metadata(pages):
    max_chunk = 100 # TODO: add quota system
    text_splitter = CharacterTextSplitter(chunk_size=1500, separator="\n")
    docs, metadatas = [], []

    chunk_count = 0
    for page in pages:
        splits = text_splitter.split_text(page['text'])
        if len(splits) + chunk_count > max_chunk: # TODO: add quota system
            break

        docs.extend(splits)
        metadatas.extend([{"source": page['source']}] * len(splits))

        chunk_count += len(splits)
        print(f"Split {page['source']} into {len(splits)} chunks")
    
    return docs, metadatas

def write_to_pickle(docs, metadatas):
    openai_key = CFG.get("OPENAI_API_KEY")
    openai_model="text-embedding-ada-002"
    
    store = FAISS.from_texts(
        docs, 
        OpenAIEmbeddings(
            model=openai_model,
            openai_api_key=openai_key, 
            max_retries=3,
        ), 
        metadatas=metadatas
    )
    with open("faiss_store.pkl", "wb") as f:
        pickle.dump(store, f)

def run(raw_xml):
    MAX_URL_SIZE = 100 # TODO: add quota system
    filter_domain = CFG.get("FILTER")
    urls = raw_xml['urlset']['url'][:MAX_URL_SIZE]
    pages = []
    for i, info in enumerate(urls):
        url = info['loc']
        
        pprint(f'{i}th url: {url}')
        if filter_domain in url:
            pages.append({'text': extract_text_from(url), 'source': url})

    docs, metadatas = get_doc_and_metadata(pages)

    pprint(docs)
    pprint(metadatas)
    write_to_pickle(docs,metadatas)


if __name__ == '__main__':
    raw_xml = get_xml()
    run(raw_xml)
