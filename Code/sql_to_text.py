from question_to_sql import write_query
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import SQLDatabase
import sqlite3
import pandas as pd

db_path = "DB//sakila.db"
llm = ChatOllama(model="llama3.2:3b")


def create_temp_table(query):
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    temp_table =  db.run(query)
    return temp_table


 


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
    question = "How many actors are there in the database?"
    result = write_query({"question": question})
    print(result)
    response = create_temp_table(result['query'])
    print(response)