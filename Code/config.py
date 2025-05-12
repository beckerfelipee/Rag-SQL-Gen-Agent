# --- OLLAMA Server Configuration --- #

RUN_LOCALLY = False  # Set to True if running the OLLAMA server locally

# Extract database tables and their information

REMOVE_EXAMPLES = True  # Set to True to remove examples from the table information

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
DISTANCE_CUTOFF = 0.52

# Embedding model to use for vectorization
EMBEDDING_MODEL = "nomic-embed-text:latest"

# --- LLM model to use for natural language responses --- #

# LLM model to use for generating SQL queries and answers

# Options: "llama3.2:3b", "gemma3:27b", "llama3.3:70b"
LLM_MODEL = "llama3.2:3b"
LLM_TEMPERATURE = 0.05  # Temperature for the LLM response
LLM_TOP_P = 0.8  # Top-p sampling for the LLM response

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

# 1. Carefully read the user's question and identify what information is being requested.
# 2. Identify which tables and columns (from the provided schema) contain this information.
# 3. Double-check to avoid using any column or table that does not exist in the schema ({table_info}).
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
- SQL Query: {query}
- SQL Total Results: {total_count}
- SQL Result: {result}

Important instructions:
- Only respond to questions that are clearly related to databases or the provided data context.
- If SQL query and results are available, use them to answer the question.
- If both query and result are empty, attempt to answer using the table information.
- Only If the SQL result text explicitly contains the phrase 'only {max_result_llm} results shown', mention that your analysis is limited to this subset of data. Otherwise, do not mention any limitation. 
- Make it clear that the user has access to the full result set by clicking on "Query Results".
- If there is not enough information to answer, clearly state that.
- Format data clearly using Markdown (tables, lists, etc.) when appropriate.
- Explain findings in a simple, objective, and easy-to-understand way.
- Do NOT suggest alternative queries or hypothetical solutions.
- Always respond in the same language as the question ({question}).
- Never answer questions that are unrelated to databases or the provided context.
"""


