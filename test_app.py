import unittest
import json
import os
from unittest.mock import patch, MagicMock, ANY
from functools import wraps

# Import the Flask app instance and SQLAlchemy models from your app.py
# This line will execute the top-level code in app.py.
# The setUpClass method below attempts to patch global resources before they are fully used.
from app import app, Task, User
from sqlalchemy.orm import Session # For type hinting and spec for mocks

class BaseTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Patch environment variables. This affects os.getenv calls within functions.
        # Note: load_dotenv() at the top of app.py and other modules likely ran at import time.
        cls.env_patch = patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:", # Use a mock DB URL
            "JWT_KEY": "test_jwt_secret_for_testing",
            "OW_KEY": "test_ow_api_key_for_testing"
        })
        cls.env_patch.start()

        # Patch SQLAlchemy engine creation to prevent real DB connections.
        cls.create_engine_patcher = patch('app.create_engine')
        cls.mock_engine = cls.create_engine_patcher.start()

        # Patch Base.metadata.create_all to prevent DDL operations.
        cls.meta_create_all_patcher = patch('app.Base.metadata.create_all')
        cls.mock_create_all = cls.meta_create_all_patcher.start()

        # Patch SessionLocal used in app.py for initial data seeding.
        # This prevents the seeding logic from running or erroring with a mock engine.
        cls.app_session_local_patcher = patch('app.SessionLocal')
        mock_sl_constructor = cls.app_session_local_patcher.start()
        mock_session_for_seeding = MagicMock(spec=Session)
        mock_query_for_seeding = MagicMock()
        mock_query_for_seeding.count.return_value = 1 # Pretend DB is not empty to skip seeding.
        mock_session_for_seeding.query.return_value = mock_query_for_seeding
        # Handle 'with SessionLocal() as session:' context manager.
        mock_sl_constructor.return_value.__enter__.return_value = mock_session_for_seeding
        # Also mock direct call if not used as context manager (though it is in app.py).
        mock_sl_constructor.return_value = mock_session_for_seeding

        # Configure the Flask app for testing.
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config['SECRET_KEY'] = 'test_flask_secret_key' # For Flask sessions, etc.

        # Use the globally imported app instance for the test client.
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.app_session_local_patcher.stop()
        cls.meta_create_all_patcher.stop()
        cls.create_engine_patcher.stop()
        cls.env_patch.stop()

    def setUp(self):
        # The client is set up at the class level.
        self.client = BaseTestCase.client

        # Mock app.db_conn (the scoped_session factory).
        # This ensures that when db_conn() is called in routes, it returns self.mock_db_session.
        self.mock_db_session = MagicMock(spec=Session)
        self.db_conn_patcher = patch('app.db_conn') # app.db_conn is the factory.
        mock_db_conn_factory = self.db_conn_patcher.start()
        mock_db_conn_factory.return_value = self.mock_db_session

        # Mock the credential_logic.validate_token decorator.
        self.validate_token_patcher = patch('app.credential_logic.validate_token', autospec=True)
        mock_validate_token_decorator = self.validate_token_patcher.start()
        def mock_decorator_side_effect(original_func):
            @wraps(original_func)
            def wrapper(*args, **kwargs):
                # Injects current_userid=1 as the first argument to the wrapped route function.
                return original_func(1, *args, **kwargs) # Dummy current_userid = 1
            return wrapper
        mock_validate_token_decorator.side_effect = mock_decorator_side_effect

        # Mock other functions from credential_logic.
        self.create_user_patcher = patch('app.credential_logic.create_user', autospec=True)
        self.mock_create_user = self.create_user_patcher.start()

        self.validate_credentials_patcher = patch('app.credential_logic.validate_credentials', autospec=True)
        self.mock_validate_credentials = self.validate_credentials_patcher.start()

        self.create_access_token_patcher = patch('app.credential_logic.create_access_token', autospec=True)
        self.mock_create_access_token = self.create_access_token_patcher.start()

        # Mock builders.add_tasks_new.
        self.add_tasks_new_patcher = patch('app.builders.add_tasks_new', autospec=True)
        self.mock_add_tasks_new = self.add_tasks_new_patcher.start()
        # Provide a default side effect for add_tasks_new to simplify tests.
        self.mock_add_tasks_new.side_effect = lambda task_obj: {
            "id": task_obj.id, "description": task_obj.description, "completed": task_obj.completed,
            "due_date": task_obj.due_date, "location": task_obj.location,
            "weather": "mocked_weather_data" if task_obj.location else None
        }

        # Mock helperUtil.bool_cleaner.
        self.bool_cleaner_patcher = patch('app.helperUtil.bool_cleaner', autospec=True)
        self.mock_bool_cleaner = self.bool_cleaner_patcher.start()
        def bool_cleaner_side_effect(value): # Simplified mock
            if isinstance(value, bool): return value
            if isinstance(value, str):
                if value.lower() == 'true': return True
                if value.lower() == 'false': return False
            return value # Return original for unhandled cases (e.g., error tuple)
        self.mock_bool_cleaner.side_effect = bool_cleaner_side_effect


    def tearDown(self):
        # Stop all patches started with .start() during this test method.
        patch.stopall()


