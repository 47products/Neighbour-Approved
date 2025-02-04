"""
Middleware management system for the Neighbour Approved application.

This module implements a comprehensive middleware management system that standardises
how middleware components are defined, registered, and executed across the application.
It provides a flexible framework for handling cross-cutting concerns while maintaining
consistent patterns and configuration options.

The module includes:
- Base middleware interface
- Middleware registry system
- Configuration management
- Execution pipeline handling
- Dependency management
"""

import time
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import structlog

logger = structlog.get_logger(__name__)


class MiddlewarePriority:
    """Enumeration for middleware execution priority levels."""

    FIRST = 1
    EARLY = 2
    NORMAL = 3
    LATE = 4
    LAST = 5


class MiddlewareConfig(BaseModel):
    """Base configuration for all middleware components."""

    enabled: bool = Field(default=True, description="Whether middleware is enabled")
    log_level: str = Field(default="INFO", description="Logging level for middleware")
    skip_paths: List[str] = Field(default_factory=list, description="Paths to skip")


ConfigType = TypeVar("ConfigType", bound=MiddlewareConfig)


class BaseMiddleware(BaseHTTPMiddleware, Generic[ConfigType]):
    """
    Base class for all middleware components.

    This class defines the interface that all middleware components must implement
    while providing common functionality through the BaseHTTPMiddleware integration.

    Type Parameters:
        ConfigType: Configuration model type for this middleware

    Attributes:
        app: FastAPI application instance
        config: Type-safe middleware configuration
        dependencies: List of required middleware classes
    """

    config_class: Type[ConfigType] = MiddlewareConfig

    def __init__(
        self,
        app: FastAPI,
        config: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[Type["BaseMiddleware"]]] = None,
    ) -> None:
        """Initialize middleware component."""
        super().__init__(app)
        self.config = self.config_class(**(config or {}))
        self.dependencies = dependencies or []
        self._logger = logger.bind(
            middleware=self.__class__.__name__, log_level=self.config.log_level
        )

    async def startup(self) -> None:
        """Called when middleware starts."""
        self._logger.debug("middleware_startup")

    async def shutdown(self) -> None:
        """Called when middleware shuts down."""
        self._logger.debug("middleware_shutdown")

    async def process(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request/response cycle.

        Args:
            request: FastAPI request instance
            call_next: Function to call the next middleware/endpoint

        Returns:
            Response: FastAPI response instance

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Middleware must implement process method")

    async def execute_pipeline(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
        pipeline_position: int,
        middleware_chain: List["BaseMiddleware"],
    ) -> Response:
        """
        Execute the middleware pipeline with proper ordering and error handling.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint to call
            pipeline_position: Current position in the middleware chain
            middleware_chain: List of middleware instances to execute

        Returns:
            Response: The processed HTTP response
        """
        try:
            if pipeline_position == len(middleware_chain):
                return await call_next(request)

            next_middleware = middleware_chain[pipeline_position]

            async def chain_next(req: Request) -> Response:
                return await next_middleware.execute_pipeline(
                    req, call_next, pipeline_position + 1, middleware_chain
                )

            start_time = time.time()
            try:
                response = await next_middleware.process(request, chain_next)
                execution_time = time.time() - start_time

                self._logger.debug(
                    "middleware_execution",
                    middleware=next_middleware.__class__.__name__,
                    execution_time=execution_time,
                    status_code=response.status_code if response else None,
                )

                return response

            except Exception as e:
                execution_time = time.time() - start_time
                self._logger.error(
                    "middleware_execution_failed",
                    middleware=next_middleware.__class__.__name__,
                    execution_time=execution_time,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

        except Exception as e:
            self._logger.error(
                "pipeline_execution_failed",
                error=str(e),
                error_type=type(e).__name__,
                pipeline_position=pipeline_position,
            )
            raise


class MiddlewareRegistry:
    """
    Registry for managing middleware components.

    This class handles middleware registration, ordering, and dependency resolution
    while maintaining configuration state.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._middlewares: Dict[Type[BaseMiddleware], Dict[str, Any]] = {}
        self._priority_map: Dict[Type[BaseMiddleware], int] = {}
        self._logger = logger.bind(component="MiddlewareRegistry")

    def register(
        self,
        middleware_class: Type[BaseMiddleware],
        priority: int = MiddlewarePriority.NORMAL,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a middleware component."""
        if middleware_class in self._middlewares:
            raise ValueError(
                f"Middleware {middleware_class.__name__} already registered"
            )

        self._middlewares[middleware_class] = config or {}
        self._priority_map[middleware_class] = priority
        self._logger.info(
            "middleware_registered",
            middleware=middleware_class.__name__,
            priority=priority,
        )

    def get_ordered_middlewares(self) -> List[Type[BaseMiddleware]]:
        """Get middleware classes in execution order."""
        return sorted(
            self._middlewares.keys(), key=lambda x: (self._priority_map[x], x.__name__)
        )

    async def startup_middlewares(self) -> None:
        """Start all registered middlewares."""
        for middleware_class in self.get_ordered_middlewares():
            instance = middleware_class(
                app=None, config=self._middlewares[middleware_class]
            )
            await instance.startup()
            self._logger.info(
                "middleware_started",
                middleware=middleware_class.__name__,
            )

    async def shutdown_middlewares(self) -> None:
        """Shut down all registered middlewares."""
        for middleware_class in reversed(self.get_ordered_middlewares()):
            instance = middleware_class(
                app=None, config=self._middlewares[middleware_class]
            )
            await instance.shutdown()
            self._logger.info(
                "middleware_shutdown",
                middleware=middleware_class.__name__,
            )

    async def execute_middleware_chain(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Execute the complete middleware chain for a request.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint to call

        Returns:
            Response: The processed HTTP response

        Note:
            This method initialises and executes the middleware chain in priority order.
        """
        middleware_chain = [
            middleware_class(app=None, config=self._middlewares[middleware_class])
            for middleware_class in self.get_ordered_middlewares()
        ]

        if middleware_chain:
            # Use the first middleware's public method to start the chain
            return await middleware_chain[0].execute_pipeline(
                request, call_next, 0, middleware_chain
            )

        return await call_next(request)

    def apply_middlewares(self, app: FastAPI) -> None:
        """Apply registered middlewares to FastAPI application."""

        @app.middleware("http")
        async def middleware_pipeline(
            request: Request, call_next: RequestResponseEndpoint
        ):
            return await self.execute_middleware_chain(request, call_next)

        self._logger.info("middleware_pipeline_configured")
