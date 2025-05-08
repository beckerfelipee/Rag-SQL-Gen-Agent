import atexit

from langchain_community.utilities import SQLDatabase

# get or create vector collection and query it
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

# Ollama server management
from ollama_management import start_ollama, is_ollama_running, terminate_ollama_processes

# --- Constants --- #

DB_PATH = "DB//sakila.db"
EMBEDDING_MODEL = "nomic-embed-text:latest"
VECTOR_DB_PATH = "Vector_DB/vectorized_db"

db = SQLDatabase.from_uri(F"sqlite:///{DB_PATH}")

# db_dialect = db.dialect
table_names = db.get_usable_table_names()
tables_info = db.get_table_info_no_throw()


# --- Functions --- #

# Vector collection management

def get_vector_collection() -> chromadb.Collection:
    """Retrieve or create a ChromaDB vector collection."""
    embedding_function = OllamaEmbeddingFunction(url="http://localhost:11434/api/embeddings", model_name=EMBEDDING_MODEL)
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH) # chroma uses sqlite3 to store data
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


# --- Script --- #

if __name__ == "__main__":
    atexit.register(terminate_ollama_processes)
    if not is_ollama_running():
        start_ollama()
        
    docs = tables_info.split("\n\n\n")
    if add_to_vector_collection(docs):
        print("✅ Document successfully added!")
    else:
        print("❌ Document processing failed.")
