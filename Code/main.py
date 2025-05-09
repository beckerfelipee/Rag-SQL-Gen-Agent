import os
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv
import config as cfg
import functions as fn


if __name__ == '__main__':

    # Load environment variables from .env file
    load_dotenv()

    # Connect to DB
    db = SQLDatabase.from_uri(f"sqlite:///{cfg.DB_PATH}")

    # Initialize the model
    llm = ChatOllama(base_url=os.getenv("OLLAMA_SERVER"), model=cfg.LLM_MODEL, temperature=cfg.LLM_TEMPERATURE)
    
    # Script to run the application
    state = fn.State()
    state["question"] = "How many customers are there in the database?"
    print("Question: ", state["question"])

    tables = fn.query_collection(prompt=state["question"])
    context = tables["documents"]
    context_tables = "\n---\n".join(context)

    state["query"] = fn.write_query(question=state["question"], llm=llm, context_tables=context_tables)['query']
    print("Query: ", state["query"])

    if state["query"] != "Error generating query":
        results, total_count = fn.create_view(query=state["query"], db=db)

        if len(results) > cfg.MAX_RESULTS_LLM:
            limited_results = results[:cfg.MAX_RESULTS_LLM]
            state["result"] = f"Showing only the first {cfg.MAX_RESULTS_LLM}:\n{str(limited_results)}"
        else:
            state["result"] = str(results)

    else:
        state["result"] = "Empty"

    print("Total Results: ", total_count)
    print("Result: ", state["result"])

    state["answer"] = fn.generate_answer(state=state, llm=llm)["answer"]
    print("Answer: ", state["answer"])
