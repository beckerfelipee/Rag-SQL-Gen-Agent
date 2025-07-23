import atexit
from Code import functions as fn

# Ollama server management
from Code.local_ollama_management import start_ollama, is_ollama_running, terminate_ollama_processes
from Code.config import RUN_LOCALLY, DB_PATH
from langchain_community.utilities import SQLDatabase 

# --- Script --- #

def create_vector_collection():
    """
    Create a vector collection from the database.
    """
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    docs = fn.db_extract(db)
    if fn.add_to_vector_collection(docs):
        print("✅ Vector collection successfully created!")
    else:
        print("❌ Vector collection creation failed.")

def create_vector_collection_azure():
    """
    Create a vector collection using Azure embeddings.
    """
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    docs = fn.db_extract(db)
    if add_to_vector_collection_azure(docs):
        print("✅ Vector collection successfully created with Azure embeddings!")
    else:
        print("❌ Vector collection creation with Azure embeddings failed.")



if __name__ == "__main__":
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    if RUN_LOCALLY:
        atexit.register(terminate_ollama_processes)
        if not is_ollama_running():
            start_ollama()

    docs = fn.db_extract(db)
    if fn.add_to_vector_collection(docs):
        print("✅ Document successfully added!")
    else:
        print("❌ Document processing failed.")

#TODO: create function to create/atualized the vector collection with the AZURE embeddings model

