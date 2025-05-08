from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models import ChatOllama
from typing import TypedDict
from langchain_community.utilities import SQLDatabase
import json


class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str


#Connect to DB
db = SQLDatabase.from_uri("sqlite:///DB//sakila.db")

# Initialize the model (e.g., llama3, mistral, etc.)
llm = ChatOllama(model="llama3.2:3b")

'''system_message = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Unless the user specifies in his question a
specific number of examples they wish to obtain, always limit your query to
at most {top_k} results. You can order the results by a relevant column to
return the most interesting examples in the database. In any case, never display
more than {max_k} results. If such situation occurs, you should notice the user.

Never query for all the columns from a specific table, only ask for a the
few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{table_info}
"""
'''

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

'''
class QueryOutput(BaseModel):
    """Generated SQL query."""
    query: Annotated[str,..., "Syntactically valid SQL query."]'''


def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "table_info": db.get_table_info().split("\n\n\n")[0],
            "input": state["question"],
        }
    )
    
    #structured_llm = llm.with_structured_output({'query': str})
    #result = structured_llm.invoke(prompt)
    #return {"query": result["query"]}

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
        #print(f"Error parsing JSON: {e}")
        #print(f"Raw response: {response.content}")
        return {"query": "Error generating query"}

def test_model():    
    response = llm.invoke("Olá, como você está?")   
    print(response.content)
 

if __name__ == '__main__':
    #print(dir(llm))
    #test_model()
    result = write_query({"question": "How many actors are there in the database?"})
    print(result)





