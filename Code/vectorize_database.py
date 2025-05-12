import atexit
import functions as fn

# Ollama server management
from local_ollama_management import start_ollama, is_ollama_running, terminate_ollama_processes
from config import RUN_LOCALLY, DB_PATH
from langchain_community.utilities import SQLDatabase 

# --- Script --- #

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
