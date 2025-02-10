"""
Repository interface module defining core database operations.

This module establishes the base protocol for all repository implementations in the
application. It defines the standard set of operations that must be supported for
database access, ensuring consistency across different model repositories.

The interface uses Python's typing system to enforce type safety and provide
better IDE support and code documentation.
"""

from typing import Protocol, Optional, List, Any, Dict
from sqlalchemy.orm import Session

# Removed module-level type variable declarations.
# Instead, we declare generic type parameters inline in the class definition.


class IRepository[ModelType, CreateSchemaType, UpdateSchemaType](Protocol):
    """
    Base repository interface defining standard database operations.

    This interface establishes the contract that all repository implementations
    must follow, ensuring consistent data access patterns across the application.

    Type Parameters:
        ModelType: The SQLAlchemy model type
        CreateSchemaType: Pydantic model type for creation operations
        UpdateSchemaType: Pydantic model type for update operations
    """

    @property
    def db(self) -> Session:
        """Get the current database session."""
        ...

    async def create(self, schema: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            schema: Validated data for creating a new record

        Returns:
            The created model instance
        """
        ...

    async def get(self, id: Any) -> Optional[ModelType]:
        """
        Retrieve a record by its identifier.

        Args:
            id: The record identifier

        Returns:
            The model instance if found, None otherwise
        """
        ...

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        Retrieve multiple records with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filtering criteria

        Returns:
            List of model instances
        """
        ...

    async def update(self, *, id: Any, schema: UpdateSchemaType) -> Optional[ModelType]:
        """
        Update an existing record.

        Args:
            id: The record identifier
            schema: Validated data for updating the record

        Returns:
            The updated model instance
        """
        ...

    async def delete(self, id: Any) -> bool:
        """
        Delete a record.

        Args:
            id: The record identifier

        Returns:
            True if the record was deleted, False otherwise
        """
        ...

    async def exists(self, id: Any) -> bool:
        """
        Check if a record exists.

        Args:
            id: The record identifier

        Returns:
            True if the record exists, False otherwise
        """
        ...

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count the number of records matching optional filters.

        Args:
            filters: Optional filtering criteria

        Returns:
            The number of matching records
        """
        ...

    def filter_by(self, **kwargs) -> List[ModelType]:
        """
        Retrieve records matching exact criteria.

        Args:
            **kwargs: Filter conditions as keyword arguments

        Returns:
            List of matching model instances
        """
        ...

    async def bulk_create(self, schemas: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple records in a single operation.

        Args:
            schemas: List of creation schemas

        Returns:
            List of created model instances
        """
        ...

    async def bulk_update(
        self, ids: List[Any], schema: UpdateSchemaType
    ) -> List[ModelType]:
        """
        Update multiple records in a single operation.

        Args:
            ids: List of record identifiers
            schema: Update schema to apply to all records

        Returns:
            List of updated model instances
        """
        ...

    async def bulk_delete(self, ids: List[Any]) -> int:
        """
        Delete multiple records in a single operation.

        Args:
            ids: List of record identifiers

        Returns:
            Number of records deleted
        """
        ...
