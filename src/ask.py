import argparse
import pickle
from pprint import pprint
from typing import OrderedDict

from dotenv import dotenv_values
from langchain import OpenAI
from langchain.chains import VectorDBQAWithSourcesChain

cfg:OrderedDict = dotenv_values(".env")
openai_api_key = cfg.get("OPENAI_API_KEY")


def get_parser():
    parser = argparse.ArgumentParser("Hello I'm jarvis 🤖, What can I help you?")
    parser.add_argument('-q', '--question', type=str, default="who is leoo.j?", help='Question')
    return parser

def get_question(parser) -> str:
    args = parser.parse_args()
    return args.question


def read_store():
    with open("faiss_store.pkl", "rb") as f:
        return pickle.load(f)

def run(parser, chain):
    q = get_question(parser)
    result = chain({"question": q})
    pprint(f"Answer: {result['answer']}")
    pprint(f"Sources: {result['sources']}")
    

if __name__ == '__main__':
    store = read_store()
    chain = VectorDBQAWithSourcesChain.from_llm(
        llm=OpenAI(
            temperature=0, 
            verbose=True,
            openai_api_key=openai_api_key), 
        vectorstore=store, 
        verbose=True)
    parser = get_parser()
    run(parser, chain)