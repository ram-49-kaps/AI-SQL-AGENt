"""
Pytest configuration — ensures database is initialized before tests.
"""

import pytest
from app.database import init_db


@pytest.fixture(autouse=True, scope="session")
def setup_database():
    """Initialize the database once for the entire test session."""
    init_db()
    yield


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests that require LLM API key (deselect with '-m \"not integration\"')"
    )
