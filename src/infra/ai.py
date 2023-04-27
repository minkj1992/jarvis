from langchain.callbacks.base import AsyncCallbackHandler, AsyncCallbackManager
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT
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


DEFAULT_PROMPT_TEMPLATE = """Use the following pieces of context to answer the question at the end in korean. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
!IMPORTANT Answer in korean:"""



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


async def get_chain(vs: VectorStore, prompt:str, question_handler:AsyncCallbackHandler , stream_handler: AsyncCallbackHandler):
    manager = AsyncCallbackManager([])
    qa_prompt = PromptTemplate(template=DEFAULT_PROMPT_TEMPLATE, input_variables=["context", "question"])

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
        prompt=qa_prompt, 
        callback_manager=manager,
    )

    return ConversationalRetrievalChain(
        retriever=vs.as_retriever(search_kwargs={'k':4}),
        combine_docs_chain=doc_chain,
        question_generator=question_generator,
        callback_manager=manager,
        max_tokens_limit=_cfg.max_token_limit
    )