"""
Repository implementation module.

This module provides the concrete implementation of the repository interface,
implementing all required database operations. It serves as the base class
for all specific repository implementations in the application.

The repository layer is responsible for:
- Database operations
- Data access patterns
- Query execution
- Connection management
"""

from typing import Type, Optional, List, Any, Dict
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
import structlog

from app.db.errors import (
    QueryError,
    IntegrityError as RepositoryIntegrityError,
    TransactionError,
)
from app.db.repositories.repository_interface import IRepository
from app.db.database_engine import Base
from app.core.error_handling import (
    DatabaseError,
    RecordNotFoundError,
    DuplicateRecordError,
)

logger = structlog.get_logger()


class BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]:
    """
    Base repository implementation with common database operations.

    This class implements the IRepository interface, providing concrete implementations
    of all required database operations. It serves as the foundation for all
    model-specific repositories.

    Attributes:
        _model: SQLAlchemy model class
        _db: Database session
        _logger: Structured logger instance

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
            RepositoryIntegrityError: If unique constraint is violated
            QueryError: If database query fails
            TransactionError: If transaction fails
        """
        try:
            self._logger.debug("db_create_start", model=self._model.__name__)

            db_obj = self._model(**schema.model_dump())
            self._db.add(db_obj)
            await self._db.flush()
            await self._db.refresh(db_obj)
            await self._db.commit()

            self._logger.debug(
                "db_create_success",
                model=self._model.__name__,
                record_id=getattr(db_obj, "id", None),
            )
            return db_obj

        except IntegrityError as e:
            await self._db.rollback()
            self._logger.error("db_create_integrity_error", error=str(e))
            raise RepositoryIntegrityError(
                details={"model": self._model.__name__, "error": str(e)}
            ) from e

        except SQLAlchemyError as e:
            await self._db.rollback()
            self._logger.error("db_create_error", error=str(e))
            raise TransactionError(
                message="Failed to create database record",
                details={"model": self._model.__name__, "error": str(e)},
            ) from e

    async def get(self, id: Any) -> Optional[ModelType]:
        """
        Retrieve a record by its identifier.

        Args:
            id: Record identifier

        Returns:
            Model instance if found, None otherwise

        Raises:
            QueryError: If database query fails
        """
        try:
            self._logger.debug("db_get_start", model_id=id)

            query = select(self._model).where(self._model.id == id)
            result = await self._db.execute(query)
            record = result.scalar_one_or_none()

            self._logger.debug("db_get_success", model_id=id, found=bool(record))
            return record

        except SQLAlchemyError as e:
            self._logger.error("db_get_error", error=str(e))
            raise QueryError(
                message="Failed to retrieve database record",
                details={"model": self._model.__name__, "id": id, "error": str(e)},
            ) from e

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

        Raises:
            QueryError: If database query fails
        """
        try:
            self._logger.debug(
                "db_get_multi_start", skip=skip, limit=limit, filters=filters
            )

            query = select(self._model)
            if filters:
                query = query.filter_by(**filters)
            query = query.offset(skip).limit(limit)

            result = await self._db.execute(query)
            records = result.scalars().all()

            self._logger.debug("db_get_multi_success", record_count=len(records))
            return records

        except SQLAlchemyError as e:
            self._logger.error("db_get_multi_error", error=str(e))
            raise QueryError(
                message="Failed to retrieve multiple database records",
                details={
                    "model": self._model.__name__,
                    "skip": skip,
                    "limit": limit,
                    "filters": filters,
                    "error": str(e),
                },
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
            RepositoryIntegrityError: If update violates constraints
            TransactionError: If transaction fails
        """
        try:
            self._logger.debug("db_update_start", record_id=id)

            record = await self.get(id)
            if not record:
                raise RecordNotFoundError(
                    details={"model": self._model.__name__, "id": id}
                )

            update_data = schema.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(record, field, value)

            await self._db.commit()
            await self._db.refresh(record)

            self._logger.debug("db_update_success", record_id=id)
            return record

        except IntegrityError as e:
            await self._db.rollback()
            self._logger.error("db_update_integrity_error", error=str(e))
            raise RepositoryIntegrityError(
                details={"model": self._model.__name__, "id": id, "error": str(e)}
            ) from e

        except SQLAlchemyError as e:
            await self._db.rollback()
            self._logger.error("db_update_error", error=str(e))
            raise TransactionError(
                message="Failed to update database record",
                details={"model": self._model.__name__, "id": id, "error": str(e)},
            ) from e

    async def delete(self, id: Any) -> bool:
        """
        Delete a record.

        Args:
            id: Record identifier

        Returns:
            True if record was deleted, False if not found

        Raises:
            TransactionError: If deletion fails
        """
        try:
            self._logger.debug("db_delete_start", record_id=id)

            query = delete(self._model).where(self._model.id == id)
            result = await self._db.execute(query)
            await self._db.commit()

            success = result.rowcount > 0
            self._logger.debug("db_delete_success", record_id=id, deleted=success)
            return success

        except SQLAlchemyError as e:
            await self._db.rollback()
            self._logger.error("db_delete_error", error=str(e))
            raise TransactionError(
                message="Failed to delete database record",
                details={"model": self._model.__name__, "id": id, "error": str(e)},
            ) from e

    async def exists(self, id: Any) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record identifier

        Returns:
            True if record exists, False otherwise

        Raises:
            QueryError: If database query fails
        """
        try:
            self._logger.debug("db_exists_check_start", record_id=id)

            query = (
                select(func.count())
                .select_from(self._model)
                .where(self._model.id == id)
            )
            result = await self._db.execute(query)
            exists = bool(result.scalar())

            self._logger.debug("db_exists_check_success", record_id=id, exists=exists)
            return exists

        except SQLAlchemyError as e:
            self._logger.error("db_exists_check_error", error=str(e))
            raise QueryError(
                message="Failed to check record existence",
                details={"model": self._model.__name__, "id": id, "error": str(e)},
            ) from e

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching optional filters.

        Args:
            filters: Optional filtering criteria

        Returns:
            Number of matching records

        Raises:
            QueryError: If database query fails
        """
        try:
            self._logger.debug("db_count_start", filters=filters)

            query = select(func.count()).select_from(self._model)
            if filters:
                query = query.filter_by(**filters)

            result = await self._db.execute(query)
            count = result.scalar()

            self._logger.debug("db_count_success", count=count)
            return count

        except SQLAlchemyError as e:
            self._logger.error("db_count_error", error=str(e))
            raise QueryError(
                message="Failed to count database records",
                details={
                    "model": self._model.__name__,
                    "filters": filters,
                    "error": str(e),
                },
            ) from e

    async def filter_by(self, **kwargs: Any) -> List[ModelType]:
        """
        Retrieve records matching exact criteria.

        Args:
            **kwargs: Filter conditions as keyword arguments

        Returns:
            List of matching model instances

        Raises:
            QueryError: If database query fails
        """
        try:
            self._logger.debug("db_filter_start", filters=kwargs)

            query = select(self._model).filter_by(**kwargs)
            result = await self._db.execute(query)
            records = result.scalars().all()

            self._logger.debug("db_filter_success", record_count=len(records))
            return records

        except SQLAlchemyError as e:
            self._logger.error("db_filter_error", error=str(e))
            raise QueryError(
                message="Failed to filter database records",
                details={
                    "model": self._model.__name__,
                    "filters": kwargs,
                    "error": str(e),
                },
            ) from e
