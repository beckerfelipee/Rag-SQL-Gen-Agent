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

# Options: "llama3.2:3b", "gemma3:27b", "llama3.3:70b"
LLM_MODEL = "llama3.2:3b"
LLM_TEMPERATURE = 0.1  # Temperature for the LLM response
LLM_TOP_P = 0.7  # Top-p sampling for the LLM response

# System message to generate SQL queries

DB_DIALECT_BASE = "sqlite"  # Base dialect for the database
MAX_RESULTS_QUERY = 3000  # Maximum number of results to return in the SQL query
MAX_RESULTS_LLM = 30  # Maximum number of results to return in the LLM response

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

ANSWER_GEN_SYSTEM_MESSAGE = """
Given the following user question and available information, provide a helpful answer. 
If SQL query and results are available, use them to answer the question. 
If not, use the provided table information to attempt to answer.

Question: {question}
Tables Info: {tables_info}
SQL Query: {query}
SQL Result: {result}

Important instructions:
- Your response must include all relevant information
- If both query and result are empty, attempt to answer using the tables info
- If no sufficient information is available, inform the user that you cannot answer the question with the available data
- Do not make assumptions beyond what is explicitly shown in the data
- Format data in an easily readable way appropriate to the question (tables, lists, etc.)
- Use natural language to explain the findings from the data
- Present your answer in a simple, easy-to-understand, and objective manner
- Do NOT suggest alternative queries or hypothetical solutions
"""


