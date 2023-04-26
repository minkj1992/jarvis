from typing import List

from langchain.callbacks.base import AsyncCallbackManager
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import VectorStore
from langchain.vectorstores.base import VectorStore

from infra.bs4 import extract_doc_metadata_from_url
from infra.config import get_config

_cfg = get_config()

langchain_template = """You are an AI assistant for answering questions about {and_domains} {kind_of_site}. 
You are given the following extracted parts of 
a long document and a question. Provide a conversational answer.
If you don't know the answer, just say {dont_know_msg}.
Don't try to make up an answer. If the question is not about
{or_domains}, politely inform them that you are tuned
to only answer questions about {and_domains} topics.
"""

answer_template = """Question: {question}
=========
{context}
=========
Answer in Markdown:
"""

# TODO: add quota system
def _is_over_limit(cnt: int)-> bool:
    return cnt >= _cfg.max_text_limit 
        

def get_docs_and_metadatas(urls):
    docs = []
    metadatas = []
    
    text_splitter = CharacterTextSplitter(chunk_size=1500, separator="\n")
    for url in urls:
        doc, metadata = extract_doc_metadata_from_url(url)
        for chunk in text_splitter.split_text(doc):
            docs.append(chunk)
            metadatas.append(metadata)
    return docs, metadatas


# to room_template
def to_room_template(kind_of_site:str, domains:List[str], dont_know_msg:str) -> str:
    langchain_kwargs = {
        "kind_of_site": kind_of_site,
        "or_domains": ' or '.join(domains) + ' topics',
        "and_domains":' and '.join(domains),
        "dont_know_msg": dont_know_msg,
    }
    return langchain_template.format(**langchain_kwargs) + answer_template

# from redis room_template -> to PromtTemplate
def _from_room_template(room_template: str) -> PromptTemplate:
    return PromptTemplate(template=room_template, input_variables=["question", "context"])


# https://github.com/hwchase17/chat-langchain/blob/da80049ba8de632e45034aab46e52141b35b5a5c/query_data.py#L13
async def get_chain(vs: VectorStore, room_template:str, question_handler, stream_handler):
    manager = AsyncCallbackManager([])
    question_manager = AsyncCallbackManager([question_handler])
    stream_manager = AsyncCallbackManager([stream_handler])
    qa_prompt = _from_room_template(room_template)

    question_gen_llm = OpenAI(
        temperature=0, 
        openai_api_key=_cfg.openai_api_key, 
        callback_manager=question_manager, 
        verbose=True,
    )
    streaming_llm = OpenAI(
        temperature=0, 
        streaming=True, 
        openai_api_key=_cfg.openai_api_key, 
        callback_manager=stream_manager, 
        verbose=True,
    )

    question_generator = LLMChain(
        llm=question_gen_llm,
        prompt=CONDENSE_QUESTION_PROMPT,
        callback_manager=manager,
    )
    doc_chain = load_qa_chain(
        streaming_llm, 
        chain_type="stuff", 
        prompt=qa_prompt, 
        callback_manager=manager,
    )

    
    return ConversationalRetrievalChain(
        retriever=vs.as_retriever(),
        combine_docs_chain=doc_chain,
        question_generator=question_generator,
        callback_manager=manager,
    )
