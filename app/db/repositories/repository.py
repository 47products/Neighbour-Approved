"""
Repository implementation module.

This module provides the concrete implementation of the repository interface,
implementing all required database operations. It serves as the base class
for all specific repository implementations in the application.
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from fastapi import HTTPException, status
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
import structlog

from app.db.repositories.base import IRepository
from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = structlog.get_logger()


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository implementation with common database operations.

    This class implements the IRepository interface, providing concrete implementations
    of all required database operations. It serves as the foundation for all
    model-specific repositories.

    Type Parameters:
        ModelType: The SQLAlchemy model type
        CreateSchemaType: Pydantic model type for creation operations
        UpdateSchemaType: Pydantic model type for update operations
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize the repository.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self._model = model
        self._db = db
        self._logger = logger.bind(repository=model.__name__)

    @property
    def db(self) -> Session:
        """Get the current database session."""
        return self._db

    async def create(self, schema: CreateSchemaType) -> ModelType:
        """
        Create a new record in the database.

        Args:
            schema: Validated data for creating a new record

        Returns:
            The created model instance

        Raises:
            HTTPException: If creation fails
        """
        try:
            db_obj = self._model(**schema.model_dump())
            self._db.add(db_obj)
            await self._db.flush()
            await self._db.refresh(db_obj)
            await self._db.commit()

            self._logger.info("created_record", model_id=db_obj.id)
            return db_obj

        except IntegrityError as e:
            await self._db.rollback()
            self._logger.error("creation_failed_integrity", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resource already exists",
            ) from e

        except SQLAlchemyError as e:
            await self._db.rollback()
            self._logger.error("creation_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create record",
            ) from e
