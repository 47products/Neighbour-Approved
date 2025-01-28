"""
Contact Repository Module.

This module implements the Contact repository pattern, providing a centralized
location for all contact-related database operations. It focuses purely on data
access operations, leaving business logic to the service layer.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.repository_implementation import BaseRepository
from app.db.models.contact_model import Contact
from app.db.models.service_model import Service
from app.db.models.category_model import Category
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.api.v1.schemas.contact_schema import ContactCreate, ContactUpdate
from app.db.errors import (
    QueryError,
    IntegrityError,
    ValidationError,
)


class ContactRepository(BaseRepository[Contact, ContactCreate, ContactUpdate]):
    """
    Repository for contact data access operations.

    This repository handles all database operations related to contact entities,
    implementing a clean separation between data access and business logic.

    Attributes:
        _model: The Contact model class
        _db: The database session
        _logger: Structured logger instance
    """

    def __init__(self, db: Session):
        """
        Initialize contact repository.

        Args:
            db: Database session for operations
        """
        super().__init__(Contact, db)

    async def get_by_email(self, email: str) -> Optional[Contact]:
        """
        Retrieve a contact by email address.

        Args:
            email: Contact's email address

        Returns:
            Optional[Contact]: Contact if found, None otherwise

        Raises:
            QueryError: If database query fails
        """
        try:
            query = select(self._model).where(self._model.email == email)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            self._logger.error(
                "get_by_email_failed",
                email=email,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve contact by email",
                details={"email": email, "error": str(e)},
            ) from e

    async def get_with_relationships(self, contact_id: int) -> Optional[Contact]:
        """
        Retrieve a contact with all relationships loaded.

        Args:
            contact_id: Contact ID

        Returns:
            Optional[Contact]: Contact with loaded relationships if found

        Raises:
            QueryError: If database query fails
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
                "get_with_relationships_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve contact with relationships",
                details={"contact_id": contact_id, "error": str(e)},
            ) from e

    async def get_by_user(self, user_id: int) -> List[Contact]:
        """
        Get all contacts owned by a user.

        Args:
            user_id: User ID

        Returns:
            List[Contact]: List of user's contacts

        Raises:
            QueryError: If database query fails
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
            self._logger.error(
                "get_by_user_failed",
                user_id=user_id,
                error=str(e),
            )
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
        Search contacts with optional filtering.

        Args:
            search_term: Search term
            category_id: Optional category filter
            service_id: Optional service filter
            community_id: Optional community filter
            skip: Number of records to skip
            limit: Maximum records to return
            active_only: Whether to include only active contacts

        Returns:
            List[Contact]: List of matching contacts

        Raises:
            QueryError: If database query fails
        """
        try:
            conditions = [
                or_(
                    self._model.contact_name.ilike(f"%{search_term}%"),
                    self._model.primary_contact_first_name.ilike(f"%{search_term}%"),
                    self._model.primary_contact_last_name.ilike(f"%{search_term}%"),
                )
            ]

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
                "search_contacts_failed",
                search_term=search_term,
                error=str(e),
            )
            raise QueryError(
                message="Failed to search contacts",
                details={"search_term": search_term, "error": str(e)},
            ) from e

    async def add_service(self, contact_id: int, service_id: int) -> bool:
        """
        Add a service to a contact's offerings.

        Args:
            contact_id: Contact ID
            service_id: Service ID

        Returns:
            bool: Whether service was added

        Raises:
            IntegrityError: If operation fails
        """
        try:
            contact = await self.get(contact_id)
            service = await self.db.get(Service, service_id)

            if not contact or not service:
                return False

            if service not in contact.services:
                contact.services.append(service)
                await self.db.commit()
                return True

            return False

        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "add_service_failed",
                contact_id=contact_id,
                service_id=service_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to add service to contact",
                details={
                    "contact_id": contact_id,
                    "service_id": service_id,
                    "error": str(e),
                },
            ) from e

    async def remove_service(self, contact_id: int, service_id: int) -> bool:
        """
        Remove a service from a contact's offerings.

        Args:
            contact_id: Contact ID
            service_id: Service ID

        Returns:
            bool: Whether service was removed

        Raises:
            IntegrityError: If operation fails
        """
        try:
            contact = await self.get(contact_id)
            service = await self.db.get(Service, service_id)

            if not contact or not service:
                return False

            if service in contact.services:
                contact.services.remove(service)
                await self.db.commit()
                return True

            return False

        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "remove_service_failed",
                contact_id=contact_id,
                service_id=service_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to remove service from contact",
                details={
                    "contact_id": contact_id,
                    "service_id": service_id,
                    "error": str(e),
                },
            ) from e

    async def add_category(self, contact_id: int, category_id: int) -> bool:
        """
        Add a category to a contact.

        Args:
            contact_id: Contact ID
            category_id: Category ID

        Returns:
            bool: Whether category was added

        Raises:
            IntegrityError: If operation fails
        """
        try:
            contact = await self.get(contact_id)
            category = await self.db.get(Category, category_id)

            if not contact or not category:
                return False

            if category not in contact.categories:
                contact.categories.append(category)
                await self.db.commit()
                return True

            return False

        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "add_category_failed",
                contact_id=contact_id,
                category_id=category_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to add category to contact",
                details={
                    "contact_id": contact_id,
                    "category_id": category_id,
                    "error": str(e),
                },
            ) from e

    async def remove_category(self, contact_id: int, category_id: int) -> bool:
        """
        Remove a category from a contact.

        Args:
            contact_id: Contact ID
            category_id: Category ID

        Returns:
            bool: Whether category was removed

        Raises:
            IntegrityError: If operation fails
        """
        try:
            contact = await self.get(contact_id)
            category = await self.db.get(Category, category_id)

            if not contact or not category:
                return False

            if category in contact.categories:
                contact.categories.remove(category)
                await self.db.commit()
                return True

            return False

        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "remove_category_failed",
                contact_id=contact_id,
                category_id=category_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to remove category from contact",
                details={
                    "contact_id": contact_id,
                    "category_id": category_id,
                    "error": str(e),
                },
            ) from e

    async def get_endorsement_stats(self, contact_id: int) -> Dict[str, Any]:
        """
        Get endorsement statistics for a contact.

        Args:
            contact_id: Contact ID

        Returns:
            Dict[str, Any]: Endorsement statistics

        Raises:
            QueryError: If query fails
        """
        try:
            # Get basic counts
            stats_query = select(
                func.count(ContactEndorsement.id).label("total"),
                func.sum(
                    case((ContactEndorsement.is_verified.is_(True), 1), else_=0)
                ).label("verified"),
                func.avg(ContactEndorsement.rating).label("average_rating"),
            ).where(ContactEndorsement.contact_id == contact_id)

            result = await self.db.execute(stats_query)
            basic_stats = result.one()

            # Get rating distribution
            rating_query = (
                select(
                    ContactEndorsement.rating,
                    func.count(ContactEndorsement.id).label("count"),
                )
                .where(
                    and_(
                        ContactEndorsement.contact_id == contact_id,
                        ContactEndorsement.rating.is_not(None),
                    )
                )
                .group_by(ContactEndorsement.rating)
            )

            rating_result = await self.db.execute(rating_query)
            rating_distribution = {row.rating: row.count for row in rating_result}

            return {
                "total_endorsements": basic_stats.total or 0,
                "verified_endorsements": basic_stats.verified or 0,
                "average_rating": (
                    round(basic_stats.average_rating, 2)
                    if basic_stats.average_rating
                    else None
                ),
                "rating_distribution": rating_distribution,
            }

        except SQLAlchemyError as e:
            self._logger.error(
                "get_endorsement_stats_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve endorsement statistics",
                details={"contact_id": contact_id, "error": str(e)},
            ) from e

    async def update_endorsement_metrics(self, contact_id: int) -> None:
        """
        Update a contact's endorsement-related metrics.

        Args:
            contact_id: Contact ID

        Raises:
            IntegrityError: If update fails
        """
        try:
            stats = await self.get_endorsement_stats(contact_id)

            stmt = (
                self._model.__table__.update()
                .where(self._model.id == contact_id)
                .values(
                    endorsements_count=stats["total_endorsements"],
                    verified_endorsements_count=stats["verified_endorsements"],
                    average_rating=stats["average_rating"],
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "update_endorsement_metrics_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to update endorsement metrics",
                details={"contact_id": contact_id, "error": str(e)},
            ) from e
