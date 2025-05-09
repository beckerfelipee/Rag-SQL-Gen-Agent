from dotenv import load_dotenv
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.utilities import SQLDatabase
from typing import TypedDict
import json

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

load_dotenv()

# --- Constants --- #

llm_model = "llama3.2:3b"  # Model name for Ollama
Ollama_server_url = os.getenv("OLLAMA_SERVER")  # URL for Ollama server

# Connect to DB
db = SQLDatabase.from_uri("sqlite:///DB//sakila.db")

# Initialize the model
llm = ChatOllama(base_url=Ollama_server_url, model=llm_model)

# Modify the system message to include instructions for JSON output
system_message = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Only query for the few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{table_info}

Return your response as a JSON object with the following format:
{{
  "query": "your SQL query here"
}}
"""

user_prompt = "Question: {input}"

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
)

# Simple JSON output parser
output_parser = JsonOutputParser()

def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "table_info": db.get_table_info().split("\n\n\n")[0],
            "input": state["question"],
        }
    )

    print(prompt)
    
    # Get the response from the LLM
    response = llm.invoke(prompt)
    
    # Parse the content to get the JSON
    try:
        # Extract the JSON part from the response
        content = response.content
        # Find JSON in the response (in case there's additional text)
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        json_str = content[json_start:json_end]
        result = json.loads(json_str)
        return {"query": result["query"]}
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response.content}")
        return {"query": "Error generating query"}

def test_model():    
    response = llm.invoke("Olá, como você está?")   
    print(response.content)

if __name__ == '__main__':
    result = write_query({"question": "How many actors are there in the database?"})
    print(result)