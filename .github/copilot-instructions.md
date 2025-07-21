# Copilot Instructions for RAG SQL Agent

## Project Architecture & Key Components
- **Code/**: Main application logic. Includes:
  - `functions.py`: Ollama LLM, vector DB, SQL generation, and answer streaming.
  - `azure_functions.py`: Azure OpenAI integration, vector DB (ChromaDB) for Azure embeddings, SQL/answer generation.
  - `UI.py`: Streamlit UI, provider switch (Ollama/Azure), unified result display.
  - `vectorize_database.py`: Populates ChromaDB collections with table schemas for retrieval.
  - `config.py`: Centralized config for models, endpoints, DB paths, and thresholds.
- **DB/**: SQLite database (`sakila.db`).
- **Vector_DB/**: ChromaDB persistent storage for vectorized table schemas. Multiple collections supported (one per embedding model).
- **Test_Files/**: Pytest-based unit/integration tests. Use mocks for LLM/DB calls. Focus on result structure, not LLM output.

## Developer Workflows
- **Run UI**: `streamlit run Code/UI.py` or use `run_streamlit.bat` for Windows.
- **Vectorize DB**: Run `Code/vectorize_database.py` to populate ChromaDB collections. Ensure correct embedding model/deployment is set in config.
- **Switch LLM Provider**: UI allows switching between Ollama (local/remote) and Azure OpenAI. Code paths are unified for answer/result display.
- **Testing**: Use `pytest Test_Files/` for all tests. Tests mock LLM/DB for deterministic results.

## Patterns & Conventions
- **ChromaDB Collections**: Named per embedding model (e.g., `rag-sql-app-text-embedding-3-small`). Always check collection existence and populate if empty.
- **Config-Driven**: All model/deployment/DB settings in `config.py`. Never hardcode in logic files.
- **LLM Output Robustness**: Tests and UI compare only query results, not LLM answer strings. Use mocks for all external calls.
- **Error Handling**: Defensive checks for empty vector results, missing tables, and failed queries. Fallback to all schemas if retrieval fails.
- **Environment**: Use `.env` for secrets/URLs. Load with `dotenv`.

## Integration Points
- **Ollama**: Local/remote server for LLM inference. Embedding model set in config.
- **Azure OpenAI**: Requires deployment name for embeddings. All API keys/URLs in `.env` and `config.py`.
- **ChromaDB**: Used for both Ollama and Azure embeddings. Multiple collections supported.
- **Streamlit**: Unified UI for both providers. Results and answers displayed in popovers.

## Examples
- To add new embedding model: Update `config.py`, run `vectorize_database.py` to populate new ChromaDB collection.
- To add new test: Place in `Test_Files/`, use pytest and mock LLM/DB calls.
- To debug vector DB: Check collection count, ensure docs are added, and verify correct model/deployment in config.

---
For unclear or incomplete sections, please provide feedback or examples from your workflow to improve these instructions.
