import os
import atexit
import pandas as pd
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama
from Code.local_ollama_management import start_ollama, is_ollama_running, terminate_ollama_processes
from dotenv import load_dotenv
from Code import config as cfg
from Code import functions as fn
from Code import azure_functions as azf


# UI imports
import streamlit as st

# --- Constants --- #

# Load environment variables from .env file
load_dotenv()

# Connect to DB
db = SQLDatabase.from_uri(f"sqlite:///{cfg.DB_PATH}")

# Initialize the model
base_url = os.getenv("OLLAMA_LOCAL_SERVER") if cfg.RUN_LOCALLY else os.getenv("OLLAMA_SERVER")

sql_llm = ChatOllama(base_url=base_url, model=cfg.SQL_LLM_MODEL, temperature=cfg.SQL_LLM_TEMPERATURE, top_p=cfg.SQL_LLM_TOP_P)
answer_llm = ChatOllama(base_url=base_url, model=cfg.ANSWER_LLM_MODEL, temperature=cfg.ANSWER_LLM_TEMPERATURE, top_p=cfg.ANSWER_LLM_TOP_P)

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
    llm_provider = st.radio(
    "Choose LLM Provider:",
    ("Ollama (Local)", "Azure OpenAI"),
    index=0)
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

            if llm_provider == "Ollama (Local)":
                state = fn.State()
                state["question"] = prompt
                state["query"] = ""
                state["result"] = ""
                state["total_count"] = 0

                info.status("Retrieving relevant tables...")
                tables = fn.query_collection(prompt=state["question"])
                context = tables["documents"]
                state["tables_info"] = "\n---\n".join(context)

                if tables['ids'] != []:
                    with col1.popover("📅 Retrieved Tables", use_container_width=100):
                        for i in range(len(tables["ids"])):
                            st.write(f"\n-----------\nID: {tables['ids'][i]}, Distance: {tables['distances'][i]}, \n\nDocument: \n{tables['documents'][i]}\n")

                info.status("Generating SQL query...")
                state["query"] = fn.write_query(question=state["question"], llm=sql_llm, context_tables=state["tables_info"])['query']
                if state["query"] != "Error generating query":
                    with col2.popover("📝 Generated SQL Query", use_container_width=100):
                        st.write(state["query"])

                info.status("Executing SQL query...")
                if state["query"] == "Error generating query":
                    state["result"] = "Empty"
                else:
                    results, total_count = fn.create_view(query=state["query"], db=db)
                    if type(results) == list:
                        with col3.popover("📊 Query Results", use_container_width=100):
                            df = pd.DataFrame(results)
                            csv = df.to_csv().encode("utf-8")
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                on_click='ignore',
                                file_name=f"{state['query']}.csv"
                            )
                            st.write(f"Total Results: {total_count}")
                            st.write("Results: ", results)
                        state["total_count"] = total_count
                        state["result"] = fn.reduce_rows(results=results, max_results=cfg.MAX_RESULTS_LLM)
                    else:
                        state["result"] = results

                info.status("Generating answer...")
                state["answer"] = fn.generate_answer(state=state, llm=answer_llm)
                output = state["answer"]
                messages.chat_message("AI").write_stream(state["answer"])
                info.empty()
            elif llm_provider == "Azure OpenAI":
                state = azf.question_and_answer_azure(question=prompt, database=db)
                # Show the same popovers as Ollama, if the keys exist in state
                if 'tables' in state and state['tables'] and 'ids' in state['tables'] and state['tables']['ids']:
                    with col1.popover("📅 Retrieved Tables", use_container_width=100):
                        for i in range(len(state['tables']['ids'])):
                            st.write(f"\n-----------\nID: {state['tables']['ids'][i]}, Distance: {state['tables']['distances'][i]}, \n\nDocument: \n{state['tables']['documents'][i]}\n")
                if 'query' in state and state['query']:
                    with col2.popover("📝 Generated SQL Query", use_container_width=100):
                        st.write(state['query'])
                if 'result' in state and isinstance(state['result'], list):
                    with col3.popover("📊 Query Results", use_container_width=100):
                        df = pd.DataFrame(state['result'])
                        csv = df.to_csv().encode("utf-8")
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            on_click='ignore',
                            file_name=f"{state['query']}.csv"
                        )
                        st.write(f"Total Results: {state.get('total_count', 0)}")
                        st.write("Results: ", state['result'])
                # Always show the answer
                messages.chat_message("AI").write(state["answer"])
                info.empty()