class TestIndexRoute(BaseTestCase):
    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, 'Hello World!')

class TestAuthRoutes(BaseTestCase):
    def test_register_user_success(self):
        self.mock_db_session.scalars.return_value.first.return_value = None # User does not exist
        self.mock_create_user.return_value = ['newuser', 'hashed_password']
        
        response = self.client.post("/register", json={"username": "newuser", "password": "password"})
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, 'User Created Successfully')
        self.mock_db_session.add.assert_called_once()
        self.mock_db_session.commit.assert_called_once()
        added_user = self.mock_db_session.add.call_args[0][0]
        self.assertEqual(added_user.username, 'newuser')
        self.assertEqual(added_user.hashed_password, 'hashed_password')

    def test_register_user_already_exists(self):
        existing_user = User(id=1, username="existinguser", hashed_password="password")
        self.mock_db_session.scalars.return_value.first.return_value = existing_user # User exists
        
        response = self.client.post("/register", json={"username": "existinguser", "password": "password"})
        
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json, 'Username already exists.')

    def test_register_user_no_data(self):
        # The route currently doesn't explicitly handle this before `request.get_json()`
        # which might raise a Werkzeug BadRequest if content type is not JSON.
        # If `user_req` becomes None, it falls through. Let's assume Flask handles it or it's a 400.
        response = self.client.post("/register") # No JSON data
        # Depending on Flask/Werkzeug behavior for missing JSON, this might be 400 or 415.
        # The current code `if user_req:` implies if it's None, it does nothing and returns Flask's default.
        # For this test, we'll expect a 400 as it's a common response for bad requests.
        self.assertIn(response.status_code, [400, 415])


    def test_login_user_success(self):
        mock_user_db = User(id=1, username="testuser", hashed_password="hashed_password_from_db")
        self.mock_db_session.scalars.return_value.first.return_value = mock_user_db
        self.mock_validate_credentials.return_value = True
        self.mock_create_access_token.return_value = {"access_token": "test_token"}
        
        response = self.client.post("/login", json={"username": "testuser", "password": "password"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"access_token": "test_token"})
        self.mock_validate_credentials.assert_called_with("password", "hashed_password_from_db")
        self.mock_create_access_token.assert_called_with(1) # User ID

    def test_login_user_invalid_credentials(self):
        mock_user_db = User(id=1, username="testuser", hashed_password="hashed_password_from_db")
        self.mock_db_session.scalars.return_value.first.return_value = mock_user_db
        self.mock_validate_credentials.return_value = False
        
        response = self.client.post("/login", json={"username": "testuser", "password": "wrongpassword"})
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {'message': 'Invalid credentials'})

    def test_login_user_not_found(self):
        self.mock_db_session.scalars.return_value.first.return_value = None # User not found
        
        response = self.client.post("/login", json={"username": "unknownuser", "password": "password"})
        
        self.assertEqual(response.status_code, 401) # As per current logic
        self.assertEqual(response.json, {'message': 'Invalid credentials'})

    def test_login_user_missing_fields(self):
        response = self.client.post("/login", json={"username": "testuser"}) # Missing password
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'Username and password required'})

        response = self.client.post("/login", json={"password": "password"}) # Missing username
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'Username and password required'})

        response = self.client.post("/login", json={}) # Missing both
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'Username and password required'})

