"""
Dependency injection module for Neighbour Approved.

This module implements a centralized dependency injection system, managing the lifecycle of services
and repositories used throughout the application. It leverages FastAPI's dependency injection
mechanism to provide clean and efficient access to core business logic.

Features:
- Centralized container for dependency management
- Lazy initialization of repositories and services
- Cleanup mechanisms for resource deallocation
- Compatibility with FastAPI's dependency injection
"""

from typing import Generator
from fastapi import Depends
from app.services.user_service import UserService
from app.services.community_service import CommunityService
from app.services.contact_service import ContactService
from app.services.endorsement_service import EndorsementService
from app.db.database_engine import create_session
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.community_repository import CommunityRepository
from app.db.repositories.contact_repository import ContactRepository
from app.db.repositories.contact_endorsement_repository import (
    ContactEndorsementRepository,
)


class Repositories:
    """Container for repository instances."""

    def __init__(self, session):
        """
        Initialize repositories with database session.

        Args:
            session: Database session for repositories.
        """
        self.user = UserRepository(session)
        self.community = CommunityRepository(session)
        self.contact = ContactRepository(session)
        self.endorsement = ContactEndorsementRepository(session)


class Services:
    """Container for service instances."""

    def __init__(self, repositories: Repositories):
        """
        Initialize services with repository instances.

        Args:
            repositories: Repository container instance.
        """
        self.user = UserService(repositories.user)
        self.community = CommunityService(repositories.community)
        self.contact = ContactService(repositories.contact)
        self.endorsement = EndorsementService(repositories.endorsement)


class DependencyContainer:
    """
    Centralized container for dependency injection in the application.

    This container creates and manages service instances, ensuring consistent
    and reusable dependencies across the application lifecycle.
    """

    def __init__(self):
        self.session = create_session()
        self.repositories = Repositories(self.session)
        self.services = Services(self.repositories)

    def cleanup(self):
        """Cleanup resources when the application shuts down."""
        self.session.close()


def get_container() -> Generator[DependencyContainer, None, None]:
    """
    Create a new DependencyContainer for each request and ensure cleanup.

    Yields:
        DependencyContainer: A new instance of the container.
    """
    container = DependencyContainer()
    try:
        yield container
    finally:
        container.cleanup()


def get_user_service(
    container: DependencyContainer = Depends(get_container),
) -> UserService:
    """
    Dependency injection for UserService.

    Args:
        container: The dependency container instance.

    Returns:
        UserService: The user service instance.
    """
    return container.services.user


def get_community_service(
    container: DependencyContainer = Depends(get_container),
) -> CommunityService:
    """
    Dependency injection for CommunityService.

    Args:
        container: The dependency container instance.

    Returns:
        CommunityService: The community service instance.
    """
    return container.services.community


def get_contact_service(
    container: DependencyContainer = Depends(get_container),
) -> ContactService:
    """
    Dependency injection for ContactService.

    Args:
        container: The dependency container instance.

    Returns:
        ContactService: The contact service instance.
    """
    return container.services.contact


def get_endorsement_service(
    container: DependencyContainer = Depends(get_container),
) -> EndorsementService:
    """
    Dependency injection for EndorsementService.

    Args:
        container: The dependency container instance.

    Returns:
        EndorsementService: The endorsement service instance.
    """
    return container.services.endorsement
