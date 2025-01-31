"""
Contact service implementation module.

This module implements the contact management service layer, handling all
contact-related business logic including endorsement calculations,
category associations, and verification workflows. It ensures proper separation
of concerns by encapsulating business rules and validation logic.

The module provides comprehensive handling of:
- Contact creation and updates with validation
- Category and service associations
- Endorsement calculations and verification
- Integration with community service
"""

from datetime import datetime, UTC
from typing import List, Optional, Dict, Any, cast
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.services.service_interfaces import IContactService
from app.services.service_exceptions import (
    ValidationError,
    BusinessRuleViolationError,
    ResourceNotFoundError,
    DuplicateResourceError,
    StateError,
)
from app.db.models.contact_model import Contact
from app.db.models.category_model import Category
from app.db.models.service_model import Service
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.db.repositories.contact_repository import ContactRepository
from app.api.v1.schemas.contact_schema import ContactCreate, ContactUpdate


class ContactService(
    BaseService[Contact, ContactCreate, ContactUpdate], IContactService
):
    """
    Service for managing contact-related operations and business logic.

    This service implements contact management operations including contact creation,
    updates, endorsement handling, and verification workflows. It encapsulates
    all contact-related business rules and validation logic.

    Attributes:
        MAX_CONTACTS_FREE (int): Maximum contacts for free users
        MAX_SERVICES (int): Maximum services per contact
        MAX_CATEGORIES (int): Maximum categories per contact
        RESTRICTED_WORDS (set): Words not allowed in contact names
        REQUIRED_FIELDS (set): Required fields for contact creation
    """

    MAX_CONTACTS_FREE = 10
    MAX_SERVICES = 20
    MAX_CATEGORIES = 5
    RESTRICTED_WORDS = {"admin", "system", "support", "test"}
    REQUIRED_FIELDS = {
        "contact_name",
        "primary_contact_first_name",
        "primary_contact_last_name",
        "email",
    }

    def __init__(self, db: Session):
        """Initialize the contact service.

        Args:
            db: Database session for repository operations
        """
        super().__init__(
            model=Contact,
            repository=ContactRepository(db),
            logger_name="ContactService",
        )

    async def create_contact(self, data: ContactCreate) -> Contact:
        """Create a new contact with validation.

        This method implements comprehensive validation including uniqueness
        checks, quota enforcement, and business rule validation before
        creating a new contact.

        Args:
            data: Validated contact creation data

        Returns:
            Created contact instance

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If creation violates business rules
            DuplicateResourceError: If contact already exists
        """
        try:
            # Validate contact creation
            await self._validate_contact_creation(data)

            # Create contact
            contact = await self.create(data)

            self._logger.info(
                "contact_created",
                contact_id=contact.id,
                user_id=data.user_id,
                contact_name=data.contact_name,
            )

            return contact

        except Exception as e:
            self._logger.error(
                "contact_creation_failed",
                error=str(e),
                user_id=data.user_id,
                contact_name=data.contact_name,
            )
            raise

    async def _validate_contact_creation(self, data: ContactCreate) -> None:
        """Validate contact creation against business rules.

        Performs comprehensive validation including:
        - Required field validation
        - Contact name restrictions
        - User quota checks
        - Duplicate contact checks

        Args:
            data: Contact creation data

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If creation violates business rules
        """
        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(
            field for field, value in data.__dict__.items() if value is not None
        )
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Validate contact name
        if any(word in data.contact_name.lower() for word in self.RESTRICTED_WORDS):
            raise ValidationError("Contact name contains restricted words")

        # Check user quota
        contacts_count = await self._get_user_contacts_count(data.user_id)
        if contacts_count >= await self._get_user_contact_limit(data.user_id):
            raise BusinessRuleViolationError(
                f"User has reached maximum contacts ({self.MAX_CONTACTS_FREE})"
            )

        # Check for duplicate contact
        repository = cast(ContactRepository, self.repository)
        if await repository.get_by_email(data.email):
            raise DuplicateResourceError("Contact with this email already exists")

    async def get_contact(self, contact_id: int) -> Optional[Contact]:
        """Retrieve a contact by ID with access control.

        Args:
            contact_id: Contact's unique identifier

        Returns:
            Contact instance if found and accessible

        Raises:
            ResourceNotFoundError: If contact not found
        """
        contact = await self.get(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        return contact

    async def update_contact(
        self, contact_id: int, data: ContactUpdate
    ) -> Optional[Contact]:
        """Update contact information.

        This method implements update validation including business rule
        enforcement and access control.

        Args:
            contact_id: Contact's unique identifier
            data: Update data

        Returns:
            Updated contact instance

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If update violates business rules
            ResourceNotFoundError: If contact not found
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        try:
            # Validate update data
            await self._validate_contact_update(contact, data)

            # Process update
            updated_contact = await self.update(id=contact_id, data=data)

            self._logger.info(
                "contact_updated",
                contact_id=contact_id,
                updates=data.model_dump(exclude_unset=True),
            )

            return updated_contact

        except Exception as e:
            self._logger.error(
                "contact_update_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise

    async def _validate_contact_update(
        self, contact: Contact, data: ContactUpdate
    ) -> None:
        """Validate contact update against business rules.

        Args:
            contact: Existing contact instance
            data: Update data

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If update violates business rules
        """
        # Validate email update
        if data.email and data.email != contact.email:
            repository = cast(ContactRepository, self.repository)
            existing_contact = await repository.get_by_email(data.email)
            if existing_contact and existing_contact.id != contact.id:
                raise DuplicateResourceError("Email already registered")

        # Validate contact name
        if data.contact_name:
            if any(word in data.contact_name.lower() for word in self.RESTRICTED_WORDS):
                raise ValidationError("Contact name contains restricted words")

    async def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact with validation.

        This method implements deletion validation including business rule
        enforcement and cleanup of related resources.

        Args:
            contact_id: Contact's unique identifier

        Returns:
            True if contact was deleted

        Raises:
            ValidationError: If deletion not allowed
            ResourceNotFoundError: If contact not found
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        try:
            # Check if contact can be deleted
            if not await self._can_delete_contact(contact):
                raise BusinessRuleViolationError(
                    "Cannot delete contact with active endorsements"
                )

            # Perform deletion
            result = await self.delete(contact_id)

            self._logger.info(
                "contact_deleted",
                contact_id=contact_id,
                contact_name=contact.contact_name,
            )

            return result

        except Exception as e:
            self._logger.error(
                "contact_deletion_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise

    async def _can_delete_contact(self, contact: Contact) -> bool:
        """Check if contact can be deleted based on business rules.

        A contact cannot be deleted if it:
        - Has verified endorsements
        - Is referenced by active communities
        - Has pending verification requests

        Args:
            contact: Contact to evaluate

        Returns:
            Whether contact can be deleted
        """
        if contact.verified_endorsements_count > 0:
            return False

        if any(community.is_active for community in contact.communities):
            return False

        return True

    async def add_service(self, contact_id: int, service_id: int) -> bool:
        """Add a service to contact's offerings.

        This method handles service association including validation of
        service limits and compatibility.

        Args:
            contact_id: Contact's unique identifier
            service_id: Service to add

        Returns:
            bool: True if service was newly added, False if already present

        Raises:
            ValidationError: If service cannot be added
            ResourceNotFoundError: If contact or service not found
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        service = await self.db.get(Service, service_id)
        if not service or not service.is_active:
            raise ResourceNotFoundError(f"Service {service_id} not found")

        try:
            # Check if service already exists
            if service in contact.services:
                return False

            # Validate service addition
            if len(contact.services) >= self.MAX_SERVICES:
                raise BusinessRuleViolationError(
                    f"Contact has reached maximum services ({self.MAX_SERVICES})"
                )

            # Add service
            contact.services.append(service)
            await self.db.commit()

            self._logger.info(
                "service_added",
                contact_id=contact_id,
                service_id=service_id,
                service_name=service.name,
            )

            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "service_addition_failed",
                contact_id=contact_id,
                service_id=service_id,
                error=str(e),
            )
            raise

    async def remove_service(self, contact_id: int, service_id: int) -> bool:
        """Remove a service from contact's offerings.

        Args:
            contact_id: Contact's unique identifier
            service_id: Service to remove

        Returns:
            bool: True if service was removed, False if not found in contact's services

        Raises:
            ResourceNotFoundError: If contact or service not found
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        service = await self.db.get(Service, service_id)
        if not service:
            raise ResourceNotFoundError(f"Service {service_id} not found")

        try:
            # Check if service exists and remove it
            if service not in contact.services:
                return False

            contact.services.remove(service)
            await self.db.commit()

            self._logger.info(
                "service_removed",
                contact_id=contact_id,
                service_id=service_id,
                service_name=service.name,
            )

            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "service_removal_failed",
                contact_id=contact_id,
                service_id=service_id,
                error=str(e),
            )
            raise

    async def get_contact_endorsements(
        self, contact_id: int
    ) -> List[ContactEndorsement]:
        """Get endorsements for a contact.

        Args:
            contact_id: Contact's unique identifier

        Returns:
            List of contact endorsements

        Raises:
            ResourceNotFoundError: If contact not found
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        return contact.endorsements

    async def verify_contact(self, contact_id: int, verified_by: int) -> bool:
        """Mark a contact as verified.

        This method implements the contact verification workflow including
        validation and audit logging.

        Args:
            contact_id: Contact's unique identifier
            verified_by: User ID performing verification

        Returns:
            True if contact was verified

        Raises:
            ValidationError: If verification requirements not met
            ResourceNotFoundError: If contact not found
            StateError: If verification fails
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        try:
            # Validate verification requirements
            if not await self._can_verify_contact(contact):
                raise ValidationError("Contact does not meet verification requirements")

            # Update verification status
            contact.is_verified = True
            contact.verification_date = datetime.now(UTC)
            contact.verification_notes = (
                f"Verified by user {verified_by} on {datetime.now(UTC)}"
            )

            await self.db.commit()

            self._logger.info(
                "contact_verified",
                contact_id=contact_id,
                verified_by=verified_by,
            )

            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "contact_verification_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise StateError(f"Failed to verify contact: {str(e)}")

    async def _can_verify_contact(self, contact: Contact) -> bool:
        """Check if contact meets verification requirements.

        A contact can be verified if it:
        - Has required profile information
        - Has minimum number of endorsements
        - Has active community memberships
        - Has no recent negative endorsements

        Args:
            contact: Contact to evaluate

        Returns:
            Whether contact can be verified
        """
        if not contact.is_active:
            return False

        # Check required information
        if not all(
            [
                contact.email,
                contact.contact_number,
                contact.primary_contact_contact_number,
            ]
        ):
            return False

        # Check endorsements
        if contact.endorsements_count < 3:
            return False

        # Check community membership
        if not contact.communities:
            return False

        return True

    async def _get_user_contacts_count(self, user_id: int) -> int:
        """Get count of active contacts for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            Count of user's active contacts
        """
        return (
            await self.db.query(Contact)
            .filter(Contact.user_id == user_id, Contact.is_active is True)
            .count()
        )

    async def _get_user_contact_limit(self, user_id: int) -> int:
        """Get contact limit for user based on subscription.

        This method determines the maximum allowed contacts based on
        user's subscription tier and role.

        Args:
            user_id: User to check

        Returns:
            Maximum allowed contacts
        """
        from app.db.models.user_model import User  # Avoid circular import

        user = await self.db.get(User, user_id)
        if not user:
            return self.MAX_CONTACTS_FREE

        # Check for premium features
        if any(role.name == "premium_user" for role in user.roles if role.is_active):
            return 50  # Premium limit

        return self.MAX_CONTACTS_FREE

    async def add_category(self, contact_id: int, category_id: int) -> bool:
        """Add a category association to contact.

        This method handles category association including validation of
        category limits and hierarchy rules.

        Args:
            contact_id: Contact's unique identifier
            category_id: Category to add

        Returns:
            bool: True if category was newly added, False if already present

        Raises:
            ValidationError: If category cannot be added
            ResourceNotFoundError: If contact or category not found
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        category = await self.db.get(Category, category_id)
        if not category or not category.is_active:
            raise ResourceNotFoundError(f"Category {category_id} not found")

        try:
            # Check if category already exists
            if category in contact.categories:
                return False

            # Validate category addition
            if len(contact.categories) >= self.MAX_CATEGORIES:
                raise BusinessRuleViolationError(
                    f"Contact has reached maximum categories ({self.MAX_CATEGORIES})"
                )

            # Validate category hierarchy
            if not await self._validate_category_hierarchy(contact, category):
                raise ValidationError("Invalid category hierarchy")

            # Add category
            contact.categories.append(category)
            await self.db.commit()

            self._logger.info(
                "category_added",
                contact_id=contact_id,
                category_id=category_id,
                category_name=category.name,
            )

            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "category_addition_failed",
                contact_id=contact_id,
                category_id=category_id,
                error=str(e),
            )
            raise

    async def _validate_category_hierarchy(
        self, contact: Contact, new_category: Category
    ) -> bool:
        """Validate category addition against hierarchy rules.

        Ensures that:
        - No duplicate categories in hierarchy
        - No conflicts with existing categories
        - Proper parent-child relationships

        Args:
            contact: Contact to validate
            new_category: Category to validate

        Returns:
            Whether category hierarchy is valid
        """
        # Check for duplicate categories
        if new_category in contact.categories:
            return False

        # Check for parent category
        if new_category.parent and new_category.parent in contact.categories:
            return False

        # Check for child categories
        existing_categories = set(contact.categories)
        for category in new_category.get_descendants():
            if category in existing_categories:
                return False

        return True

    async def remove_category(self, contact_id: int, category_id: int) -> bool:
        """Remove a category association from contact.

        Args:
            contact_id: Contact's unique identifier
            category_id: Category to remove

        Returns:
            bool: True if category was removed, False if not found in contact's categories

        Raises:
            ResourceNotFoundError: If contact or category not found
            BusinessRuleViolationError: If category cannot be removed
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        category = await self.db.get(Category, category_id)
        if not category:
            raise ResourceNotFoundError(f"Category {category_id} not found")

        try:
            # Check if category exists
            if category not in contact.categories:
                return False

            # Check if category can be removed
            if not await self._can_remove_category(contact, category):
                raise BusinessRuleViolationError(
                    "Cannot remove category with active services"
                )

            contact.categories.remove(category)
            await self.db.commit()

            self._logger.info(
                "category_removed",
                contact_id=contact_id,
                category_id=category_id,
                category_name=category.name,
            )

            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "category_removal_failed",
                contact_id=contact_id,
                category_id=category_id,
                error=str(e),
            )
            raise

    async def _can_remove_category(self, contact: Contact, category: Category) -> bool:
        """Check if category can be removed from contact.

        A category cannot be removed if:
        - It has active services
        - It is required by endorsements
        - It is a parent category with active children

        Args:
            contact: Contact to check
            category: Category to check

        Returns:
            Whether category can be removed
        """
        # Check for active services in category
        if any(
            service.category_id == category.id and service.is_active
            for service in contact.services
        ):
            return False

        # Check for endorsements requiring category
        if any(
            endorsement.is_verified
            and any(service.category_id == category.id for service in contact.services)
            for endorsement in contact.endorsements
        ):
            return False

        return True

    async def update_endorsement_metrics(self, contact_id: int) -> None:
        """Update contact's endorsement-related metrics.

        This method recalculates:
        - Total endorsement count
        - Verified endorsement count
        - Average rating
        - Other endorsement-based metrics

        Args:
            contact_id: Contact to update

        Raises:
            ResourceNotFoundError: If contact not found
            StateError: If update fails
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        try:
            # Calculate metrics
            total_endorsements = len(contact.endorsements)
            verified_endorsements = sum(
                1 for e in contact.endorsements if e.is_verified
            )

            # Calculate average rating
            rated_endorsements = [
                e
                for e in contact.endorsements
                if e.is_verified and e.rating is not None
            ]
            average_rating = (
                sum(e.rating for e in rated_endorsements) / len(rated_endorsements)
                if rated_endorsements
                else None
            )

            # Update contact
            contact.endorsements_count = total_endorsements
            contact.verified_endorsements_count = verified_endorsements
            contact.average_rating = (
                round(average_rating, 2) if average_rating else None
            )

            await self.db.commit()

            self._logger.info(
                "endorsement_metrics_updated",
                contact_id=contact_id,
                total=total_endorsements,
                verified=verified_endorsements,
                average_rating=average_rating,
            )

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "endorsement_metrics_update_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise StateError(f"Failed to update endorsement metrics: {str(e)}")

    async def get_contact_stats(self, contact_id: int) -> Dict[str, Any]:
        """Get comprehensive contact statistics.

        This method aggregates various metrics including:
        - Endorsement statistics
        - Service usage
        - Community participation
        - Verification status

        Args:
            contact_id: Contact to analyze

        Returns:
            Dictionary of contact statistics

        Raises:
            ResourceNotFoundError: If contact not found
        """
        contact = await self.get_contact(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        stats = {
            "total_endorsements": contact.endorsements_count,
            "verified_endorsements": contact.verified_endorsements_count,
            "average_rating": contact.average_rating,
            "total_services": len(contact.services),
            "active_services": sum(
                1 for service in contact.services if service.is_active
            ),
            "total_categories": len(contact.categories),
            "communities": len(contact.communities),
            "active_communities": sum(
                1 for community in contact.communities if community.is_active
            ),
            "verification_status": {
                "is_verified": (
                    contact.is_verified if hasattr(contact, "is_verified") else False
                ),
                "verification_date": (
                    contact.verification_date
                    if hasattr(contact, "verification_date")
                    else None
                ),
                "meets_requirements": await self._can_verify_contact(contact),
            },
        }

        # Add endorsement breakdown
        endorsement_breakdown = {
            "positive": sum(1 for e in contact.endorsements if e.endorsed),
            "negative": sum(1 for e in contact.endorsements if not e.endorsed),
            "rating_distribution": {
                i: sum(1 for e in contact.endorsements if e.rating == i)
                for i in range(1, 6)
            },
        }
        stats["endorsement_breakdown"] = endorsement_breakdown

        return stats
