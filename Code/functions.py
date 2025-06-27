# load environment variables from .env file
from dotenv import load_dotenv
import os

# get or create vector collection and query it
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

# generate SQL queries
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
import json

# Execute SQL queries
import ast # transform string to python literal

# Generate Answer
from typing import TypedDict

# Config
import config as cfg
# Extract environment variables from .env file
load_dotenv()

# --- Functions --- #

# Database Extraction

def db_extract(db) -> list[str]:
    """Extracts the table names and their information from the database."""
    tables_info = db.get_table_info_no_throw()
    docs = tables_info.split("\n\n\n")
    if cfg.REMOVE_EXAMPLES:
        if cfg.REMOVE_EXAMPLES:
            docs = [doc.split("\n\n")[0] for doc in docs]
    return docs

# Vector collection management

def get_vector_collection() -> chromadb.Collection:
    """Retrieve or create a ChromaDB vector collection."""
    url = os.getenv("OLLAMA_LOCAL_SERVER") if cfg.RUN_LOCALLY else os.getenv("OLLAMA_SERVER")
    # print(f"Connecting to OLLAMA server at {url}...")
    embedding_function = OllamaEmbeddingFunction(url=url, model_name=cfg.EMBEDDING_MODEL)
    chroma_client = chromadb.PersistentClient(path=cfg.VECTOR_DB_PATH) # chroma uses sqlite3 to store data
    return chroma_client.get_or_create_collection(name="rag-sql-app", embedding_function=embedding_function, metadata={"hnsw:space": "cosine"})
    # hnsw is a nearest neighbor search algorithm, cosine is a similarity measure.


def add_to_vector_collection(all_splits) -> bool:
    """Add document chunks to the vector database."""
    collection = get_vector_collection()
    print("Adding tables to the collection...")

    ids = []

    for idx, split in enumerate(all_splits):
        ids.append(f"{idx}") # Create unique IDs for each chunk
    
    # create or update data in the collection
    collection.upsert(documents=all_splits, ids=ids)
    print(f"Added {len(all_splits)} tables to the collection")
    return True


def query_collection(prompt: str, top_k: int = cfg.EMBEDDING_TOP_K) -> dict:
    """Query the vector database based on a user prompt."""
    collection = get_vector_collection()
    print("Querying the collection...")
    results = collection.query(query_texts=[prompt], n_results=top_k) if collection.count() > 0 else None

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
    
    
# LLM test

def test_model(llm: ChatOllama) -> None:    
    response = llm.invoke("Olá, como você está?")   
    print(response.content)

# Write SQL query

def write_query(question: str, llm: ChatOllama, context_tables: str, db_dialect: str = cfg.DB_DIALECT_BASE) -> dict:
    """Generate SQL query to fetch information."""

    user_prompt = "Question: {input}"

    query_prompt_template = ChatPromptTemplate(
    [("system", cfg.SQL_GEN_SYSTEM_MESSAGE), ("user", user_prompt)]
    )   

    prompt = query_prompt_template.invoke(
        {
            "dialect": db_dialect,
            "tables_info": context_tables,
            "input": question
        }
    )

    print(f"Prompt: {prompt}")

    # Get the response from the LLM
    response = llm.invoke(prompt)

     # Parse the content to get the JSON
    try:
        # Extract the JSON part from the response
        content = response.content
        # Find the first JSON in the response (in case there's more than one)
        json_start = content.find('{')
        json_end = content.find('}', json_start) + 1
        json_str = content[json_start:json_end]
        result = json.loads(json_str)
        print(f"Raw response: {response.content}")
        print(result)
        return {"query": result["query"]}
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response.content}")
        return {"query": "Error generating query"}
    

# Execute SQL query (Create view)
def create_view(query: str, db):
    '''Uses and SQL query to retrieve a table from the DB and calls an llm to generate a 
    text answer to the user input based on that table'''
    temp_table =  db.run_no_throw(query, include_columns=True)
    try:
        results = ast.literal_eval(temp_table)
    except Exception as e:
        results = temp_table
    total_count = len(results)
    # print(type(results))
    # print(results)
    return results, total_count


# Reduce the number of rows in the result
def reduce_rows(results: list, max_results: int = cfg.MAX_RESULTS_LLM) -> str:
    if len(results) > max_results:
        limited_results = results[:max_results]
        return f"Showing only the first {max_results}:\n{str(limited_results)}"
    else:
        return str(results)


# Answer generation

class State(TypedDict):
    question: str
    query: str
    result: str
    total_count: int
    answer: str
    tables_info: str

def generate_answer(state: State, llm: ChatOllama):
    """Answer question using retrieved information as context."""
    prompt = cfg.ANSWER_GEN_SYSTEM_MESSAGE.format(
        question=state["question"],
        tables_info=state["tables_info"],
        sql_query=state["query"],
        result_row_count=state["total_count"],
        result_data=state["result"]
    )
    
    response = llm.stream(prompt)

    for chunk in response:
        yield chunk.content

    # return {"answer": response.content}


if __name__ == "__main__":
    # Example usage
    load_dotenv()
    db = None  # Replace with actual database connection
    llm = ChatOllama(model=cfg.SQL_LLM_MODEL, temperature=cfg.SQL_LLM_TEMPERATURE, top_p=cfg.SQL_LLM_TOP_P)
    
    question = "What are the entries in the mock table?"
    context_tables = "mock_table_info"
    
    query_result = write_query(question, llm, context_tables)
    print(query_result)
    
    results, total_count = create_view(query_result["query"], db)
    print(results, total_count)
    
    state = State(question=question, query=query_result["query"], result=str(results), total_count=total_count, answer="", tables_info=context_tables)
    answer = generate_answer(state, llm)
    
    for chunk in answer:
        print(chunk)  # Stream the answer
    