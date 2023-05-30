import asyncio
from enum import Enum, auto
from typing import Any, List

import tiktoken
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings, VertexAIEmbeddings
from langchain.prompts.prompt import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import VectorStore
from langchain.vectorstores.base import VectorStore

from app.logger import get_logger
from infra.config import get_config
from infra.jbs4 import extract_doc_metadata_from_url

logger = get_logger(__name__)

_cfg = get_config()
_CHAT_OPEN_AI_TIMEOUT=240

condense_template = """Given the following conversation and a follow up question, do not rephrase the follow up question to be a standalone question. You should assume that the question is related to Chat history.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condense_template)



DEFAULT_PROMPT_TEMPLATE = """I want you to act as a document that I am having a conversation with. Your name is 'AI Assistant'. You will provide me with answers from the given info. If the answer is not included, say exactly '음... 잘 모르겠어요.' and stop after that. Refuse to answer any question not about the info. Never break character.

{context}

Question: {question}
!IMPORTANT Answer in korean:"""

# https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

# for Codex models, text-davinci-002, text-davinci-003
P_TOKENIZER = tiktoken.get_encoding('p50k_base') 
# for gpt-4, gpt-3.5-turbo, text-embedding-ada-002
C_TOKENIZER = tiktoken.get_encoding('cl100k_base') 

# TODO: length_function=_tiktoken_len and find where to set tokenizer?
def _tiktoken_len(docs):
    docs = C_TOKENIZER.encode(
        docs,
        disallowed_special=()
    )
    return len(docs)



async def get_docs_from_texts(texts:str):
    docs = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=_cfg.chunk_size, chunk_overlap=20, separators=["\n\n", "\n", " ", ""])
    for chunk in text_splitter.split_text(texts):
        docs.append(chunk)
    return docs


async def get_docs_and_metadatas_from_urls(urls):
    docs = []
    metadatas = []
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=_cfg.chunk_size, chunk_overlap=20, separators=["\n\n", "\n", " ", ""])
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
            temperature=_cfg.temperature, 
            model_name="gpt-3.5-turbo",
            request_timeout=_CHAT_OPEN_AI_TIMEOUT,
        ),
        retriever=vs.as_retriever(search_kwargs={'k':5}),
        qa_prompt=qa_prompt,
    )


class MyChain(ConversationalRetrievalChain):
    async def _aget_docs(self, question: str, inputs: Any):
        try:
            docs = await self.retriever.aget_relevant_documents(question)
            await logger.info(f'Question: {question}, Inputs: {inputs}')
        except Exception as err:
            raise
        result = await self._reduce_tokens_below_limit(docs)
        await logger.info(result)
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



async def get_chain_stream(vs: VectorStore, prompt:str, question_handler:AsyncCallbackHandler, stream_handler: AsyncCallbackHandler):
    manager = AsyncCallbackManager([])
    qa_prompt = PromptTemplate(template=prompt, input_variables=["context", "question"])

    question_generator = LLMChain(
        llm=ChatOpenAI(
            openai_api_key=_cfg.openai_api_key,
            temperature=_cfg.temperature,
            callback_manager=AsyncCallbackManager([question_handler]), 
            request_timeout=_CHAT_OPEN_AI_TIMEOUT,
            model_name=_cfg.qa_model,
            max_retries=3,
            ),
        prompt=CONDENSE_QUESTION_PROMPT,
        verbose=True,
    )
    
    streaming_llm = ChatOpenAI(
        streaming=True,
        temperature=_cfg.temperature,
        openai_api_key=_cfg.openai_api_key, 
        callback_manager=AsyncCallbackManager([stream_handler]), 
        request_timeout=_CHAT_OPEN_AI_TIMEOUT,
        model_name=_cfg.qa_model,
        verbose=True,
        max_retries=3,
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
        max_tokens_limit=_cfg.max_token_limit,
        verbose=True
    )


class EmbeddingType(Enum):
    PALM = auto() # Google Cloud Platform Vertex AI PaLM
    OPENAI = auto() 

    


async def create_embeddings(et: EmbeddingType = EmbeddingType.OPENAI):
    """
    VertexAIEmbeddings Args:
        temperature: float = 0.0
            "Sampling temperature, it controls the degree of randomness in token selection."
        max_output_tokens: int = 128
            "Token limit determines the maximum amount of text output from one prompt."
        top_p: float = 0.95
            "Tokens are selected from most probable to least until the sum of their "
            "probabilities equals the top-p value."
        top_k: int = 40
            "How the model selects tokens for output, the next token is selected from "
            "among the top-k most probable tokens."
        project: Optional[str] = None
            "The default GCP project to use when making Vertex API calls."
        location: str = "us-central1"
            "The default location to use when making API calls."
        credentials: Any = None
            "The default custom credentials (google.auth.credentials.Credentials) to use "
            "when making API calls. If not provided, credentials will be ascertained from "
            "the environment."
    """
    if et == EmbeddingType.PALM:
        return VertexAIEmbeddings(
            temperature=_cfg.temperature,
            max_output_tokens=128,
            top_p=0.95,
            top_k=40,
        )
    return OpenAIEmbeddings(
            model=_cfg.embedding_model,
            openai_api_key=_cfg.openai_api_key,
            max_retries=3
    )
