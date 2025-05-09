# --- OLLAMA Server Configuration --- #

RUN_LOCALLY = False  # Set to True if running the OLLAMA server locally

# --- Vector Database and Embedding Configuration --- #

# DB path for the SQLite database
DB_PATH = "DB//sakila.db"

# Path to the vector database (ChromaDB)
VECTOR_DB_PATH = "Vector_DB/vectorized_db"

# Number of top results (tables) to retrieve from the vector database
EMBEDDING_TOP_K = 10

# Threshold for filtering results based on best distance
DISTANCE_THRESHOLD = 1.3 

# Cutoff for filtering results based on distance
DISTANCE_CUTOFF = 0.5 

# Embedding model to use for vectorization
EMBEDDING_MODEL = "nomic-embed-text:latest"

# --- LLM model to use for natural language responses --- #

# LLM model to use for generating SQL queries and answers
LLM_MODEL = "llama3.2:3b"

# System message to generate SQL queries

SQL_GEN_SYSTEM_MESSAGE = """
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


