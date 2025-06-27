import os
import atexit
from local_ollama_management import start_ollama, is_ollama_running, terminate_ollama_processes
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv
import config as cfg
import functions as fn


if __name__ == '__main__':
    if cfg.RUN_LOCALLY:
        atexit.register(terminate_ollama_processes)
        if not is_ollama_running():
            start_ollama()

    # Load environment variables from .env file
    load_dotenv()

    # Connect to DB
    db = SQLDatabase.from_uri(f"sqlite:///{cfg.DB_PATH}")

    # Initialize the model
    base_url = os.getenv("OLLAMA_LOCAL_SERVER") if cfg.RUN_LOCALLY else os.getenv("OLLAMA_SERVER")
    llm = ChatOllama(base_url=base_url, model=cfg.SQL_LLM_MODEL, temperature=cfg.SQL_LLM_TEMPERATURE, top_p=cfg.SQL_LLM_TOP_P)
    
    # Script to run the application
    state = fn.State()
    state["question"] = "How many actors are in the database?"
    print("Question: ", state["question"])
    state["query"] = ""
    state["result"] = ""

    # Get the context tables
    tables = fn.query_collection(prompt=state["question"])

    if not tables:
        # Extract table info from your database
        all_splits = fn.db_extract(db)
        # Add to vector DB
        fn.add_to_vector_collection(all_splits)
        tables = fn.query_collection(prompt=state["question"])



    context = tables["documents"]

    state["tables_info"] = "\n---\n".join(context)

    # print("Context Tables: ", state["tables_info"])

    state["query"] = fn.write_query(question=state["question"], llm=llm, context_tables=state["tables_info"])['query']
    print("Query: ", state["query"])

    total_count = 0

    if state["query"] != "Error generating query":
        results, total_count = fn.create_view(query=state["query"], db=db)
        # print("Results: ", results) # All results of the query
        state["result"] = fn.reduce_rows(results=results, max_results=cfg.MAX_RESULTS_LLM)
    else:
        state["result"] = "Empty"

    state["total_count"] = total_count
    print("Total Results: ", state["total_count"])
    print("Result: ", state["result"])

    state["answer"] = fn.generate_answer(state=state, llm=llm)

    # Stream the answer
    for chunk in state["answer"]:
        print(chunk, end="", flush=True)
