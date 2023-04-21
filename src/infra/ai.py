from typing import List

from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS, VectorStore

from infra.config import get_config

_cfg = get_config()

base_condense_question_template = PromptTemplate.from_template(
"""Given the following conversation and a follow up question, 
rephrase the follow up question to be a standalone question.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:""")

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
        

def get_docs_and_metadatas(pages):
    text_splitter = CharacterTextSplitter(chunk_size=1500, separator="\n")
    docs, metadatas = [], []

    text_limit_counter = 0
    for page in pages:
        splits = text_splitter.split_text(page['text'])
        txt_len = sum([len(s) for s in splits])

        if _is_over_limit(text_limit_counter + txt_len):
            break
        docs.extend(splits)
        metadatas.extend([dict(source=page['source'])]* len(splits))
        text_limit_counter += txt_len    

    return docs, metadatas # type hint: tuple(List[str],List[dict])



def to_faiss(txts:List[str], metadatas:List[dict])-> FAISS:
    openai_key = _cfg.openai_api_key
    openai_model=_cfg.openai_model
    
    return FAISS.from_texts(
        txts, 
        OpenAIEmbeddings(
            model=openai_model,
            openai_api_key=openai_key, 
            max_retries=3,
        ), 
        metadatas=metadatas
    )

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


def get_chain(vs: VectorStore, room_template:str):
    llm = OpenAI(temperature=0, openai_api_key=_cfg.openai_api_key)
    return ConversationalRetrievalChain.from_llm(
        llm,
        vs.as_retriever(),
        condense_question_prompt=base_condense_question_template,
        qa_prompt=_from_room_template(room_template),
    )

# maybe websocket
# def chat():
#     qa_chain = get_chain(vec_store)
#     chat_history = [] # TODO: How to manage chat history
#     print(f"Chat with the {HOST} bot:")
#     while True:
#         print("Your question:")
#         question = input()
#         result = qa_chain({"question": question, "chat_history": chat_history})
#         chat_history.append((question, result["answer"]))
#         print(f"AI: {result['answer']}")
