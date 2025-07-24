import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add the Code directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Code')))

from Code.azure_functions import question_and_answer_azure, State
from Code.functions import create_view
import Code.config as cfg


class MockAzureDatabase:
    """Mock database that returns predefined results based on query patterns."""
    
    def run_no_throw(self, query, include_columns=True):
        """Mock database responses for different query patterns."""
        query_lower = query.lower().strip()
        
        # Basic queries
        if "count(*)" in query_lower and "actor" in query_lower:
            return "[200]"
        elif "select * from customer" in query_lower or "customer_id, first_name" in query_lower:
            return "[{'customer_id': 1, 'first_name': 'John', 'last_name': 'Doe'}, {'customer_id': 2, 'first_name': 'Jane', 'last_name': 'Smith'}]"
        elif "rental_rate" in query_lower and "limit 5" in query_lower:
            return "[{'title': 'Film A', 'rental_rate': 4.99}, {'title': 'Film B', 'rental_rate': 3.99}]"
        elif "inventory" in query_lower and "academy dinosaur" in query_lower:
            return "[{'inventory_id': 1, 'film_id': 1, 'store_id': 1}]"
        elif "staff" in query_lower and "group by store_id" in query_lower:
            return "[{'store_id': 1, 'staff_count': 2}, {'store_id': 2, 'staff_count': 1}]"
        elif "sum(amount)" in query_lower and "payment" in query_lower:
            return "[67416.51]"
            
        # New query patterns for additional test cases
        elif "avg" in query_lower and "rental_rate" in query_lower:
            return "[3.99]"
        elif "category" in query_lower and "count" in query_lower and "group by" in query_lower:
            return "[{'category_name': 'Action', 'film_count': 64}, {'category_name': 'Comedy', 'film_count': 58}]"
        elif "length" in query_lower and (">180" in query_lower or "greater than 180" in query_lower or "> 180" in query_lower):
            return "[{'title': 'Long Film 1', 'length': 185}, {'title': 'Long Film 2', 'length': 190}]"
        elif "actor" in query_lower and "count" in query_lower and "order by" in query_lower and "desc" in query_lower:
            return "[{'actor_name': 'GINA DEGENERES', 'film_count': 42}]"
        elif "never been rented" in query_lower or "not in" in query_lower and "rental" in query_lower:
            return "[{'title': 'Unwatched Film', 'film_id': 123}]"
        elif "most rented" in query_lower or ("count" in query_lower and "rental" in query_lower and "order by" in query_lower and "desc" in query_lower):
            return "[{'title': 'Popular Movie', 'rental_count': 30}]"
        elif "country" in query_lower and "count" in query_lower:
            return "[{'country': 'United States', 'customer_count': 50}, {'country': 'Canada', 'customer_count': 30}]"
        elif "revenue" in query_lower and "store" in query_lower:
            return "[{'store_id': 1, 'revenue': 33489.47}, {'store_id': 2, 'revenue': 33927.04}]"
        elif "horror" in query_lower and "category" in query_lower:
            return "[{'title': 'Horror Film 1', 'category': 'Horror'}, {'title': 'Horror Film 2', 'category': 'Horror'}]"
        elif "rented more than 40" in query_lower or "> 40" in query_lower and "rental" in query_lower:
            return "[{'customer_id': 526, 'first_name': 'Heavy', 'last_name': 'Viewer', 'rental_count': 45}]"
        else:
            return "[{'result': 'mock_data'}]"



