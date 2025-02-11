"""
Base service layer module for Neighbour Approved application.

This module provides the core service layer abstractions and base implementations,
establishing a clear separation between business logic and data access. It defines
the contract that all service implementations must follow and provides common
functionality through base classes.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Type
import structlog
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.error_handling import BaseAppException, BusinessLogicError
from app.db.repositories.repository_interface import IRepository
from app.services.service_exceptions import ResourceNotFoundError

logger = structlog.get_logger(__name__)


class ServiceException(BaseAppException):
    """Base exception for service-related errors."""

    def __init__(
        self,
        message: str = "Service operation failed",
        error_code: str = "SERVICE_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the service exception.

        Args:
            message: Error message
            error_code: Error code for client
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message, error_code, status_code, details)


class ValidationException(ServiceException):
    """Exception for validation errors in services."""

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation exception.

        Args:
            message: Validation error message
            details: Additional validation details
        """
        super().__init__(
            message,
            "VALIDATION_ERROR",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            details,
        )


# Inline generic type parameters are declared directly after the class name.
class IService[ModelType, CreateSchemaType, UpdateSchemaType](Protocol):
    """Base service interface defining standard operations.

    This interface establishes the contract that all service implementations
    must follow, ensuring consistent business logic handling across the application.
    """

    @property
    @abstractmethod
    def repository(self) -> IRepository:
        """Get the underlying repository instance."""
        ...

    @abstractmethod
    async def create(self, data: CreateSchemaType) -> ModelType:
        """Create a new record with business logic validation.

        Args:
            data: Validated creation data

        Returns:
            Created model instance

        Raises:
            ValidationException: If business rules are violated
            ServiceException: If service operation fails
        """
        ...

    @abstractmethod
    async def get(self, id: Any) -> Optional[ModelType]:
        """Retrieve a record by ID with additional business logic.

        Args:
            id: Record identifier

        Returns:
            Model instance if found and accessible

        Raises:
            ServiceException: If service operation fails
        """
        ...

    @abstractmethod
    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """Retrieve multiple records with business rules applied.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filtering criteria

        Returns:
            List of accessible model instances

        Raises:
            ServiceException: If service operation fails
        """
        ...

    @abstractmethod
    async def update(self, *, id: Any, data: UpdateSchemaType) -> Optional[ModelType]:
        """Update a record with business logic validation.

        Args:
            id: Record identifier
            data: Update data

        Returns:
            Updated model instance

        Raises:
            ValidationException: If business rules are violated
            ServiceException: If service operation fails
        """
        ...

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete a record with business logic checks.

        Args:
            id: Record identifier

        Returns:
            True if record was deleted

        Raises:
            ValidationException: If deletion is not allowed
            ServiceException: If service operation fails
        """
        ...


class BaseService[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]:
    """Base service implementation with common functionality.

    This class provides a foundation for all service implementations,
    handling common operations while allowing for specific business logic
    in derived classes.

    Type Parameters:
        ModelType: The SQLAlchemy model type
        CreateSchemaType: Pydantic model for creation
        UpdateSchemaType: Pydantic model for updates
        RepositoryType: Repository implementation type
    """

    def __init__(
        self,
        model: Type[ModelType],
        repository: RepositoryType,
        logger_name: Optional[str] = None,
    ):
        """Initialize the service.

        Args:
            model: SQLAlchemy model class
            repository: Repository instance
            logger_name: Optional custom logger name
        """
        self._model = model
        self._repository = repository
        self._logger = logger.bind(
            service=logger_name or model.__name__,
            service_id=id(self),
        )

    @property
    def repository(self) -> RepositoryType:
        """Get the underlying repository instance."""
        return self._repository

    @property
    def db(self) -> Session:
        """Get the current database session."""
        return self._repository.db

    async def create(self, data: CreateSchemaType) -> ModelType:
        """Create a new record with validation.

        Args:
            data: Creation data

        Returns:
            Created model instance

        Raises:
            ValidationException: If validation fails
            ServiceException: If creation fails
        """
        try:
            # Perform business rule validation
            await self.validate_create(data)

            # Perform any pre-create processing
            processed_data = await self.pre_create(data)

            # Create the record
            self._logger.info(
                "creating_record",
                model=self._model.__name__,
                data=processed_data.model_dump(
                    exclude=(
                        {"password"} if hasattr(processed_data, "password") else None
                    )
                ),
            )
            record = await self._repository.create(processed_data)

            # Perform any post-create processing
            await self.post_create(record)

            self._logger.info(
                "record_created",
                model=self._model.__name__,
                record_id=getattr(record, "id", None),
            )
            return record

        except BusinessLogicError as e:
            self._logger.error(
                "creation_failed_validation",
                model=self._model.__name__,
                error=str(e),
            )
            raise ValidationException(str(e)) from e

        except Exception as e:
            self._logger.error(
                "creation_failed",
                model=self._model.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ServiceException(f"Failed to create {self._model.__name__}") from e

    async def validate_create(self, data: CreateSchemaType) -> None:
        """Validate creation data against business rules.

        Args:
            data: Data to validate

        Raises:
            BusinessLogicError: If validation fails
        """
        # Override in derived classes to implement specific validation

    async def pre_create(self, data: CreateSchemaType) -> CreateSchemaType:
        """Process data before creation.

        Args:
            data: Data to process

        Returns:
            Processed data
        """
        # Override in derived classes to implement pre-creation processing
        return data

    async def post_create(self, record: ModelType) -> None:
        """Process record after creation.

        Args:
            record: Created record
        """
        # Override in derived classes to implement post-creation processing

    async def get(self, id: Any) -> Optional[ModelType]:
        """Retrieve a record by ID.

        Args:
            id: Record identifier

        Returns:
            Model instance if found and accessible

        Raises:
            ServiceException: If retrieval fails
        """
        try:
            record = await self._repository.get(id)
            if record:
                await self.check_access(record)
            return record
        except ResourceNotFoundError:  # Allow it to propagate
            raise
        except HTTPException:
            raise
        except Exception as e:
            self._logger.error(
                "retrieval_failed",
                model=self._model.__name__,
                id=id,
                error=str(e),
            )
            raise ServiceException(f"Failed to retrieve {self._model.__name__}") from e

    async def check_access(self, record: ModelType) -> None:
        """Check if current context has access to record.

        Args:
            record: Record to check

        Raises:
            HTTPException: If access is denied
        """
        # Override in derived classes to implement access control

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """Retrieve multiple records.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filtering criteria

        Returns:
            List of accessible model instances

        Raises:
            ServiceException: If retrieval fails
        """
        try:
            # Apply business logic to filters
            processed_filters = await self.process_filters(filters or {})

            records = await self._repository.get_multi(
                skip=skip,
                limit=limit,
                filters=processed_filters,
            )

            # Filter based on access control
            return [r for r in records if await self.can_access(r)]

        except Exception as e:
            self._logger.error(
                "multi_retrieval_failed",
                model=self._model.__name__,
                error=str(e),
                filters=filters,
            )
            raise ServiceException(
                f"Failed to retrieve multiple {self._model.__name__}"
            ) from e

    async def process_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate filter criteria.

        Args:
            filters: Raw filter criteria

        Returns:
            Processed filter criteria
        """
        # Override in derived classes to implement filter processing
        return filters

    async def can_access(self, record: ModelType) -> bool:
        """Check if record can be accessed in current context.

        Args:
            record: Record to check

        Returns:
            Whether record is accessible
        """
        # Override in derived classes to implement access control
        return True

    async def update(self, *, id: Any, data: UpdateSchemaType) -> Optional[ModelType]:
        """Update a record.

        Args:
            id: Record identifier
            data: Update data

        Returns:
            Updated model instance

        Raises:
            ValidationException: If validation fails
            ServiceException: If update fails
        """
        try:
            # Validate update data
            await self.validate_update(id, data)

            # Process update data
            processed_data = await self.pre_update(id, data)

            # Perform update
            record = await self._repository.update(id=id, schema=processed_data)

            if record:
                # Post-update processing
                await self.post_update(record)

            return record

        except BusinessLogicError as e:
            self._logger.error(
                "update_failed_validation",
                model=self._model.__name__,
                id=id,
                error=str(e),
            )
            raise ValidationException(str(e)) from e

        except Exception as e:
            self._logger.error(
                "update_failed",
                model=self._model.__name__,
                id=id,
                error=str(e),
            )
            raise ServiceException(f"Failed to update {self._model.__name__}") from e

    async def validate_update(self, id: Any, data: UpdateSchemaType) -> None:
        """Validate update data against business rules.

        Args:
            id: Record identifier
            data: Data to validate

        Raises:
            BusinessLogicError: If validation fails
        """
        # Override in derived classes to implement validation

    async def pre_update(self, _, data: UpdateSchemaType) -> UpdateSchemaType:
        """Process data before update.

        Args:
            id: Record identifier
            data: Data to process

        Returns:
            Processed data
        """
        # Override in derived classes to implement pre-update processing
        return data

    async def post_update(self, record: ModelType) -> None:
        """Process record after update.

        Args:
            record: Updated record
        """
        # Override in derived classes to implement post-update processing

    async def delete(self, id: Any) -> bool:
        """Delete a record.

        Args:
            id: Record identifier

        Returns:
            True if record was deleted

        Raises:
            ValidationException: If deletion is not allowed
            ServiceException: If deletion fails
        """
        try:
            # Check if deletion is allowed
            await self.validate_delete(id)

            # Perform any pre-delete processing
            await self.pre_delete(id)

            # Delete the record
            result = await self._repository.delete(id)

            if result:
                # Perform any post-delete processing
                await self.post_delete(id)

            return result

        except BusinessLogicError as e:
            self._logger.error(
                "deletion_failed_validation",
                model=self._model.__name__,
                id=id,
                error=str(e),
            )
            raise ValidationException(str(e)) from e

        except ResourceNotFoundError:
            raise  # Allow the test to catch it
        except Exception as e:
            self._logger.error(
                "deletion_failed",
                model=self._model.__name__,
                id=id,
                error=str(e),
            )
            raise ServiceException(f"Failed to delete {self._model.__name__}") from e

    async def validate_delete(self, id: Any) -> None:
        """Validate if record can be deleted.

        Args:
            id: Record identifier

        Raises:
            BusinessLogicError: If deletion is not allowed
        """
        # Override in derived classes to implement deletion validation

    async def pre_delete(self, id: Any) -> None:
        """Process before deletion.

        Args:
            id: Record identifier
        """
        # Override in derived classes to implement pre-deletion processing

    async def post_delete(self, id: Any) -> None:
        """Process after deletion.

        Args:
            id: Record identifier
        """
        # Override in derived classes to implement post-deletion processing
