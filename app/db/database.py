"""
This file contains the database configuration and session creation.

The `create_engine` function from the `sqlalchemy` module is used to create a new 
database engine. The `engine` object is used to connect to the database and 
execute SQL queries.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.db.config import Settings

settings = Settings()

DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine = create_engine(settings.DATABASE_URL, echo=True)  # echo=True for SQL logging

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
