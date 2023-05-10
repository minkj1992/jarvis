import asyncio
import logging
from typing import Any, List

from langchain.callbacks.base import AsyncCallbackHandler, AsyncCallbackManager
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import (CONDENSE_QUESTION_PROMPT,
                                                     QA_PROMPT)
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import VectorStore
from langchain.vectorstores.base import VectorStore

from infra.config import get_config
from infra.jbs4 import extract_doc_metadata_from_url

_cfg = get_config()
_CHAT_OPEN_AI_TIMEOUT=120

DEFAULT_PROMPT_TEMPLATE = """Use the following pieces of context to answer the question at the end in korean. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
!IMPORTANT Answer in korean:"""


async def get_docs_from_texts(texts:str):
    docs = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, separators=["\n\n", "\n", " ", ""])
    for chunk in text_splitter.split_text(texts):
        docs.append(chunk)
    return docs


async def get_docs_and_metadatas_from_urls(urls):
    docs = []
    metadatas = []
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, separators=["\n\n", "\n", " ", ""])
    result = await asyncio.gather(
        *[extract_doc_metadata_from_url(url) for url in urls]
    )
    for (doc, metadata) in result:
        for chunk in text_splitter.split_text(doc):
            docs.append(chunk)
            metadatas.append(metadata)
    return docs, metadatas



async def get_chain(vs: VectorStore, prompt:str)-> ConversationalRetrievalChain:
    qa_prompt = PromptTemplate(template=prompt, input_variables=["context", "question"])
    return ConversationalRetrievalChain.from_llm(
        ChatOpenAI(
            openai_api_key=_cfg.openai_api_key, 
            temperature=0.7, 
            model_name="gpt-3.5-turbo",
            request_timeout=_CHAT_OPEN_AI_TIMEOUT,
        ),
        retriever=vs.as_retriever(search_kwargs={'k':4}),
        qa_prompt=qa_prompt,
    )


class MyChain(ConversationalRetrievalChain):
    async def _aget_docs(self, question: str, inputs: Any):
        try:
            docs = await self.retriever.aget_relevant_documents(question)
            logging.error(f'Question: {question}, Inputs: {inputs}')
        except Exception as err:
            logging.error(err)
            raise err
        result = await self._reduce_tokens_below_limit(docs)
        return result
    
    async def _reduce_tokens_below_limit(self, docs: List[Any]) -> List[Any]:
        num_docs = len(docs)

        if self.max_tokens_limit:
            tokens = [
                self.combine_docs_chain.llm_chain.llm.get_num_tokens(doc.page_content)
                for doc in docs
            ]

            token_count = sum(tokens[:num_docs])
            while token_count > self.max_tokens_limit:
                num_docs -= 1
                token_count -= tokens[num_docs]

        return docs[:num_docs]



async def get_chain_stream(vs: VectorStore, prompt:str, question_handler:AsyncCallbackHandler , stream_handler: AsyncCallbackHandler):
    manager = AsyncCallbackManager([])
    qa_prompt = PromptTemplate(template=prompt, input_variables=["context", "question"])

    question_generator = LLMChain(
        llm=ChatOpenAI(
            openai_api_key=_cfg.openai_api_key,
            temperature=0.7,
            callback_manager=AsyncCallbackManager([question_handler]),
            request_timeout=_CHAT_OPEN_AI_TIMEOUT,
            model_name="gpt-3.5-turbo",
            ),
        prompt=CONDENSE_QUESTION_PROMPT,
        callback_manager=manager,
        verbose=True,
    )
    streaming_llm = ChatOpenAI(
        streaming=True,
        temperature=0.7,
        openai_api_key=_cfg.openai_api_key, 
        callback_manager=AsyncCallbackManager([stream_handler]), 
        request_timeout=_CHAT_OPEN_AI_TIMEOUT,
        model_name="gpt-3.5-turbo",
        verbose=True,
    )
    
    doc_chain = load_qa_chain(
        streaming_llm,
        chain_type="stuff",
        prompt=qa_prompt,
        callback_manager=manager,
    )

    return MyChain(
        retriever=vs.as_retriever(search_kwargs={'k':4}),
        combine_docs_chain=doc_chain,
        question_generator=question_generator,
        callback_manager=manager,
        max_tokens_limit=_cfg.max_token_limit
    )