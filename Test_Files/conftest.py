import sys
import os

# Add the root directory of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Add the Code directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Code')))

import pytest
from unittest.mock import MagicMock
from Code.functions import write_query
from langchain_community.chat_models import ChatOllama

@pytest.fixture
def fake_llm_success():
    """LLM that returns well‐formed JSON containing a SQL query."""
    llm = MagicMock(spec=ChatOllama)  # MagicMock simulates LLM methods by default :contentReference[oaicite:5]{index=5}
    llm.invoke.return_value.content = '{"query": "SELECT COUNT(*) FROM customers;"}'
    return llm

@pytest.fixture
def fake_llm_bad_json():
    """LLM that returns non‐JSON text to trigger the error fallback."""
    llm = MagicMock(spec=ChatOllama)
    llm.invoke.return_value.content = "I’m sorry, I don’t understand."
    return llm
