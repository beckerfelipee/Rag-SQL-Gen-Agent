from config import db_path

from question_to_sql import write_query
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import SQLDatabase
from typing import TypedDict
#from main import State

'''Uses and SQL query to retrieve a table from the DB and calls an llm to generate a text answer to the user input based on that table'''


llm = ChatOllama(model="llama3.2:3b")

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str


def create_view(query):
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    temp_table =  db.run(query)
    return temp_table

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}
 

 


"""
    conn = sqlite3.connect(db_path)
    temp_table = pd.read_sql(query, conn)
    conn2 = sqlite3.connect("DB\\Temporary_db\\temporary.db")
    temp_table.to_sql("temporary", conn2, index=False, if_exists="replace")

    agent = create_pandas_dataframe_agent(llm, temp_table, verbose=True)
    response = agent.run(question) """

system_message = """
Given an input question, create a response that uses the {table} to answer the question.



Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{table_info}

Return your response as a JSON object with the following format:
{{
  "query": "your SQL query here"
}} """


user_prompt = "Question: {input}"


# def write_answer():
"""Generate answer to user input question based on the data avaiable on the temporary table"""



if __name__== '__main__':
    state = State()
    state.question = "How many actors are there in the database?"
    print(state)
    state.query = write_query({"question": state.question})['query']
    print(state)
    response = create_view(state.query)
    print(response)