# --- OLLAMA Server Configuration --- #

RUN_LOCALLY = True # Set to True if running the OLLAMA server locally

# --- Vector Database and Embedding Configuration --- #

# DB path for the SQLite database
DB_PATH = "DB//sakila.db"

# Path to the vector database (ChromaDB)
VECTOR_DB_PATH = "Vector_DB/vectorized_db"

# Extract database tables and their information
REMOVE_EXAMPLES = True  # Set to True to remove examples from the table information

# Embedding model to use for vectorization
EMBEDDING_MODEL = "nomic-embed-text:latest"

# Number of top results (tables) to retrieve from the vector database
EMBEDDING_TOP_K = 10

# Threshold for filtering results based on best distance
DISTANCE_THRESHOLD = 0.3 # percentage

# Cutoff for filtering results based on distance
DISTANCE_CUTOFF = 0.55

# Reranking model to use for vectorization
# RERANK_MODEL_PATH = "./ms-marco-MiniLM-L6-v2"

# Rerank top K results
# RERANK_TOP_K = 8

# Rerank threshold
# RERANK_THRESHOLD = 0.3 # percentage

# Rerank cutoff
# RERANK_CUTOFF = 1 # score

# --- LLM model to use for natural language responses --- #

# LLM model to use for generating SQL queries and answers
SQL_LLM_MODEL = "gemma3:27b"  # Model for SQL query generation
SQL_LLM_TEMPERATURE = 0.2  # Temperature for the SQL query generation
SQL_LLM_TOP_P = 0.9  # Top-p sampling for the SQL query generation

# Options: "llama3.2:3b", "gemma3:27b", "llama3.3:70b"
ANSWER_LLM_MODEL = "llama3.2:3b"
ANSWER_LLM_TEMPERATURE = 0.1  # Temperature for the LLM response
ANSWER_LLM_TOP_P = 0.9  # Top-p sampling for the LLM response

# System message to generate SQL queries

DB_DIALECT_BASE = "sqlite"  # Base dialect for the database
MAX_RESULTS_QUERY = 3000  # Maximum number of results to return in the SQL query
MAX_RESULTS_LLM = 20  # Maximum number of results to return in the LLM response

SQL_GEN_SYSTEM_MESSAGE = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Only query for the few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{tables_info}

# 1. Carefully read the user's question and identify what information is being requested.
# 2. Identify which tables and columns (from the provided schema) contain this information.
# 3. Double-check to avoid using any column or table that does not exist in the schema.
# 4. Finally, return the query in the specified JSON format.

Return your response as a JSON object with the following format:
{{
  "query": "your SQL query here"
}}
"""

ANSWER_GEN_SYSTEM_MESSAGE = """
You are a Capgemini AI tool specialized in databases. Respond strictly based on the provided context.

Given the following user question and available information, provide a helpful answer only if it is related to databases.

Context:
- Question: {question}

- Tables Info: {tables_info}

- SQL Query: {sql_query}

- Result to ANSWER: {result_data}

- (metadata) Number of rows (full result set): {result_row_count}

Important instructions:
- Only respond to questions that are clearly related to databases or the provided data context.
- If SQL query and result to answer are available, display them to answer the question.
- If both SQL query and result are empty, attempt to answer using the tables Info.
- Make it clear that the user has access to the full result set by clicking on "Query Results".
- Format data clearly using Markdown (tables, lists, etc.) when appropriate.
- Explain findings in a simple, objective, and easy-to-understand way.
- Do NOT suggest alternative queries or hypothetical solutions.
- Always respond in the same language as the question ({question}).
- Never answer questions that are unrelated to databases or the provided context.
"""
# - If there is not enough information to answer, clearly state that.