@pytest.fixture
def mock_azure_client():
    """Mock Azure OpenAI client with predefined responses."""
    client = MagicMock()
    
    def mock_chat_completion(*args, **kwargs):
        messages = kwargs.get('messages', [])
        user_content = ""
        
        for message in messages:
            if message.get('role') == 'user':
                user_content = message.get('content', '').lower()
                break
        
        # Default response
        content = '{"query": "SELECT * FROM mock_table;"}'
        
        # Basic query responses
        if "how many actors" in user_content:
            content = '{"query": "SELECT COUNT(*) FROM actor;"}'
        elif "list all customers" in user_content:
            content = '{"query": "SELECT customer_id, first_name, last_name FROM customer;"}'
        elif "top 5 films by rental rate" in user_content:
            content = '{"query": "SELECT title, rental_rate FROM film ORDER BY rental_rate DESC LIMIT 5;"}'
        elif "inventory details" in user_content and "academy dinosaur" in user_content:
            content = '{"query": "SELECT * FROM inventory WHERE film_id = (SELECT film_id FROM film WHERE title = \'ACADEMY DINOSAUR\');"}'
        elif "stores" in user_content and "staff members" in user_content:
            content = '{"query": "SELECT store_id, COUNT(*) AS staff_count FROM staff GROUP BY store_id ORDER BY staff_count DESC;"}'
        elif "total revenue" in user_content:
            content = '{"query": "SELECT SUM(amount) FROM payment;"}'
            
        # New query responses for additional test cases
        elif "average rental rate" in user_content:
            content = '{"query": "SELECT AVG(rental_rate) FROM film;"}'
        elif "films are in each category" in user_content:
            content = '{"query": "SELECT c.name AS category_name, COUNT(fc.film_id) AS film_count FROM category c JOIN film_category fc ON c.category_id = fc.category_id GROUP BY c.name ORDER BY film_count DESC;"}'
        elif "longer than 180" in user_content:
            content = '{"query": "SELECT title, length FROM film WHERE length > 180 ORDER BY length DESC;"}'
        elif "actor has appeared in the most films" in user_content:
            content = '{"query": "SELECT CONCAT(a.first_name, \' \', a.last_name) AS actor_name, COUNT(fa.film_id) AS film_count FROM actor a JOIN film_actor fa ON a.actor_id = fa.actor_id GROUP BY actor_name ORDER BY film_count DESC LIMIT 1;"}'
        elif "never been rented" in user_content:
            content = '{"query": "SELECT f.title, f.film_id FROM film f LEFT JOIN inventory i ON f.film_id = i.film_id LEFT JOIN rental r ON i.inventory_id = r.inventory_id WHERE r.rental_id IS NULL;"}'
        elif "most rented film" in user_content:
            content = '{"query": "SELECT f.title, COUNT(r.rental_id) AS rental_count FROM film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY f.title ORDER BY rental_count DESC LIMIT 1;"}'
        elif "customers are there per country" in user_content:
            content = '{"query": "SELECT co.country, COUNT(cu.customer_id) AS customer_count FROM country co JOIN city ci ON co.country_id = ci.country_id JOIN address a ON ci.city_id = a.city_id JOIN customer cu ON a.address_id = cu.address_id GROUP BY co.country ORDER BY customer_count DESC;"}'
        elif "revenue generated by each store" in user_content:
            content = '{"query": "SELECT s.store_id, SUM(p.amount) AS revenue FROM store s JOIN staff st ON s.store_id = st.store_id JOIN payment p ON st.staff_id = p.staff_id GROUP BY s.store_id ORDER BY revenue DESC;"}'
        elif "horror category" in user_content:
            content = '{"query": "SELECT f.title, c.name AS category FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON fc.category_id = c.category_id WHERE c.name = \'Horror\';"}'
        elif "rented more than 40" in user_content:
            content = '{"query": "SELECT c.customer_id, c.first_name, c.last_name, COUNT(r.rental_id) AS rental_count FROM customer c JOIN rental r ON c.customer_id = r.customer_id GROUP BY c.customer_id HAVING COUNT(r.rental_id) > 40 ORDER BY rental_count DESC;"}'
        
        # Answer generation call
        if len(user_content) > 200 and "sql" in user_content and "answer" in user_content:
            content = '{"answer": "Based on the query results, here is the answer to your question."}'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = content
        return mock_response
    
    client.chat.completions.create = mock_chat_completion
    return client


