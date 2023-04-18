import pickle
from typing import OrderedDict

from dotenv import dotenv_values
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import OpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.vectorstores import VectorStore

_cfg:OrderedDict = dotenv_values(".env")
HOST: str = _cfg.get("TARGET_DOMAIN")
OPENAI_API_KEY = _cfg.get("OPENAI_API_KEY")

gpt_question_template = """Given the following conversation and a follow up question, 
rephrase the follow up question to be a standalone question.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(gpt_question_template)


_domain = ["blockchain", "IT trend", "software develop"]
KIND_OF_SITE = "blog"
DOMAIN_AND_QUESTION = ' and '.join(_domain)
DOMAIN_OR_QUESTION = ' or '.join(_domain) + ' topics'
DONT_KNOW_PATTERN = "Hmm, I'm not sure."

langchain_should_know = f"""You are an AI assistant for answering questions about {DOMAIN_AND_QUESTION} {KIND_OF_SITE}. 
You are given the following extracted parts of 
a long document and a question. Provide a conversational answer.
If you don't know the answer, just say {DONT_KNOW_PATTERN}.
Don't try to make up an answer. If the question is not about
{DOMAIN_OR_QUESTION}, politely inform them that you are tuned
to only answer questions about {DOMAIN_AND_QUESTION} topics.
"""

answer_template = langchain_should_know + """Question: {question}
=========
{context}
=========
Answer in Markdown:
"""



QA_PROMPT = PromptTemplate(template=answer_template, input_variables=["question", "context"])


def get_chain(vc: VectorStore):
    llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    return ConversationalRetrievalChain.from_llm(
        llm,
        vc.as_retriever(),
        condense_question_prompt=CONDENSE_QUESTION_PROMPT,
        qa_prompt=QA_PROMPT,
    )


if __name__ == "__main__":
    with open("faiss_store.pkl", "rb") as f:
        vec_store = pickle.load(f)
        
    qa_chain = get_chain(vec_store)
    chat_history = [] # TODO: How to manage chat history
    print(f"Chat with the {HOST} bot:")
    while True:
        print("Your question:")
        question = input()
        result = qa_chain({"question": question, "chat_history": chat_history})
        chat_history.append((question, result["answer"]))
        print(f"AI: {result['answer']}")
