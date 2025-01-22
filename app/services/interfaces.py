"""
Service interface definitions for Neighbour Approved application.

This module defines the interface contracts for all service types in the
application. It establishes the protocols that service implementations must
follow while maintaining clear separation of concerns and type safety.

The interfaces defined here serve as the foundation for the service layer,
ensuring consistent implementation patterns across different service types.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, TypeVar
from pydantic import EmailStr

from app.api.v1.schemas.user_schema import UserCreate, UserUpdate
from app.api.v1.schemas.community_schema import CommunityCreate, CommunityUpdate
from app.api.v1.schemas.contact_schema import ContactCreate, ContactUpdate
from app.api.v1.schemas.contact_endorsement_schema import (
    ContactEndorsementCreate,
    ContactEndorsementUpdate,
)
from app.db.models.user_model import User
from app.db.models.community_model import Community
from app.db.models.contact_model import Contact
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.db.models.role_model import Role
from app.db.models.service_model import Service

# Type variables for generic service methods
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class IUserService(Protocol):
    """Interface defining user management operations."""

    async def authenticate(self, email: EmailStr, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        ...

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user with validation."""
        ...

    async def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        ...

    async def update_user(self, user_id: int, data: UserUpdate) -> Optional[User]:
        """Update user information."""
        ...

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user account."""
        ...

    async def verify_email(self, user_id: int) -> bool:
        """Mark user's email as verified."""
        ...

    async def assign_role(self, user_id: int, role_id: int) -> Optional[User]:
        """Assign a role to a user."""
        ...

    async def remove_role(self, user_id: int, role_id: int) -> Optional[User]:
        """Remove a role from a user."""
        ...

    async def get_user_communities(self, user_id: int) -> List[Community]:
        """Get communities associated with user."""
        ...


class ICommunityService(Protocol):
    """Interface defining community management operations."""

    async def create_community(self, data: CommunityCreate) -> Community:
        """Create a new community."""
        ...

    async def get_community(self, community_id: int) -> Optional[Community]:
        """Retrieve a community by ID."""
        ...

    async def update_community(
        self, community_id: int, data: CommunityUpdate
    ) -> Optional[Community]:
        """Update community information."""
        ...

    async def delete_community(self, community_id: int) -> bool:
        """Delete a community."""
        ...

    async def add_member(self, community_id: int, user_id: int) -> bool:
        """Add a user to the community."""
        ...

    async def remove_member(self, community_id: int, user_id: int) -> bool:
        """Remove a user from the community."""
        ...

    async def get_community_contacts(self, community_id: int) -> List[Contact]:
        """Get contacts associated with community."""
        ...

    async def get_community_members(self, community_id: int) -> List[User]:
        """Get members of the community."""
        ...


class IContactService(Protocol):
    """Interface defining contact management operations."""

    async def create_contact(self, data: ContactCreate) -> Contact:
        """Create a new contact."""
        ...

    async def get_contact(self, contact_id: int) -> Optional[Contact]:
        """Retrieve a contact by ID."""
        ...

    async def update_contact(
        self, contact_id: int, data: ContactUpdate
    ) -> Optional[Contact]:
        """Update contact information."""
        ...

    async def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact."""
        ...

    async def add_service(self, contact_id: int, service_id: int) -> bool:
        """Add a service to contact's offerings."""
        ...

    async def remove_service(self, contact_id: int, service_id: int) -> bool:
        """Remove a service from contact's offerings."""
        ...

    async def get_contact_endorsements(
        self, contact_id: int
    ) -> List[ContactEndorsement]:
        """Get endorsements for a contact."""
        ...

    async def verify_contact(self, contact_id: int, verified_by: int) -> bool:
        """Mark a contact as verified."""
        ...


class IEndorsementService(Protocol):
    """Interface defining endorsement management operations."""

    async def create_endorsement(
        self, data: ContactEndorsementCreate
    ) -> ContactEndorsement:
        """Create a new endorsement."""
        ...

    async def get_endorsement(
        self, endorsement_id: int
    ) -> Optional[ContactEndorsement]:
        """Retrieve an endorsement by ID."""
        ...

    async def update_endorsement(
        self, endorsement_id: int, data: ContactEndorsementUpdate
    ) -> Optional[ContactEndorsement]:
        """Update endorsement information."""
        ...

    async def delete_endorsement(self, endorsement_id: int) -> bool:
        """Delete an endorsement."""
        ...

    async def verify_endorsement(self, endorsement_id: int, verified_by: int) -> bool:
        """Mark an endorsement as verified."""
        ...

    async def get_community_endorsements(
        self, community_id: int
    ) -> List[ContactEndorsement]:
        """Get endorsements within a community."""
        ...


class IRoleService(Protocol):
    """Interface defining role management operations."""

    async def create_role(
        self,
        name: str,
        permissions: List[str],
        description: Optional[str] = None,
    ) -> Role:
        """Create a new role."""
        ...

    async def get_role(self, role_id: int) -> Optional[Role]:
        """Retrieve a role by ID."""
        ...

    async def update_role(
        self,
        role_id: int,
        permissions: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Optional[Role]:
        """Update role information."""
        ...

    async def delete_role(self, role_id: int) -> bool:
        """Delete a role."""
        ...

    async def get_role_users(self, role_id: int) -> List[User]:
        """Get users assigned to a role."""
        ...


class IServiceManagement(Protocol):
    """Interface defining service offering management operations."""

    async def create_service(
        self,
        name: str,
        category_id: int,
        description: Optional[str] = None,
        base_price: Optional[float] = None,
    ) -> Service:
        """Create a new service offering."""
        ...

    async def get_service(self, service_id: int) -> Optional[Service]:
        """Retrieve a service by ID."""
        ...

    async def update_service(
        self,
        service_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        base_price: Optional[float] = None,
    ) -> Optional[Service]:
        """Update service information."""
        ...

    async def delete_service(self, service_id: int) -> bool:
        """Delete a service."""
        ...

    async def get_category_services(self, category_id: int) -> List[Service]:
        """Get services in a category."""
        ...


class IAuditService(Protocol):
    """Interface defining audit logging operations."""

    async def log_user_action(
        self,
        user_id: int,
        action: str,
        target_type: str,
        target_id: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a user action."""
        ...

    async def get_user_audit_log(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get audit log entries for a user."""
        ...

    async def get_resource_audit_log(
        self,
        resource_type: str,
        resource_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get audit log entries for a resource."""
        ...
