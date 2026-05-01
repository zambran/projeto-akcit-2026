"""Test fixtures for the task tracker."""

import pytest

from tracker.database import get_connection


@pytest.fixture
def conn():
    """In-memory SQLite database for isolated tests."""
    connection = get_connection(":memory:")
    yield connection
    connection.close()
