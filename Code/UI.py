import os
import atexit
import pandas as pd
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

# print("Temperature:", llm.temperature)

# --- Functions --- #



# --- Streamlit UI --- #

if __name__ == '__main__':
    if cfg.RUN_LOCALLY:
        atexit.register(terminate_ollama_processes)
        if not is_ollama_running():
            start_ollama()

    st.set_page_config(page_title="RAG SQL App", page_icon="🤖", layout="wide")
    st.title("🤖 RAG SQL App Interface")
    st.write("You can ask questions about the database and get answers in natural language.")

    #st.header("🔍 Question Answering")

    # Criar colunas para os popovers
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    info = st.empty()

    with st.container(height=650, border=False):
        messages = st.container(height=550)
        if prompt := st.chat_input("Ask a question about the database", max_chars=300):
            messages.chat_message("user").write(prompt)
            # st.toast("Thinking..")
            
            info.info("Processing your question...")

            state = fn.State()
            state["question"] = prompt
            state["query"] = ""
            state["result"] = ""
            state["total_count"] = 0

            # Retrieve relevant tables from the vector database
            
            info.status("Retrieving relevant tables...")
            tables = fn.query_collection(prompt=state["question"])
            context = tables["documents"]
            state["tables_info"] = "\n---\n".join(context)
            
            if tables['ids'] != []:
                with col1.popover("📅 Retrieved Tables", use_container_width=100):
                    for i in range(len(tables["ids"])):  # Itera sobre o comprimento de 'ids'
                        st.write(f"\n-----------\nID: {tables['ids'][i]}, Distance: {tables['distances'][i]}, \n\nDocument: \n{tables['documents'][i]}\n")
            
                # Generate SQL query using the retrieved tables

                info.status("Generating SQL query...")
                state["query"] = fn.write_query(question=state["question"], llm=llm, context_tables=state["tables_info"])['query']
                if state["query"] != "Error generating query":
                    with col2.popover("📝 Generated SQL Query", use_container_width=100):
                        st.write(state["query"])
                
                # Execute the SQL query and retrieve results
                
                info.status("Executing SQL query...")
                if state["query"] == "Error generating query":
                    state["result"] = "Empty"
                else:
                    results, total_count = fn.create_view(query=state["query"], db=db)

                    if type(results) == list:
                        with col3.popover("📊 Query Results", use_container_width=100):
                            # Create a download button for the results
                            df = pd.DataFrame(results)
                            csv = df.to_csv().encode("utf-8")
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                on_click='ignore',
                                file_name=f"{state['query']}.csv"
                            )
                            # Display the results in a table
                            st.write(f"Total Results: {total_count}")
                            st.write("Results: ", results)

                        state["total_count"] = total_count
                        state["result"] = fn.reduce_rows(results=results, max_results=cfg.MAX_RESULTS_LLM)
                    else:
                        state["result"] = results # Error message from DB

            info.status("Generating answer...")
            state["answer"] = fn.generate_answer(state=state, llm=llm)
            output = state["answer"]

            messages.chat_message("AI").write_stream(state["answer"])
            info.empty()

