import pytest
from unittest.mock import MagicMock
from Code.functions import write_query, create_view

class MockDB:
    def run(self, query):
        return [{"id": 1, "name": "Mock Entry"}]

def test_integration_query_execution(monkeypatch):
    # Mock inputs
    question = "What are the entries in the mock table?"
    context_tables = "mock_table_info"
    db_dialect = "sqlite"
    max_results = 10

    # Mock LLM
    class MockLLM:
        def invoke(self, prompt):
            class MockResponse:
                def __init__(self, content):
                    self.content = '{"query": "SELECT * FROM mock_table;"}'
            return MockResponse('{"query": "SELECT * FROM mock_table;"}')

    llm = MockLLM()

    # Mock DB
    db = MockDB()

    # Call write_query
    query_result = write_query(question, llm, context_tables, max_results, db_dialect)
    assert "query" in query_result
    assert query_result["query"] == "SELECT * FROM mock_table;"

    # Call create_view
    result = create_view(query_result["query"], db)
    assert len(result) > 0
    assert result[0]["name"] == "Mock Entry"

    print("Integration test passed: Query execution and DB interaction.")
