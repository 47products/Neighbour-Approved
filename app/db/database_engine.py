# pylint: disable=unused-import
"""
Database configuration and engine setup module.

This module establishes the core database configuration for the application,
including the SQLAlchemy engine setup, session management, and declarative base
configuration. It implements connection pooling and proper engine configuration
for optimal database performance and reliability.

The module integrates with the application's configuration management system
to handle database credentials and connection parameters securely while
providing flexibility for different deployment environments.
"""

from typing import Any, Dict
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.core.config import Settings

# Initialize settings from environment
settings = Settings()

# Configure database connection parameters
connection_args: Dict[str, Any] = {
    "pool_pre_ping": True,  # Enable connection health checks
    "pool_size": 5,  # Initial pool size
    "max_overflow": 10,  # Maximum number of connections above pool_size
    "pool_timeout": 30,  # Timeout for getting connection from pool
    "pool_recycle": 1800,  # Recycle connections after 30 minutes
    "echo": settings.ENABLE_SQL_ECHO,  # SQL query logging
    "poolclass": QueuePool,  # Use QueuePool for connection pooling
}

# Create the database URL
database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD.get_secret_value(),
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    database=settings.POSTGRES_DB,
)

# Create the SQLAlchemy engine
engine = create_engine(
    database_url,
    **connection_args,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create declarative base for models
Base = declarative_base()

# Import all models so they are registered in Base.metadata.
from app.db.models import (
    category_model,
    community_member_model,
    community_model,
    contact_endorsement_model,
    contact_model,
    role_model,
    service_model,
    user_model,
)


@event.listens_for(Engine, "connect")
def set_postgres_timezone(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    """
    Set timezone to UTC for all database connections.

    This event listener ensures that all database connections use UTC
    timezone for consistent datetime handling across the application.

    Args:
        dbapi_connection: The raw database connection
        connection_record: Connection pool record
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("SET TIME ZONE 'UTC'")
    cursor.close()


@event.listens_for(Engine, "connect")
def set_search_path(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    """
    Set the schema search path for all database connections.

    This event listener configures the schema search path to ensure
    proper schema resolution for database operations.

    Args:
        dbapi_connection: The raw database connection
        connection_record: Connection pool record
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("SET search_path TO public")
    cursor.close()


def get_engine() -> Engine:
    """
    Get the configured database engine instance.

    This function provides access to the database engine with all
    connection pooling and configuration settings properly applied.

    Returns:
        Engine: Configured SQLAlchemy engine instance
    """
    return engine


def create_session() -> Session:
    """
    Create a new database session.

    This function creates a new session using the configured session
    factory. It should be used when explicit session creation is needed
    outside of the dependency injection system.

    Returns:
        Session: New database session instance
    """
    return SessionLocal()


def verify_database_connection() -> bool:
    """
    Verify that the database connection is working.

    This function attempts to establish a database connection and
    execute a simple query to verify database accessibility.

    Returns:
        bool: True if connection is successful, False otherwise

    Raises:
        SQLAlchemyError: If database connection fails
    """
    try:
        with create_session() as session:
            session.execute("SELECT 1")
        return True
    except Exception as e:
        # Add specific exception handling

        if isinstance(e, SQLAlchemyError):
            return False
        raise


def init_database() -> None:
    """
    Initialize the database with required tables and initial data.

    This function creates all database tables based on the defined models
    and performs any necessary initialization steps. It should be called
    during application startup.
    """
    Base.metadata.create_all(bind=engine)
