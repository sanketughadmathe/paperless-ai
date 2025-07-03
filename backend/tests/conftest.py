import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.supabase_client import get_supabase_client
from supabase import Client
import os


# Mock Supabase client for testing
class MockSupabaseClient:
    def from_(self, table_name: str):
        return MockSupabaseTable(table_name)

    @property
    def auth(self):
        return MockSupabaseAuth()


class MockSupabaseTable:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self._data = []  # Simple in-memory store for mocks

    def select(self, *args):
        return self

    def eq(self, column, value):
        return self

    def limit(self, count):
        return self

    def single(self):
        return self

    def insert(self, data):
        self._data.append(data)
        return self

    def update(self, data):
        return self

    def delete(self):
        return self

    def execute(self):
        # Simulate Supabase response structure
        if self.table_name == "profiles":
            # Return dummy data for healthcheck
            return type("obj", (object,), {"data": [{"id": "some-uuid"}]})()
        return type("obj", (object,), {"data": self._data})()


class MockSupabaseAuth:
    def sign_up(self, credentials):
        # Simulate successful signup
        return type(
            "obj",
            (object,),
            {"user": {"id": "mock-user-id", "email": credentials["email"]}},
        )()

    def sign_in_with_password(self, credentials):
        # Simulate successful login
        return type(
            "obj", (object,), {"session": {"access_token": "mock-access-token"}}
        )()

    def get_user(self, token):
        if token == "mock-access-token":
            return type(
                "obj",
                (object,),
                {"user": {"id": "mock-user-id", "email": "test@example.com"}},
            )()
        return type("obj", (object,), {"user": None})()


@pytest.fixture(name="client")
def client_fixture():
    """FastAPI TestClient fixture."""
    # Override the get_supabase_client dependency for testing
    app.dependency_overrides[get_supabase_client] = lambda: MockSupabaseClient()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()  # Clear overrides after test


@pytest.fixture(name="mock_supabase")
def mock_supabase_fixture():
    """Fixture to provide a mock Supabase client directly."""
    return MockSupabaseClient()
