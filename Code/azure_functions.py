import ast
import json
import os
import sys
import openai

from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
from openai import AzureOpenAI

import config as cfg
import functions as fn

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from typing import TypedDict

import time

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("API_KEY_AZURE"),
    api_version=cfg.API_VERSION_AZURE,
    azure_endpoint=os.getenv("API_ENDPOINT_AZURE")
)


"""Requires an embedding model to be set in the environment variable MODEL_EMBEDDINGS_AZURE."""
def get_vector_collection_azure() -> chromadb.Collection:
    """Retrieve or create a ChromaDB vector collection using Azure OpenAI embeddings."""
    # Use AzureOpenAI client for embedding function
    embedding_function = OpenAIEmbeddingFunction(
        api_key=os.getenv("API_KEY_AZURE"),
        api_base=os.getenv("API_ENDPOINT_AZURE"),
        api_type="azure",
        api_version=os.getenv("API_VERSION_AZURE"),
        model_name=os.getenv("MODEL_EMBEDDINGS_AZURE"),
        deployment_id=os.getenv("MODEL_AZURE")
    )
    chroma_client = chromadb.PersistentClient(path=cfg.VECTOR_DB_PATH)
    return chroma_client.get_or_create_collection(
        name="rag-sql-app",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )

def write_query_azure(question: str, client: AzureOpenAI, context_tables: str, db_dialect: str = cfg.DB_DIALECT_BASE) -> dict:
    """Generate SQL query to fetch information using Azure OpenAI."""

    system_message = cfg.SQL_GEN_SYSTEM_MESSAGE
    user_prompt = f"Question: {question}\nDialect: {db_dialect}\nTables Info: {context_tables}"

    try:
        response = client.chat.completions.create(
            model=cfg.SQL_LLM_MODEL_AZURE,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ],
            temperature= cfg.SQL_LLM_TEMPERATURE_AZURE,
            max_tokens=cfg.SQL_LLM_MAX_TOKENS_AZURE,
        )
        content = response.choices[0].message.content

        # Extract the JSON part from the response
        json_start = content.find('{')
        json_end = content.find('}', json_start) + 1
        json_str = content[json_start:json_end]
        result = json.loads(json_str)
        # print(f"Raw response: {content}")
        print(result)
        return {"query": result["query"]}
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {content if 'content' in locals() else 'No content'}")
        return {"query": "Error generating query"}
    
# Answer generation

class State(TypedDict):
    question: str
    query: str
    result: str
    total_count: int
    answer: str
    tables_info: str

def generate_answer_azure(state: State, client: AzureOpenAI) -> str:
    """Answer question using retrieved information as context with Azure OpenAI."""
    prompt = cfg.ANSWER_GEN_SYSTEM_MESSAGE.format(
        question=state["question"],
        tables_info=state["tables_info"],
        sql_query=state["query"],
        result_row_count=state["total_count"],
        result_data=state["result"]
    )


    response = client.chat.completions.create(
        model=cfg.ANSWER_LLM_MODEL_AZURE,
        messages=[
            {"role": "system", "content": cfg.ANSWER_GEN_SYSTEM_MESSAGE},
            {"role": "user", "content": prompt}
        ],
        temperature=cfg.ANSWER_LLM_TEMPERATURE_AZURE,
        max_tokens=cfg.ANSWER_LLM_MAX_TOKENS_AZURE,
    )
    return response.choices[0].message.content

def question_and_answer_azure(question, database ) -> State:
    """Process a question and return the answer using Azure OpenAI."""

    state = fn.State()
    state["question"] = question
    # print("Question: ", state["question"])
    state["query"] = ""
    state["result"] = ""

    tables = fn.query_collection(prompt=state["question"])

    context = tables["documents"]

    state["tables"] = tables
    state["query"] = write_query_azure(
        question=state["question"],
        client=client,
        context_tables=tables["documents"]
    )["query"]
    state["tables_info"] = "\n---\n".join(context)

    if state["query"] != "Error generating query":
        results, total_count = fn.create_view(query=state["query"], db=database)
        # print("Results: ", results) # All results of the query
        print(state["result"])
        state["result"] = results
    else:
        state["result"] = "Empty"

    # print(state)

    state["total_count"] = total_count
    state["answer"] = generate_answer_azure(state=state, client=client)

    # Stream the answer
    for chunk in state["answer"]:
        print(chunk, end="", flush=True)

    print("Total Results: ", state["total_count"])
    print("Result: ", state["result"])

    return state


if __name__ == "__main__":
    # Example usage

    db = SQLDatabase.from_uri(f"sqlite:///{cfg.DB_PATH}")
    question_and_answer_azure(question = 'How many actors in db', database = db)
