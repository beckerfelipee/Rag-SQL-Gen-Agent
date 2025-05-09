import os
import atexit
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama
from local_ollama_management import start_ollama, is_ollama_running, terminate_ollama_processes
from dotenv import load_dotenv
import config as cfg
import functions as fn

# UI imports
import streamlit as st


# --- Constants --- #

# Load environment variables from .env file
load_dotenv()

# Connect to DB
db = SQLDatabase.from_uri(f"sqlite:///{cfg.DB_PATH}")

# Initialize the model
llm = ChatOllama(base_url=os.getenv("OLLAMA_SERVER"), model=cfg.LLM_MODEL, temperature=cfg.LLM_TEMPERATURE)

# --- Functions --- #



# --- Streamlit UI --- #

if __name__ == '__main__':
    if cfg.RUN_LOCALLY:
        atexit.register(terminate_ollama_processes)
        if not is_ollama_running():
            start_ollama()

    st.set_page_config(page_title="RAG SQL App", page_icon="🤖", layout="wide")
    st.title("RAG SQL App Interface")
    st.write("You can ask questions about the database and get answers in natural language.")

    st.header("🔍 Question Answering")
    prompt = st.text_area(label="Ask a question about the database:", placeholder="Type your question here...")
    

    # Criar colunas para os popovers
    col1, col2, col3, col4, col5 = st.columns([1, 4, 4, 4, 4])

    submit_button = col1.button(label="Submit")

    if submit_button:
        if prompt:
            info = st.empty()
            info.info("Processing your question...")


            state = fn.State()
            state["question"] = prompt

            # Retrieve relevant tables from the vector database
            
            info.status("Retrieving relevant tables...")
            tables = fn.query_collection(prompt=state["question"])
            context = tables["documents"]
            context_tables = "\n---\n".join(context)

            with col2.popover("📅 Retrieved Tables", use_container_width=100):
                if tables:  
                    for i in range(len(tables["ids"])):  # Itera sobre o comprimento de 'ids'
                        st.write(f"\n-----------\nID: {tables['ids'][i]}, Distance: {tables['distances'][i]}, \n\nDocument: \n{tables['documents'][i]}\n")
                else:
                    st.warning("No results found in the vector database.")
            
            # Generate SQL query using the retrieved tables

            info.status("Generating SQL query...")
            state["query"] = fn.write_query(question=state["question"], llm=llm, context_tables=context_tables)['query']
            with col3.popover("📝 Generated SQL Query", use_container_width=100):
                st.write(state["query"])
            
            # Execute the SQL query and retrieve results
            
            info.status("Executing SQL query...")
            if state["query"] == "Error generating query":
                state["result"] = "Empty"
            else:
                results, total_count = fn.create_view(query=state["query"], db=db)

                with col4.popover("📊 Query Results", use_container_width=100):
                    st.write(f"Total Results: {total_count}")
                    st.write("Results: ", results)

                if len(results) > cfg.MAX_RESULTS_LLM:
                    limited_results = results[:cfg.MAX_RESULTS_LLM]
                    state["result"] = f"Showing only the first {cfg.MAX_RESULTS_LLM}:\n{str(limited_results)}"
                else:
                    state["result"] = str(results)
                
            # Generate answer using the SQL result

            info.status("Generating answer...")
            state["answer"] = fn.generate_answer(state=state, llm=llm)

            st.header("💬 Answer")
            st.write_stream(state["answer"])

            info.subheader("") 

        
        else:
            st.warning("Please enter a question to ask.")
