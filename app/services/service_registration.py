"""
Service registration module for Neighbour Approved application.

This module implements the service registration and management system,
providing centralized service lifecycle management and dependency injection.
It ensures proper initialization and cleanup of services while maintaining
dependency relationships between different service components.
"""

from typing import Any, Dict, Optional, Type, cast
from contextlib import contextmanager
import structlog
from fastapi import Depends
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.services.service_exceptions import DependencyError
from app.db.database_session_management import get_db
from app.services.user_service.user_service_authentication import AuthenticationService
from app.services.user_service.user_service_email_verification import (
    EmailVerificationService,
)
from app.services.user_service.user_service_role import RoleService
from app.services.user_service.user_service_security import SecurityService
from app.services.user_service.user_management import UserManagementService

logger = structlog.get_logger(__name__)


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

    def register[
        T: BaseService
    ](
        self,
        service_class: Type[T],
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

    def get_service[T: BaseService](self, service_name: str, db: Session) -> T:
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
                resolved_deps = {
                    dep_name: self.get_service(dep_service_name, db)
                    for dep_name, dep_service_name in service_info[
                        "dependencies"
                    ].items()
                }

                service_info["instance"] = service_info["class"](
                    db=db, **resolved_deps, **service_info["params"]
                )
                self._logger.info("service_initialized", service=service_name)
            except Exception as e:
                self._logger.error(
                    "service_initialization_failed", service=service_name, error=str(e)
                )
                raise DependencyError(
                    f"Failed to initialize service {service_name}: {str(e)}"
                ) from e

        return cast(T, service_info["instance"])

    @contextmanager
    def service_context(self, service_name: str, db: Session):
        service = self.get_service(service_name, db)
        try:
            yield service
        finally:
            self._logger.info(f"Service context closed for {service_name}")

    def create_dependency(self, service_name: str) -> Any:
        """
        Create a FastAPI dependency for a service.
        """

        def get_service(db: Session = Depends(get_db)) -> BaseService:
            return self.get_service(service_name, db)

        return get_service

    def reset(self) -> None:
        """
        Reset the registry, clearing all service instances.
        """
        self._services.clear()
        self._initialized = False
        self._logger.info("registry_reset")


# Global registry instance
registry = ServiceRegistry()


def get_registry() -> ServiceRegistry:
    return registry


def register_core_services() -> None:
    if registry._initialized:
        logger.info("Services already registered")
        return

    logger.info("Starting core service registration")

    try:
        registry.register(SecurityService, name="SecurityService")
        registry.register(
            AuthenticationService,
            name="AuthenticationService",
            dependencies={"security_service": "SecurityService"},
        )
        registry.register(EmailVerificationService, name="EmailVerificationService")
        registry.register(RoleService, name="RoleService")
        registry.register(
            UserManagementService,
            name="UserManagementService",
            dependencies={"security_service": "SecurityService"},
        )

        registry._initialized = True
        logger.info("Core service registration complete")
    except Exception as e:
        logger.error("Service registration failed", error=str(e))
        raise
