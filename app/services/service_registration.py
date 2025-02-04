"""
Service registration module for Neighbour Approved application.

This module implements the service registration and management system,
providing centralized service lifecycle management and dependency injection.
It ensures proper initialization and cleanup of services while maintaining
dependency relationships between different service components.
"""

from typing import Any, Dict, Optional, Type, TypeVar, cast
from contextlib import contextmanager
import structlog
from fastapi import Depends
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.services.service_exceptions import DependencyError
from app.db.database_session_management import get_db
from app.services.user_service.authentication import AuthenticationService
from app.services.user_service.email_verification import (
    EmailVerificationService,
)
from app.services.user_service.role import RoleService
from app.services.user_service.security import SecurityService
from app.services.user_service.user_management import UserManagementService

logger = structlog.get_logger(__name__)

ServiceType = TypeVar("ServiceType", bound=BaseService)


class ServiceRegistry:
    """
    Central registry for managing application services.

    This class provides service registration, lifecycle management, and
    dependency resolution for all application services. It ensures services
    are properly initialized and maintains their relationships.
    """

    _instance = None
    _services: Dict[str, Dict[str, Any]] = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logger = logger.bind(component="ServiceRegistry")
        return cls._instance

    def register(
        self,
        service_class: Type[ServiceType],
        *,
        name: Optional[str] = None,
        dependencies: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Register a service with the registry.

        Args:
            service_class: Service class to register.
            name: Optional custom name for the service.
            dependencies: Optional dictionary of service dependencies by name.
            **kwargs: Additional initialization parameters.

        Raises:
            ValueError: If service name is already registered.
        """
        service_name = name or service_class.__name__
        if service_name in self._services:
            self._logger.warning("service_already_registered", service=service_name)
            return

        self._services[service_name] = {
            "class": service_class,
            "dependencies": dependencies or {},
            "params": kwargs,
            "instance": None,
        }
        self._logger.info(
            "service_registered",
            service=service_name,
            dependencies=list(dependencies.keys()) if dependencies else [],
        )

    def get_service(
        self,
        service_name: str,
        db: Session,
    ) -> ServiceType:
        """
        Get or create a service instance.

        Args:
            service_name: Name of the service to retrieve.
            db: Database session for service initialization.

        Returns:
            Initialized service instance.

        Raises:
            KeyError: If service is not registered.
            DependencyError: If service dependencies cannot be resolved.
        """
        if service_name not in self._services:
            raise KeyError(f"Service {service_name} is not registered")

        service_info = self._services[service_name]
        if not service_info["instance"]:
            try:
                # Resolve dependencies
                resolved_deps = {}
                for dep_name, dep_service_name in service_info["dependencies"].items():
                    resolved_deps[dep_name] = self.get_service(dep_service_name, db)

                # Create service instance
                service_info["instance"] = service_info["class"](
                    db=db,
                    **resolved_deps,
                    **service_info["params"],
                )
                self._logger.info(
                    "service_initialized",
                    service=service_name,
                )

            except Exception as e:
                self._logger.error(
                    "service_initialization_failed",
                    service=service_name,
                    error=str(e),
                )
                raise DependencyError(
                    f"Failed to initialize service {service_name}: {str(e)}"
                ) from e

        return cast(ServiceType, service_info["instance"])

    @contextmanager
    def service_context(
        self,
        service_name: str,
        db: Session,
    ):
        """
        Context manager for service usage.

        Provides a service instance within a context, handling cleanup
        when the context exits.

        Args:
            service_name: Name of the service to use.
            db: Database session for service initialization.

        Yields:
            Initialized service instance.

        Example:
            with registry.service_context("UserService", db) as service:
                result = await service.get_user(user_id)
        """
        service = self.get_service(service_name, db)
        try:
            yield service
        finally:
            # Perform any necessary cleanup
            pass

    def create_dependency(
        self,
        service_name: str,
    ) -> Any:
        """
        Create a FastAPI dependency for a service.

        Args:
            service_name: Name of the service to create dependency for.

        Returns:
            FastAPI dependency callable.

        Example:
            @router.get("/users/{user_id}")
            async def get_user(
                user_id: int,
                service: UserService = Depends(registry.create_dependency("UserService"))
            ):
                return await service.get_user(user_id)
        """

        def get_service(db: Session = Depends(get_db)) -> ServiceType:
            return self.get_service(service_name, db)

        return get_service

    def reset(self) -> None:
        """
        Reset the registry, clearing all service instances.

        This is primarily useful for testing scenarios where you need
        to reset the state between tests.
        """
        self._services.clear()
        self._initialized = False
        self._logger.info("registry_reset")


# Global registry instance
registry = ServiceRegistry()


def get_registry() -> ServiceRegistry:
    """
    Get the global service registry instance.

    Returns:
        ServiceRegistry: Global registry instance.

    Example:
        registry = get_registry()
        registry.register(UserService, name="UserService")
    """
    return registry


def register_core_services() -> None:
    """Register all core application services."""
    if registry._initialized:
        logger.info("Services already registered")
        return

    logger.info("Starting core service registration")

    try:
        # Register base services first
        logger.info("Registering base services")
        registry.register(
            SecurityService,
            name="SecurityService",
        )

        # Register user-related services
        logger.info("Registering user services")
        registry.register(
            AuthenticationService,
            name="AuthenticationService",
            dependencies={
                "security_service": "SecurityService",
            },
        )

        registry.register(
            EmailVerificationService,
            name="EmailVerificationService",
        )

        registry.register(
            RoleService,
            name="RoleService",
        )

        registry.register(
            UserManagementService,
            name="UserManagementService",
            dependencies={
                "security_service": "SecurityService",
            },
        )

        registry._initialized = True
        logger.info("Core service registration complete")
    except Exception as e:
        logger.error("Service registration failed", error=str(e))
        raise