class TestTaskCRUDRoutes(BaseTestCase):
    def test_display_tasks_all_success(self):
        mock_task1 = Task(id=1, description="Task 1", completed=False, due_date="2024-01-01", location="Office", owner_id=1)
        mock_task2 = Task(id=2, description="Task 2", completed=True, due_date="2024-01-02", location=None, owner_id=1)
        self.mock_db_session.scalars.return_value.all.return_value = [mock_task1, mock_task2]
        
        # Configure mock_add_tasks_new to return specific dicts for these tasks
        def side_effect_add_tasks(task_obj):
            if task_obj.id == 1:
                return {"id": 1, "description": "Task 1", "completed": False, "due_date": "2024-01-01", "location": "Office", "weather": "Cloudy"}
            if task_obj.id == 2:
                return {"id": 2, "description": "Task 2", "completed": True, "due_date": "2024-01-02", "location": None, "weather": None}
            return {} # Default
        self.mock_add_tasks_new.side_effect = side_effect_add_tasks

        response = self.client.get("/tasks/") # current_userid=1 injected by mock decorator
        
        self.assertEqual(response.status_code, 200)
        expected_json = [
            {"id": 1, "description": "Task 1", "completed": False, "due_date": "2024-01-01", "location": "Office", "weather": "Cloudy"},
            {"id": 2, "description": "Task 2", "completed": True, "due_date": "2024-01-02", "location": None, "weather": None}
        ]
        self.assertEqual(response.json, expected_json)
        self.mock_db_session.scalars.assert_called_once() # Ensure query was made

    def test_display_task_specific_success(self):
        mock_task = Task(id=1, description="Specific Task", completed=False, due_date="2024-01-01", location="Home", owner_id=1)
        self.mock_db_session.scalars.return_value.first.return_value = mock_task
        self.mock_add_tasks_new.return_value = {"id": 1, "description": "Specific Task", "completed": False, "due_date": "2024-01-01", "location": "Home", "weather": "Sunny"}

        response = self.client.get("/tasks/1")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"id": 1, "description": "Specific Task", "completed": False, "due_date": "2024-01-01", "location": "Home", "weather": "Sunny"})

    def test_display_task_specific_not_found(self):
        self.mock_db_session.scalars.return_value.first.return_value = None # Task not found
        response = self.client.get("/tasks/999")
        self.assertEqual(response.status_code, 404)

    def test_add_new_task_with_location(self):
        task_data = {"id": "10", "description": "New Task Location", "completed": "true", "due_date": "2024-12-31", "location": "Park"}
        self.mock_bool_cleaner.return_value = True # Assume 'true' -> True

        response = self.client.post("/tasks/", json=task_data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_data(as_text=True), 'POST CREATED')
        self.mock_db_session.add.assert_called_once()
        added_task = self.mock_db_session.add.call_args[0][0]
        self.assertEqual(added_task.id, 10)
        self.assertEqual(added_task.description, "New Task Location")
        self.assertTrue(added_task.completed)
        self.assertEqual(added_task.location, "Park")
        self.assertEqual(added_task.owner_id, 1) # From mocked current_userid
        self.mock_db_session.commit.assert_called_once()

    def test_add_new_task_without_location(self):
        task_data = {"id": "11", "description": "New Task No Location", "completed": "false", "due_date": "2025-01-01"}
        self.mock_bool_cleaner.return_value = False # Assume 'false' -> False

        response = self.client.post("/tasks/", json=task_data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_data(as_text=True), 'POST CREATED')
        added_task = self.mock_db_session.add.call_args[0][0]
        self.assertIsNone(added_task.location)
        self.assertEqual(added_task.owner_id, 1)

    def test_add_new_task_no_data(self):
        response = self.client.post("/tasks/") # No JSON body
        # Current app.py logic: `if new_task:` (where new_task is None) -> else: abort(404)
        self.assertEqual(response.status_code, 404) # Based on current app.py logic

    def test_update_task_success(self):
        existing_task = Task(id=5, description="Old Desc", completed=False, due_date="2023-01-01", location="Old Loc", owner_id=1)
        self.mock_db_session.get.return_value = existing_task
        
        update_data = {"description": "New Desc", "completed": True, "location": "New Loc"}
        # Note: The app's update logic for 'completed' has its own string parsing.
        # We are testing that logic here, not helperUtil.bool_cleaner for this specific field if not used.

        response = self.client.put("/tasks/5", json=update_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['description'], "New Desc")
        self.assertTrue(response.json['completed'])
        # The response from PUT doesn't include location, as per app.py
        # self.assertEqual(response.json['location'], "New Loc") # This would fail based on current PUT response
        
        self.assertEqual(existing_task.description, "New Desc")
        self.assertTrue(existing_task.completed)
        self.assertEqual(existing_task.location, "New Loc")
        self.mock_db_session.commit.assert_called_once()

    def test_update_task_completed_from_string_true(self):
        existing_task = Task(id=6, description="Test", completed=False, due_date="2023-01-01", owner_id=1)
        self.mock_db_session.get.return_value = existing_task
        update_data = {"completed": "true"}
        response = self.client.put("/tasks/6", json=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['completed'])
        self.assertTrue(existing_task.completed)

    def test_update_task_completed_from_string_false(self):
        existing_task = Task(id=7, description="Test", completed=True, due_date="2023-01-01", owner_id=1)
        self.mock_db_session.get.return_value = existing_task
        update_data = {"completed": "false"}
        response = self.client.put("/tasks/7", json=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['completed'])
        self.assertFalse(existing_task.completed)

    def test_update_task_invalid_completed_string(self):
        existing_task = Task(id=8, description="Test", completed=False, due_date="2023-01-01", owner_id=1)
        self.mock_db_session.get.return_value = existing_task
        update_data = {"completed": "maybe"}
        response = self.client.put("/tasks/8", json=update_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "Invalid value for 'completed'. Must be true or false."})


    def test_update_task_not_found(self):
        self.mock_db_session.get.return_value = None # Task not found
        response = self.client.put("/tasks/999", json={"description": "Doesn't matter"})
        self.assertEqual(response.status_code, 404)

    def test_delete_task_success(self):
        mock_task_to_delete = Task(id=20, description="To Delete", owner_id=1)
        self.mock_db_session.get.return_value = mock_task_to_delete
        
        # DELETE route in app.py expects a JSON body, even if not used for deletion criteria.
        response = self.client.delete("/tasks/20", json={"confirm": True}) 
        
        self.assertEqual(response.status_code, 204) # No Content
        self.mock_db_session.delete.assert_called_with(mock_task_to_delete)
        self.mock_db_session.commit.assert_called_once()

    def test_delete_task_not_found(self):
        self.mock_db_session.get.return_value = None # Task not found
        response = self.client.delete("/tasks/999", json={"confirm": True})
        self.assertEqual(response.status_code, 404) # Falls into `if db_obj:` else abort(404)

    def test_delete_task_no_request_body(self):
        # The app.py code: `if new_task == None: abort(404)`
        response = self.client.delete("/tasks/21") # No JSON body
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

