"""
Contact Queries Module.

This module provides the `ContactQueriesMixin` class which encapsulates
query-related operations for the Contact repository. It includes methods to:
    - Retrieve a contact by email.
    - Retrieve a contact with all relationships.
    - Retrieve contacts by user.
    - Search contacts based on various filters.

Usage Example:
    from app.db.repositories.contact_repository.queries import ContactQueriesMixin

    class MyRepository(ContactQueriesMixin, BaseRepository):
        pass

Dependencies:
    - SQLAlchemy (for query execution)
    - app.db.models.contact_model.Contact (Contact model)
    - app.db.errors.QueryError (Custom error for query failures)
"""

from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.contact_model import Contact
from app.db.errors import QueryError


class ContactQueriesMixin:
    """
    Mixin class for contact query operations.

    Provides methods to fetch contact records using various criteria,
    including email lookup, relationship loading, filtering by user,
    and searching with multiple filters.
    """

    async def get_by_email(self, email: str) -> Optional[Contact]:
        """
        Retrieve a contact by its email address.

        Args:
            email (str): The email address of the contact.

        Returns:
            Optional[Contact]: The contact if found, otherwise None.

        Raises:
            QueryError: If the database query fails.
        """
        try:
            query = select(self._model).where(self._model.email == email)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.error("get_by_email_failed", email=email, error=str(e))
            raise QueryError(
                message="Failed to retrieve contact by email",
                details={"email": email, "error": str(e)},
            ) from e

    async def get_with_relationships(self, contact_id: int) -> Optional[Contact]:
        """
        Retrieve a contact with all associated relationships loaded.

        Args:
            contact_id (int): The unique identifier of the contact.

        Returns:
            Optional[Contact]: The contact with relationships if found, otherwise None.

        Raises:
            QueryError: If the database query fails.
        """
        try:
            query = (
                select(self._model)
                .where(self._model.id == contact_id)
                .options(
                    selectinload(self._model.services),
                    selectinload(self._model.categories),
                    selectinload(self._model.endorsements),
                    selectinload(self._model.communities),
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.error(
                "get_with_relationships_failed", contact_id=contact_id, error=str(e)
            )
            raise QueryError(
                message="Failed to retrieve contact with relationships",
                details={"contact_id": contact_id, "error": str(e)},
            ) from e

    async def get_by_user(self, user_id: int) -> List[Contact]:
        """
        Retrieve all contacts associated with a specific user.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            List[Contact]: A list of contacts belonging to the user.

        Raises:
            QueryError: If the database query fails.
        """
        try:
            query = (
                select(self._model)
                .where(self._model.user_id == user_id)
                .order_by(self._model.contact_name)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error("get_by_user_failed", user_id=user_id, error=str(e))
            raise QueryError(
                message="Failed to retrieve user contacts",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def search_contacts(
        self,
        search_term: str,
        *,
        category_id: Optional[int] = None,
        service_id: Optional[int] = None,
        community_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Contact]:
        """
        Search for contacts based on a search term and optional filters.

        This method searches the contact name as well as the primary contact's
        first and last names. It supports additional filters for category,
        service, and community, along with pagination support.

        Args:
            search_term (str): The term to search for.
            category_id (Optional[int]): Filter by category ID if provided.
            service_id (Optional[int]): Filter by service ID if provided.
            community_id (Optional[int]): Filter by community ID if provided.
            skip (int): Number of records to skip (for pagination).
            limit (int): Maximum number of records to return.
            active_only (bool): If True, only include active contacts.

        Returns:
            List[Contact]: A list of contacts matching the search criteria.

        Raises:
            QueryError: If the database query fails.
        """
        try:
            conditions = [
                or_(
                    self._model.contact_name.ilike(f"%{search_term}%"),
                    self._model.primary_contact_first_name.ilike(f"%{search_term}%"),
                    self._model.primary_contact_last_name.ilike(f"%{search_term}%"),
                )
            ]
            # Include filter to return only active contacts if required.
            if active_only:
                conditions.append(self._model.is_active.is_(True))
            if category_id:
                conditions.append(self._model.categories.any(id=category_id))
            if service_id:
                conditions.append(self._model.services.any(id=service_id))
            if community_id:
                conditions.append(self._model.communities.any(id=community_id))

            query = (
                select(self._model)
                .where(and_(*conditions))
                .offset(skip)
                .limit(limit)
                .order_by(self._model.contact_name)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error(
                "search_contacts_failed", search_term=search_term, error=str(e)
            )
            raise QueryError(
                message="Failed to search contacts",
                details={"search_term": search_term, "error": str(e)},
            ) from e
