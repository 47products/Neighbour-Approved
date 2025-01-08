"""
Database session management module.

This module provides utilities for managing database sessions within the application,
ensuring proper handling of database connections and transactions. It implements
a dependency that can be used in FastAPI endpoints to obtain database sessions
that are automatically closed after use.

The module follows best practices for connection management, including proper
resource cleanup and error handling. It provides type-safe session handling
while maintaining efficient connection pooling through SQLAlchemy.
"""

from typing import Generator, Any
from contextlib import contextmanager
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.database_configuration import SessionLocal


def get_db() -> Generator[Session, Any, None]:
    """
    FastAPI dependency that provides a database session and ensures proper cleanup.

    This dependency yields a database session that can be used within FastAPI
    endpoint functions. The session is automatically closed when the endpoint
    processing is complete, ensuring proper resource management even in case
    of errors.

    Yields:
        Session: An active database session from the connection pool

    Raises:
        HTTPException: If a database error occurs during session creation
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        ) from e
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, Any, None]:
    """
    Context manager for handling database sessions in background tasks.

    This context manager provides a database session with automatic commit/rollback
    handling. It should be used for database operations outside of HTTP request
    handling, such as background tasks or scheduled jobs.

    Yields:
        Session: An active database session

    Example:
        with session_scope() as session:
            session.add(some_object)
            # Session is automatically committed if no exception occurs
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseSessionManager:
    """
    Manager class for handling database sessions with explicit lifecycle control.

    This class provides methods for obtaining and managing database sessions
    with explicit control over the session lifecycle. It's useful for cases
    where the automatic session management through dependencies or context
    managers isn't suitable.

    Example:
        session_manager = DatabaseSessionManager()
        session = session_manager.get_session()
        try:
            # Use session
            session_manager.commit(session)
        except Exception:
            session_manager.rollback(session)
        finally:
            session_manager.close(session)
    """

    @staticmethod
    def get_session() -> Session:
        """
        Create and return a new database session.

        Returns:
            Session: A new database session
        """
        return SessionLocal()

    @staticmethod
    def commit(session: Session) -> None:
        """
        Commit the current transaction on the given session.

        Args:
            session: The database session to commit
        """
        session.commit()

    @staticmethod
    def rollback(session: Session) -> None:
        """
        Roll back the current transaction on the given session.

        Args:
            session: The database session to roll back
        """
        session.rollback()

    @staticmethod
    def close(session: Session) -> None:
        """
        Close the given database session.

        Args:
            session: The database session to close
        """
        session.close()
