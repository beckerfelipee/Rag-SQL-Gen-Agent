# RAG SQL Agent

RAG SQL Agent is a Retrieval-Augmented Generation (RAG) application designed to interact with SQL databases using natural language queries. It leverages advanced language models to generate SQL queries, retrieve relevant data, and provide human-readable answers.

## Features

- **Natural Language to SQL**: Converts user questions into SQL queries.
- **Database Interaction**: Supports querying SQLite databases.
- **Vector Database Integration**: Uses ChromaDB for vectorized document storage and retrieval.
- **Streamlit UI**: Provides an intuitive interface for user interaction.
- **Local and Remote LLM Support**: Supports both local and remote Ollama servers for language model inference.

### Key Directories and Files

- **Code/**: Contains the core application logic, including database interaction, LLM integration, and utility functions.
- **DB/**: Stores the SQLite database (`sakila.db`).
- **Test_Files/**: Includes unit and integration tests for the application.
- **Vector_DB/**: Stores vectorized representations of database tables for retrieval.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/rag-sql-agent.git
   cd rag-sql-agent
   ```

2. Install dependencies:
   ```python
   pip install -r requirements.txt
   ```
   
3. Set up the environment variables:
  * Create a .env file in the root directory.
  * Add the required variables (OLLAMA_SERVER, OLLAMA_LOCAL_SERVER).

4. Ensure the SQLite database is in the DB/ directory.

## Usage

Run the Streamlit UI:
   ```python
   streamlit run Code/UI.py
   ```

Ask questions about the database and get answers in natural language.

### License
This project is licensed under the MIT License.

### Colaborators
- [André Roque](https://github.com/Roque97)
- [Felipe Becker](https://github.com/beckerfelipee)
- [Guilherme Marques](https://github.com/guilhermusm)
