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

from app.db.repositories.repository_interface import IRepository
from app.db.database_configuration import Base
from app.core.error_handling import DatabaseError, RecordNotFoundError

ModelType = TypeVar("ModelType")
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
        self._logger = logger.bind(repository=model.__name__, repository_id=id(self))

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
            self._logger.info(
                "creating_record",
                model=self._model.__name__,
                data=schema.model_dump(
                    exclude={"password"} if hasattr(schema, "password") else None
                ),
            )

            db_obj = self._model(**schema.model_dump())
            self._db.add(db_obj)
            await self._db.flush()
            await self._db.refresh(db_obj)
            await self._db.commit()

            self._logger.info(
                "record_created", model=self._model.__name__, model_id=db_obj.id
            )
            return db_obj

        except IntegrityError as e:
            await self._db.rollback()
            self._logger.error(
                "creation_failed_integrity",
                model=self._model.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resource already exists",
            ) from e

        except SQLAlchemyError as e:
            await self._db.rollback()
            self._logger.error(
                "creation_failed",
                model=self._model.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create record",
            ) from e

    async def get(self, id: Any) -> Optional[ModelType]:
        """
        Retrieve a record by its identifier.

        Args:
            id: Record identifier

        Returns:
            Model instance if found, None otherwise
        """
        try:
            self._logger.debug(
                "fetching_record", model=self._model.__name__, model_id=id
            )

            query = select(self._model).where(self._model.id == id)
            result = await self._db.execute(query)
            record = result.scalar_one_or_none()

            if record:
                self._logger.debug(
                    "record_found", model=self._model.__name__, model_id=id
                )
            else:
                self._logger.debug(
                    "record_not_found", model=self._model.__name__, model_id=id
                )

            return record

        except SQLAlchemyError as e:
            self._logger.error(
                "fetch_failed",
                model=self._model.__name__,
                model_id=id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DatabaseError(f"Error fetching {self._model.__name__}") from e

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        Retrieve multiple records with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filtering criteria

        Returns:
            List of model instances
        """
        try:
            self._logger.debug(
                "fetching_multiple_records",
                model=self._model.__name__,
                skip=skip,
                limit=limit,
                filters=filters,
            )

            query = select(self._model)
            if filters:
                query = query.filter_by(**filters)
            query = query.offset(skip).limit(limit)

            result = await self._db.execute(query)
            records = result.scalars().all()

            self._logger.debug(
                "multiple_records_fetched",
                model=self._model.__name__,
                record_count=len(records),
            )
            return records

        except SQLAlchemyError as e:
            self._logger.error(
                "fetch_multiple_failed",
                model=self._model.__name__,
                error=str(e),
                error_type=type(e).__name__,
                skip=skip,
                limit=limit,
                filters=filters,
            )
            raise DatabaseError(
                f"Error fetching multiple {self._model.__name__}"
            ) from e

    async def update(self, *, id: Any, schema: UpdateSchemaType) -> Optional[ModelType]:
        """
        Update an existing record.

        Args:
            id: Record identifier
            schema: Update data

        Returns:
            Updated model instance

        Raises:
            RecordNotFoundError: If record not found
        """
        try:
            self._logger.info(
                "updating_record",
                model=self._model.__name__,
                model_id=id,
                update_data=schema.model_dump(exclude_unset=True),
            )

            record = await self.get(id)
            if not record:
                raise RecordNotFoundError(f"{self._model.__name__} not found")

            update_data = schema.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(record, field, value)

            await self._db.commit()
            await self._db.refresh(record)

            self._logger.info("record_updated", model=self._model.__name__, model_id=id)
            return record

        except SQLAlchemyError as e:
            await self._db.rollback()
            self._logger.error(
                "update_failed",
                model=self._model.__name__,
                model_id=id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DatabaseError(f"Error updating {self._model.__name__}") from e

    async def delete(self, id: Any) -> bool:
        """
        Delete a record.

        Args:
            id: Record identifier

        Returns:
            True if record was deleted, False otherwise
        """
        try:
            self._logger.info(
                "deleting_record", model=self._model.__name__, model_id=id
            )

            query = delete(self._model).where(self._model.id == id)
            result = await self._db.execute(query)
            await self._db.commit()

            success = result.rowcount > 0
            self._logger.info(
                "record_deleted" if success else "record_not_found",
                model=self._model.__name__,
                model_id=id,
                success=success,
            )
            return success

        except SQLAlchemyError as e:
            await self._db.rollback()
            self._logger.error(
                "deletion_failed",
                model=self._model.__name__,
                model_id=id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DatabaseError(f"Error deleting {self._model.__name__}") from e

    async def exists(self, id: Any) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record identifier

        Returns:
            True if record exists, False otherwise
        """
        self._logger.debug(
            "checking_record_existence", model=self._model.__name__, model_id=id
        )

        query = (
            select(func.count()).select_from(self._model).where(self._model.id == id)
        )
        result = await self._db.execute(query)
        exists = bool(result.scalar())

        self._logger.debug(
            "record_existence_checked",
            model=self._model.__name__,
            model_id=id,
            exists=exists,
        )
        return exists

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching optional filters.

        Args:
            filters: Optional filtering criteria

        Returns:
            Number of matching records
        """
        try:
            self._logger.debug(
                "counting_records", model=self._model.__name__, filters=filters
            )

            query = select(func.count()).select_from(self._model)
            if filters:
                query = query.filter_by(**filters)

            result = await self._db.execute(query)
            count = result.scalar()

            self._logger.debug(
                "records_counted",
                model=self._model.__name__,
                count=count,
                filters=filters,
            )
            return count

        except SQLAlchemyError as e:
            self._logger.error(
                "count_failed",
                model=self._model.__name__,
                error=str(e),
                error_type=type(e).__name__,
                filters=filters,
            )
            raise DatabaseError(f"Error counting {self._model.__name__}") from e

    def filter_by(self, **kwargs: Any) -> List[ModelType]:
        """
        Retrieve records matching exact criteria.

        Args:
            **kwargs: Filter conditions as keyword arguments

        Returns:
            List of matching model instances
        """
        self._logger.debug(
            "filtering_records", model=self._model.__name__, filters=kwargs
        )

        try:
            records = self._db.query(self._model).filter_by(**kwargs).all()

            self._logger.debug(
                "records_filtered",
                model=self._model.__name__,
                record_count=len(records),
                filters=kwargs,
            )
            return records

        except SQLAlchemyError as e:
            self._logger.error(
                "filter_failed",
                model=self._model.__name__,
                error=str(e),
                error_type=type(e).__name__,
                filters=kwargs,
            )
            raise DatabaseError(f"Error filtering {self._model.__name__}") from e
