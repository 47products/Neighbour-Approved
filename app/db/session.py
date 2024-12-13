"""
This module provides a dependency that provides a database session and ensures 
its closure after use.

Functions:
    get_db: Dependency that provides a database session and ensures its closure after use.

Dependencies:
    - Generator: Generator type hint from the typing module.
    - SessionLocal: Database session from the app.db.database module.

Classes:
    - None

Exceptions:
    - None

Constants:
    - None

Resources:
    - https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-dependency
"""

from typing import Generator
from app.db.database import SessionLocal


def get_db() -> Generator:
    """
    Dependency that provides a database session and ensures its closure after use.

    Yields:
        SessionLocal: An instance of the database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