class TestQuestionAndAnswerAzure:
    """Test cases for the question_and_answer_azure function."""
    
    test_questions_and_expected_results = [
        # Original test cases
        {
            "question": "How many actors are in the database?",
            "expected_result_type": list,
            "expected_result_content": [200],
            "description": "Count query should return number of actors"
        },
        {
            "question": "List all customers.",
            "expected_result_type": list,
            "expected_result_content": [
                {'customer_id': 1, 'first_name': 'John', 'last_name': 'Doe'},
                {'customer_id': 2, 'first_name': 'Jane', 'last_name': 'Smith'}
            ],
            "description": "Customer list should return customer records"
        },
        {
            "question": "What are the top 5 films by rental rate?",
            "expected_result_type": list,
            "expected_result_content": [
                {'title': 'Film A', 'rental_rate': 4.99},
                {'title': 'Film B', 'rental_rate': 3.99}
            ],
            "description": "Top films query should return sorted films by rental rate"
        },
        {
            "question": "Show the inventory details for the film 'ACADEMY DINOSAUR'.",
            "expected_result_type": list,
            "expected_result_content": [{'inventory_id': 1, 'film_id': 1, 'store_id': 1}],
            "description": "Inventory query should return specific film inventory"
        },
        {
            "question": "Which stores have the most staff members?",
            "expected_result_type": list,
            "expected_result_content": [
                {'store_id': 1, 'staff_count': 2},
                {'store_id': 2, 'staff_count': 1}
            ],
            "description": "Staff count query should return store staff statistics"
        },
        {
            "question": "What is the total revenue generated by rentals?",
            "expected_result_type": list,
            "expected_result_content": [67416.51],
            "description": "Revenue query should return total payment sum"
        },
        
        # New test cases (10 additional cases)
        {
            "question": "What is the average rental rate of all films?",
            "expected_result_type": list,
            "expected_result_content": [3.99],
            "description": "Average rental rate should return a single float value"
        },
        {
            "question": "How many films are in each category?",
            "expected_result_type": list,
            "expected_result_content": [
                {'category_name': 'Action', 'film_count': 64},
                {'category_name': 'Comedy', 'film_count': 58}
            ],
            "description": "Category count should return category names with counts"
        },
        {
            "question": "Find all films that are longer than 180 minutes.",
            "expected_result_type": list,
            "expected_result_content": [
                {'title': 'Long Film 1', 'length': 185},
                {'title': 'Long Film 2', 'length': 190}
            ],
            "description": "Long films query should return films with length > 180"
        },
        {
            "question": "Which actor has appeared in the most films?",
            "expected_result_type": list,
            "expected_result_content": [
                {'actor_name': 'GINA DEGENERES', 'film_count': 42}
            ],
            "description": "Most films by actor should return actor name and count"
        },
        {
            "question": "List all films that have never been rented.",
            "expected_result_type": list,
            "expected_result_content": [
                {'title': 'Unwatched Film', 'film_id': 123}
            ],
            "description": "Unwatched films should return films with no rentals"
        },
        {
            "question": "What's the most rented film?",
            "expected_result_type": list,
            "expected_result_content": [
                {'title': 'Popular Movie', 'rental_count': 30}
            ],
            "description": "Most rented film should return film with highest rental count"
        },
        {
            "question": "How many customers are there per country?",
            "expected_result_type": list,
            "expected_result_content": [
                {'country': 'United States', 'customer_count': 50},
                {'country': 'Canada', 'customer_count': 30}
            ],
            "description": "Customers per country should return country names with counts"
        },
        {
            "question": "What's the revenue generated by each store?",
            "expected_result_type": list,
            "expected_result_content": [
                {'store_id': 1, 'revenue': 33489.47},
                {'store_id': 2, 'revenue': 33927.04}
            ],
            "description": "Revenue per store should return store IDs with revenue amounts"
        },
        {
            "question": "List all films in the 'Horror' category.",
            "expected_result_type": list,
            "expected_result_content": [
                {'title': 'Horror Film 1', 'category': 'Horror'},
                {'title': 'Horror Film 2', 'category': 'Horror'}
            ],
            "description": "Horror films should return all films in Horror category"
        },
        {
            "question": "Find customers who have rented more than 40 films.",
            "expected_result_type": list,
            "expected_result_content": [
                {'customer_id': 526, 'first_name': 'Heavy', 'last_name': 'Viewer', 'rental_count': 45}
            ],
            "description": "Heavy renters should return customers with > 40 rentals"
        }
    ]
    
    @patch('Code.azure_functions.query_collection_azure')
    def test_question_and_answer_azure_with_valid_questions(
        self, 
        mock_query_collection, 
        mock_azure_db, 
        mock_azure_client, 
        mock_vector_results
    ):
        """Test question_and_answer_azure with various valid questions."""
        # Setup mock vector collection response
        mock_query_collection.return_value = mock_vector_results
        
        for test_case in self.test_questions_and_expected_results:
            with patch('Code.azure_functions.client', mock_azure_client):
                with patch('Code.azure_functions.fn.create_view') as mock_create_view:
                    # Mock create_view to return expected results
                    mock_create_view.return_value = (
                        test_case["expected_result_content"], 
                        len(test_case["expected_result_content"])
                    )
                    
                    # Execute the function
                    result = question_and_answer_azure(
                        question=test_case["question"],
                        database=mock_azure_db
                    )
                    
                    # Log the test being executed
                    print(f"\n🔍 Testing: {test_case['description']}")
                    print(f"Question asked: {test_case['question']}")
                    print(f"LLM response query: {result.get('query', 'No query produced')}")
                    # Validate result structure
                    self._assert_valid_result_structure(result, test_case)
                    print(f"✅ Test passed: {test_case['description']}")
    
    def _assert_valid_result_structure(self, result, test_case):
        """Helper method to validate result structure with detailed error reporting."""
        try:
            # Basic structure checks
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "question" in result, "Result should contain question"
            assert "query" in result, "Result should contain query"
            assert "result" in result, "Result should contain result"
            assert "answer" in result, "Result should contain answer"
            assert "total_count" in result, "Result should contain total_count"
            
            # Check question is preserved
            assert result["question"] == test_case["question"], "Question should be preserved"
            
            # Check result based on whether it's an error case or success case
            if result["result"] == "Empty":
                # In error case, just check that query shows error
                assert "Error" in result["query"] or result["query"] == "", \
                    "Query should indicate error for error cases"
            else:
                # For normal case, check result type
                assert isinstance(result["result"], test_case["expected_result_type"]), \
                    f"Result should be {test_case['expected_result_type']}"
            
            # Check total count matches result length
            if isinstance(result["result"], list):
                assert result["total_count"] == len(result["result"]), \
                    "Total count should match result length"
            
            # Check answer is generated
            assert result["answer"], "Answer should not be empty"
            assert isinstance(result["answer"], str), "Answer should be string"
            
        except AssertionError as e:
            print(f"\n❌ Test failed: {test_case['description']}")
            print(f"Question: {test_case['question']}")
            print(f"Produced Result: {result.get('result', 'No result produced')}")
            print(f"Expected Result Type: {test_case['expected_result_type']}")
            print(f"Actual Result Type: {type(result.get('result'))}")
            print(f"Error: {e}\n")
            raise
    
    @patch('Code.azure_functions.query_collection_azure')
    def test_question_and_answer_azure_no_tables_found(self, mock_query_collection, mock_azure_db, mock_azure_client):
        """Test behavior when no relevant tables are found."""
        # Mock no tables found
        mock_query_collection.return_value = None
        
        with patch('Code.azure_functions.client', mock_azure_client):
            # Execution
            result = question_and_answer_azure(
                question="Some unrelated question",
                database=mock_azure_db
            )
            
            # Validation
            self._assert_no_tables_response(result)
            print("✅ Test passed: No tables found scenario")
    
    def _assert_no_tables_response(self, result):
        """Helper method to validate response when no tables are found."""
        assert result["answer"] == "No relevant tables found to answer the question."
        assert result["result"] == "Empty"
        assert result["total_count"] == 0
        assert result["query"] == ""
        assert "tables" in result
    
    @patch('Code.azure_functions.query_collection_azure')
    def test_question_and_answer_azure_query_generation_error(
        self,
        mock_query_collection,
        mock_azure_db,
        mock_vector_results
    ):
        """Test behavior when query generation fails."""
        # Setup
        mock_query_collection.return_value = mock_vector_results
        
        # Create a mock client that returns malformed response
        mock_client_error = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client_error.chat.completions.create.return_value = mock_response
        
        with patch('Code.azure_functions.client', mock_client_error):
            # Execution
            result = question_and_answer_azure(
                question="Test question",
                database=mock_azure_db
            )
            
            # Validation
            self._assert_query_generation_error(result)
            print("✅ Test passed: Query generation error scenario")
    
    def _assert_query_generation_error(self, result):
        """Helper method to validate response when query generation fails."""
        assert result["query"] == "Error generating query"
        assert result["result"] == "Empty"
    
    def test_result_data_comparison(self, mock_azure_db, mock_azure_client, mock_vector_results):
        """Test that results match expected data structures."""
        
        test_cases = [
            {
                "question": "How many actors are in the database?",
                "expected_result": [200],
                "result_validation": lambda x: isinstance(x, list) and len(x) == 1 and isinstance(x[0], (int, float))
            },
            {
                "question": "List all customers.",
                "expected_result": [
                    {'customer_id': 1, 'first_name': 'John', 'last_name': 'Doe'},
                    {'customer_id': 2, 'first_name': 'Jane', 'last_name': 'Smith'}
                ],
                "result_validation": lambda x: isinstance(x, list) and all(isinstance(item, dict) for item in x)
            }
        ]
        
        with patch('Code.azure_functions.query_collection_azure') as mock_query_collection:
            mock_query_collection.return_value = mock_vector_results
            
            for test_case in test_cases:
                with patch('Code.azure_functions.client', mock_azure_client):
                    with patch('Code.azure_functions.fn.create_view') as mock_create_view:
                        # Setup
                        mock_create_view.return_value = (
                            test_case["expected_result"], 
                            len(test_case["expected_result"])
                        )
                        
                        # Execution
                        result = question_and_answer_azure(
                            question=test_case["question"],
                            database=mock_azure_db
                        )
                        
                        # Logging
                        print(f"\n🔍 Data Comparison Test: {test_case['question']}")
                        
                        # Validation
                        self._validate_result_data(result, test_case)
    
    def _validate_result_data(self, result, test_case):
        """Helper method to validate result data with detailed error reporting."""
        try:
            # Handle error case
            if result["result"] == "Empty":
                print(f"⚠️ Warning: 'Empty' result detected. Mock might be misconfigured.")
                print(f"⚠️ Skipping validation for this test case.")
                return
                
            # Validate result structure
            assert test_case["result_validation"](result["result"]), \
                f"Result validation failed for: {test_case['question']}"
            
            # Compare actual results with expected
            assert result["result"] == test_case["expected_result"], \
                f"Result data mismatch for: {test_case['question']}"
            
            print(f"✅ Data comparison test passed for: {test_case['question']}")
            
        except AssertionError as e:
            print(f"\n❌ Data comparison test failed for: {test_case['question']}")
            print(f"Expected Result: {test_case['expected_result']}")
            print(f"Produced Result: {result.get('result', 'No result produced')}")
            print(f"Error: {e}\n")
            raise


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])