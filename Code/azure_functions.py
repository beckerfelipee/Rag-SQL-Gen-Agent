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

DEBUG = True

client = AzureOpenAI(
    api_key=os.getenv("API_KEY_AZURE"),
    api_version=cfg.API_VERSION_AZURE,
    azure_endpoint=os.getenv("API_ENDPOINT_AZURE")
)


"""Requires an embedding model to be set in the environment variable MODEL_EMBEDDINGS_AZURE."""
def get_vector_collection_azure() -> chromadb.Collection:
    """Retrieve or create a ChromaDB vector collection using Azure OpenAI embeddings, one per embedding model."""
    # Use AzureOpenAI client for embedding function
    #!
    embedding_function = OpenAIEmbeddingFunction(
        api_key=os.getenv("API_KEY_AZURE"),
        api_base=os.getenv("API_ENDPOINT_AZURE"),
        api_type="azure",
        api_version=cfg.API_VERSION_AZURE,
        model_name=cfg.MODEL_EMBEDDINGS_AZURE,
        deployment_id=cfg.DEPLOYMENT_ID_EMBEDDINGS_AZURE
    )
    chroma_client = chromadb.PersistentClient(path=cfg.VECTOR_DB_PATH)
    collection_name = f"rag-sql-app-{cfg.MODEL_EMBEDDINGS_AZURE}"
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )
    if collection.count() == 0:
        # Load your documents to add (replace with your actual docs loading logic)
        db = SQLDatabase.from_uri(f"sqlite:///{cfg.DB_PATH}")
        docs = fn.db_extract(db)
        print(f"Adding {len(docs)} documents to the collection {collection_name}...")
        add_docs_to_azure_vector_collection(docs = docs, collection = collection)

    return collection


def query_collection_azure(prompt: str, top_k: int = cfg.EMBEDDING_TOP_K, model_name=None) -> dict:
    """Query the vector database based on a user prompt and embedding model."""
    collection = get_vector_collection_azure()

    if DEBUG:
        print("Collection count: ", collection.count())

    print(f"Querying the collection for model: {model_name or cfg.MODEL_EMBEDDINGS_AZURE}")
    results = collection.query(query_texts=[prompt], n_results=top_k) if collection.count() > 0 else None

    if DEBUG:
        print(f"Results for model {model_name or cfg.MODEL_EMBEDDINGS_AZURE}: {results}")

    if results:
        distances = results["distances"][0]
        # print(distances)

        best_distance = min(distances)
        threshold = best_distance * (1 + cfg.DISTANCE_THRESHOLD)
        
        # Criar uma máscara de índices que atendem ao critério
        filtered_indices = [i for i, distance in enumerate(distances) if distance <= threshold and distance <= cfg.DISTANCE_CUTOFF]
        
        # Aplicar a filtragem de uma vez só
        return {
            "ids": [results["ids"][0][i] for i in filtered_indices],
            "documents": [results["documents"][0][i] for i in filtered_indices],
            "distances": [results["distances"][0][i] for i in filtered_indices]
        }
    else:
        return None



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
        print(f"Raw response: {content}")
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
    if DEBUG:
        print("Generated answer:", response.choices[0].message.content)

    return response.choices[0].message.content

def question_and_answer_azure(question, database ) -> State:
    """Process a question and return the answer using Azure OpenAI."""

    state = fn.State()
    state["question"] = question
    print("Question: ", state["question"])
    state["query"] = ""
    state["result"] = ""

    tables = query_collection_azure(prompt=state["question"])

    if tables is None:
        print("No relevant tables found in the vector database for this question or database not found.")
        state["tables"] = {}
        state["query"] = ""
        state["tables_info"] = ""
        state["result"] = "Empty"
        state["total_count"] = 0
        state["answer"] = "No relevant tables found to answer the question."
        return state

    if DEBUG:
        print("Retrieved tables:", tables)

    context = tables["documents"]

    state["tables"] = tables
    state["query"] = write_query_azure(
        question=state["question"],
        client=client,
        context_tables=tables["documents"]
    )["query"]
    state["tables_info"] = "\n---\n".join(context)

    if DEBUG:
        print("Context Tables: ", state["tables_info"])
        print("Generated Query: ", state["query"])
        print("Query: ", state["query"])

    if state["query"] != "Error generating query":
        results, total_count = fn.create_view(query=state["query"], db=database)
        # print("Results: ", results) # All results of the query
        print(state["result"])
        state["result"] = results
    else:
        state["result"] = "Empty"

    print(state)

    state["total_count"] = total_count
    state["answer"] = generate_answer_azure(state=state, client=client)

    # Stream the answer
    for chunk in state["answer"]:
        print(chunk, end="", flush=True)

    print(state["answer"])
    print("Total Results: ", state["total_count"])
    print("Result: ", state["result"])

    return state


def add_docs_to_azure_vector_collection(docs, collection, ids=None):
    """Add documents to the ChromaDB collection using the Azure embeddings model."""
    if ids is None:
        ids = [str(i) for i in range(1, len(docs) + 1)]
    collection.add(documents=docs, ids=ids)
    if DEBUG:
        print(f"Added {len(docs)} docs to collection {collection.name}. New count: {collection.count()}")
    return True


if __name__ == "__main__":
    # Example usage

    db = SQLDatabase.from_uri(f"sqlite:///{cfg.DB_PATH}")
    question_and_answer_azure(question = 'How many actors in db', database = db)





    """
    print("API_KEY_AZURE:", os.getenv("API_KEY_AZURE"))
    print("API_VERSION_AZURE:", os.getenv("API_VERSION_AZURE"))
    print("API_ENDPOINT_AZURE:", os.getenv("API_ENDPOINT_AZURE"))
    print("MODEL_AZURE:", os.getenv("MODEL_AZURE"))"""

    """
    db = SQLDatabase.from_uri(f"sqlite:///{cfg.DB_PATH}")

    # Script to run the application
    state = fn.State()
    state["question"] = "How many actors are in the database?"
    print("Question: ", state["question"])
    state["query"] = ""
    state["result"] = ""

    # Get the context tables using local Ollama server
    tables = fn.query_collection(prompt=state["question"])

    context = tables["documents"]
    state["query"] = write_query_azure(
        question=state["question"],
        client=client,
        context_tables=tables["documents"]
    )["query"]

    state["tables_info"] = "\n---\n".join(context)

    print(state["query"])

    if state["query"] != "Error generating query":
        results, total_count = fn.create_view(query=state["query"], db=db)
        # print("Results: ", results) # All results of the query
        state["result"] = fn.reduce_rows(results=results, max_results=cfg.MAX_RESULTS_LLM)
    else:
        state["result"] = "Empty"

    print(state)

    state["total_count"] = total_count

    state["answer"] = generate_answer_azure(state=state, client=client)

    # Stream the answer
    for chunk in state["answer"]:
        print(chunk, end="", flush=True) """




    
    # You can now use this collection to add documents, query, etc.
    # For example, you can add a document:
    # collection.add(documents=["This is a test document."], ids=["1"])
    
    # To query the collection:
    # results = collection.query(query_texts=["What is the test document?"])
    # print(results)