import atexit

from vectorize_database import get_vector_collection, EMBEDDING_MODEL
from ollama_management import start_ollama, is_ollama_running, terminate_ollama_processes

EMBEDDING_TOP_K = 3

# --- Functions --- #

def query_collection(prompt: str, top_k: int = EMBEDDING_TOP_K):
    """Query the vector database based on a user prompt."""
    collection = get_vector_collection()
    print("Querying the collection...")
    results = collection.query(query_texts=[prompt], n_results=top_k) if collection.count() > 0 else None

    if results:
        return {
            "ids": results.get("ids")[0],
            "documents": results.get("documents")[0],
            "distances": results.get("distances")[0]
        }
    else:
        return None

# --- Script --- #

if __name__ == "__main__":
    atexit.register(terminate_ollama_processes)
    if not is_ollama_running():
        start_ollama()
    
    result = query_collection("How many actors are there in the database?")
    if result:
        print("Query Results:")
        for i in range(len(result["ids"])):
            print(f"\nID: {result['ids'][i]}, Distance: {result['distances'][i]}, \nDocument: {result['documents'][i]}\n")
    else:
        print("No results found in the vector collection.")


