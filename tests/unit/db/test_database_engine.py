"""
Unit tests for the database_configuration module in the Neighbour Approved application.

This module tests:
- Engine creation and session factory settings
- get_engine() and create_session() methods
- Event listeners for timezone and search_path
- verify_database_connection() to confirm DB access
- init_database() table creation

Typical usage example:
    pytest tests/unit/test_database_configuration.py

Dependencies:
    - pytest
    - pytest-mock or unittest.mock
    - SQLAlchemy
    - The database_configuration module under test
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.db.database_engine import (
    engine,
    SessionLocal,
    get_engine,
    create_session,
    verify_database_connection,
    init_database,
    Base,
)


def test_engine_is_created():
    """
    Test that the global 'engine' object is an instance of SQLAlchemy Engine.
    """
    assert isinstance(engine, Engine)


def test_sessionlocal_is_callable():
    """
    Test that SessionLocal returns a valid Session object.
    """
    session = SessionLocal()
    assert isinstance(session, Session)
    session.close()


@patch("app.db.database_engine.create_engine")
def test_get_engine(mock_create_engine):
    """
    Test that get_engine() returns the global engine, and doesn't re-create it if it exists.
    """
    # If 'engine' is already created, get_engine() should just return it,
    # so 'create_engine' won't be called again.
    result = get_engine()
    mock_create_engine.assert_not_called()
    assert result is engine


def test_create_session():
    """
    Test that create_session() returns a Session object from SessionLocal.
    """
    db_session = create_session()
    assert isinstance(db_session, Session)
    db_session.close()


@patch("app.db.database_engine.create_session")
def test_verify_database_connection_success(mock_create_session):
    """
    Test verify_database_connection() returns True when query executes successfully.
    """
    # 1) Create a mock that acts like a context manager
    mock_session = MagicMock()
    # Tells the mock: "If used in a 'with' block, yield 'mock_session'"
    mock_session.__enter__.return_value = mock_session

    # 2) Make sure create_session() returns our mock
    mock_create_session.return_value = mock_session

    # 3) Set up a successful query result
    mock_session.execute.return_value = None

    # 4) Call verify_database_connection(), expecting success
    from app.db.database_engine import verify_database_connection

    assert verify_database_connection() is True

    # 5) Validate calls
    mock_create_session.assert_called_once()
    mock_session.__enter__.assert_called_once()  # with-block
    mock_session.__exit__.assert_called_once()  # end of with-block
    mock_session.execute.assert_called_once_with("SELECT 1")
    mock_session.close.assert_not_called()
    # or depends on your code if 'close()' is also expected


@patch("app.db.database_engine.create_session")
def test_verify_database_connection_failure(mock_create_session):
    mock_session = MagicMock()
    # Make the session behave like a context manager
    mock_session.__enter__.return_value = mock_session
    mock_create_session.return_value = mock_session

    # Force an error on session.execute
    from sqlalchemy.exc import SQLAlchemyError

    mock_session.execute.side_effect = SQLAlchemyError("DB error")

    from app.db.database_engine import verify_database_connection

    assert verify_database_connection() is False

    mock_session.execute.assert_called_once_with("SELECT 1")


@patch("app.db.database_engine.create_session")
def test_verify_database_connection_unexpected_error(mock_create_session):
    """
    Test that verify_database_connection re-raises non-SQLAlchemyError exceptions.
    This covers the line that raises e if it's not SQLAlchemyError.
    """
    from sqlalchemy.orm import Session

    mock_session = MagicMock(spec=Session)
    # Make the session behave like a context manager
    mock_session.__enter__.return_value = mock_session
    mock_create_session.return_value = mock_session

    # Side effect is a non-SQLAlchemyError => triggers 'raise e' path
    mock_session.execute.side_effect = ValueError("Non-SQL error")

    from app.db.database_engine import verify_database_connection

    # We expect it to bubble up as a ValueError, not return True/False
    with pytest.raises(ValueError, match="Non-SQL error"):
        verify_database_connection()

    # The session was still opened and closed
    mock_session.__enter__.assert_called_once()
    mock_session.__exit__.assert_called_once()
    mock_session.execute.assert_called_once_with("SELECT 1")


@patch("app.db.database_engine.create_session")
@patch("app.db.database_engine.Base.metadata.create_all")
def test_init_database(mock_create_all, mock_create_session):
    """
    Test that init_database() calls Base.metadata.create_all with the global engine.
    """
    # Call init_database
    init_database()

    # create_all should be invoked with bind=engine
    mock_create_all.assert_called_once_with(bind=engine)
    # No session usage required for init_database, so no calls to create_session
    mock_create_session.assert_not_called()


def test_set_postgres_timezone(mocker):
    """
    Test the 'set_postgres_timezone' event listener by simulating an Engine-level event.
    """
    # We'll import the event function from the module,
    # then manually call it with a mock dbapi_connection
    from app.db.database_engine import set_postgres_timezone

    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    # Call the listener function
    set_postgres_timezone(mock_connection, None)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SET TIME ZONE 'UTC'")
    mock_cursor.close.assert_called_once()


def test_set_search_path(mocker):
    """
    Test the 'set_search_path' event listener by simulating an Engine-level event.
    """
    from app.db.database_engine import set_search_path

    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    set_search_path(mock_connection, None)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SET search_path TO public")
    mock_cursor.close.assert_called_once()
