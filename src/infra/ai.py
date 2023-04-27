from typing import Any, Dict, List

from langchain.callbacks.base import AsyncCallbackManager
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain.chains import ChatVectorDBChain, ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import VectorStore
from langchain.vectorstores.base import VectorStore

from infra.config import get_config
from infra.jbs4 import extract_doc_metadata_from_url

_cfg = get_config()


# langchain_template = """You are an AI assistant for answering questions about {and_domains} {kind_of_site}. 
# You are given the following extracted parts of 
# a long document and a question. Provide a conversational answer.
# If you don't know the answer, just say {dont_know_msg}.
# Don't try to make up an answer. If the question is not about
# {or_domains}, politely inform them that you are tuned
# to only answer questions about {and_domains} topics.
# """

# answer_template = """Question: {question}
# =========
# {context}
# =========
# Answer in Markdown:
# """


# _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

# Chat History:
# {chat_history}
# Follow Up Input: {question}
# Standalone question:"""
# CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)


# # TODO: in korean to variable
# _prompt_template = """You are an language model trained on a specific domain-knowledge website. You are given the following extracted parts of a long document and a question. Use the following pieces of context to answer the question at the end in korean. If you don't know the answer, just say that you don't know, don't try to make up an answer.

# {context}

# Question: {question}
# Answer in Markdown:"""
# QA_PROMPT = PromptTemplate(
#     template=_prompt_template, input_variables=["context", "question"]
# )


prompt_template = """Use the following pieces of context to answer the question at the end in korean. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:"""
QA_PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)



def get_docs_and_metadatas(urls):
    docs = []
    metadatas = []
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, separators=["\n\n", "\n", " ", ""])
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
    # TODO: change promt template
    return ""
    # return langchain_template.format(**langchain_kwargs) + answer_template

# from redis room_template -> to PromtTemplate
def _from_room_template(room_template: str) -> PromptTemplate:
    return PromptTemplate(template=room_template, input_variables=["question", "context"])



# class PrintAsyncCallbackManager(AsyncCallbackManager):
    
#     async def on_chain_start(
#         self,
#         serialized: Dict[str, Any],
#         inputs: Dict[str, Any],
#         verbose: bool = False,
#         **kwargs: Any
#     ) -> None:
#         """Run when chain starts running."""
#         print("###########on_chain_start###########")
#         print(inputs)
#         await super()._handle_event(
#             "on_chain_start", "ignore_chain", verbose, serialized, inputs, **kwargs
#         )
    
#     async def on_chain_error(self, error, verbose: bool = False, **kwargs: Any):
#         return await super().on_chain_error(error, verbose, **kwargs)

#     async def on_chain_end(
#         self, outputs: Dict[str, Any], verbose: bool = False, **kwargs: Any
#     ) -> None:
#         """Run when chain ends running."""
#         print("###########on_chain_end###########")
#         print(outputs)
#         await super()._handle_event(
#             "on_chain_end", "ignore_chain", verbose, outputs, **kwargs
#         )


# https://github.com/hwchase17/chat-langchain/blob/da80049ba8de632e45034aab46e52141b35b5a5c/query_data.py#L13
async def get_chain(vs: VectorStore, room_template:str, question_handler, stream_handler):
    manager = AsyncCallbackManager([])
    # 4097에러 만들어진다.
    # qa_prompt = _from_room_template(room_template)
    # question_gen_llm = ChatOpenAI(
    #     openai_api_key=_cfg.openai_api_key, 
    #     callback_manager=AsyncCallbackManager([question_handler]), 
    #     verbose=True,
    #     max_tokens=_cfg.max_token_limit
    # )

    # question_generator = LLMChain(
    #     llm=question_gen_llm,
    #     prompt=CONDENSE_QUESTION_PROMPT,
        # callback_manager=manager,
    #     verbose=True,
    # )

    question_generator = LLMChain(
        llm=ChatOpenAI(
            openai_api_key=_cfg.openai_api_key,
            temperature=1,
            callback_manager=AsyncCallbackManager([question_handler])
            ),
        prompt=CONDENSE_QUESTION_PROMPT,
        callback_manager=manager,
        verbose=True,
    )
    streaming_llm = ChatOpenAI(
        streaming=True,
        temperature=1,
        openai_api_key=_cfg.openai_api_key, 
        callback_manager=AsyncCallbackManager([stream_handler]), 
        verbose=True,
    )
    
    doc_chain = load_qa_chain(
        streaming_llm,
        chain_type="stuff",
        prompt=QA_PROMPT, 
        callback_manager=manager,
    )

    return ConversationalRetrievalChain(
        retriever=vs.as_retriever(search_kwargs={'k':4}),
        combine_docs_chain=doc_chain,
        question_generator=question_generator,
        callback_manager=manager,
        max_tokens_limit=_cfg.max_token_limit
    )