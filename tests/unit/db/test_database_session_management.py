"""
Unit tests for the database_session_management module in the Neighbour Approved application.

This module tests:
- get_db: FastAPI dependency function that yields a database session.
- session_scope: Context manager for handling a session with automatic commit/rollback.
- DatabaseSessionManager: A class with explicit session lifecycle methods.

Typical usage example:
    pytest tests/unit/test_database_session_management.py

Dependencies:
    - pytest
    - pytest-mock or unittest.mock for session mocking
    - fastapi.HTTPException
    - The database_session_management module under test
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.database_session_management import (
    get_db,
    session_scope,
    DatabaseSessionManager,
)


# ---- get_db tests ----


def test_get_db_normal_flow(mocker):
    """
    Test that get_db yields a session and closes it normally with no exceptions.
    """
    session_mock = mocker.MagicMock(spec=Session)
    session_local_mock = mocker.patch(
        "app.db.database_session_management.SessionLocal", return_value=session_mock
    )

    # Create the generator and retrieve the session
    gen = get_db()
    db_session = next(gen)
    assert db_session == session_mock

    # Close the generator gracefully => triggers the 'finally:' block
    gen.close()

    # Confirm we got the session once, and it was closed (no rollback)
    session_local_mock.assert_called_once()
    session_mock.close.assert_called_once()
    session_mock.rollback.assert_not_called()


def test_get_db_exception_rollback(mocker):
    """
    Test that get_db rolls back and raises HTTPException if an exception
    occurs inside the generator block.
    """
    session_mock = mocker.MagicMock(spec=Session)
    mocker.patch(
        "app.db.database_session_management.SessionLocal", return_value=session_mock
    )

    with pytest.raises(HTTPException) as excinfo:
        gen = get_db()
        db_session = next(gen)  # yield the session

        # This injects the ValueError directly into the generator,
        # triggering its `except Exception as e:` block
        gen.throw(ValueError("Some DB error"))

    # We confirm rollback and close were called
    session_mock.rollback.assert_called_once()
    session_mock.close.assert_called_once()

    # Confirm the exception info
    assert excinfo.value.status_code == 500
    assert "Database error occurred" in excinfo.value.detail


# ---- session_scope tests ----


def test_session_scope_commit(mocker):
    """
    Test that session_scope commits when no exception occurs.
    """
    session_mock = mocker.MagicMock(spec=Session)
    session_local_mock = mocker.patch(
        "app.db.database_session_management.SessionLocal", return_value=session_mock
    )

    with session_scope() as s:
        assert s == session_mock
        s.add.assert_not_called()

    # Confirm normal flow => commit, close
    session_mock.commit.assert_called_once()
    session_mock.close.assert_called_once()
    session_mock.rollback.assert_not_called()
    session_local_mock.assert_called_once()


def test_session_scope_rollback(mocker):
    """
    Test that session_scope rolls back if an exception is raised inside the context.
    """
    session_mock = mocker.MagicMock(spec=Session)
    mocker.patch(
        "app.db.database_session_management.SessionLocal", return_value=session_mock
    )

    with pytest.raises(RuntimeError, match="Simulated error"):
        with session_scope() as s:
            assert s == session_mock
            raise RuntimeError("Simulated error")

    # Confirm rollback and close were called
    session_mock.rollback.assert_called_once()
    session_mock.close.assert_called_once()
    session_mock.commit.assert_not_called()


# ---- DatabaseSessionManager tests ----


def test_database_session_manager_get_session(mocker):
    """
    Test that DatabaseSessionManager.get_session() returns a new session from SessionLocal.
    """
    session_mock = mocker.MagicMock(spec=Session)
    session_local_mock = mocker.patch(
        "app.db.database_session_management.SessionLocal", return_value=session_mock
    )

    session_manager = DatabaseSessionManager()
    session = session_manager.get_session()

    assert session == session_mock
    session_local_mock.assert_called_once()


def test_database_session_manager_commit(mocker):
    """
    Test that DatabaseSessionManager.commit() calls session.commit().
    """
    session_mock = mocker.MagicMock(spec=Session)
    DatabaseSessionManager.commit(session_mock)
    session_mock.commit.assert_called_once()


def test_database_session_manager_rollback(mocker):
    """
    Test that DatabaseSessionManager.rollback() calls session.rollback().
    """
    session_mock = mocker.MagicMock(spec=Session)
    DatabaseSessionManager.rollback(session_mock)
    session_mock.rollback.assert_called_once()


def test_database_session_manager_close(mocker):
    """
    Test that DatabaseSessionManager.close() calls session.close().
    """
    session_mock = mocker.MagicMock(spec=Session)
    DatabaseSessionManager.close(session_mock)
    session_mock.close.assert_called_once()
