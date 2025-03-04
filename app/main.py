"""
Main application module for Neighbour Approved API.

This module initializes the FastAPI application and includes the API router.
It also configures logging, exception handling, and middleware.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.system.health.health_check import health_router
from app.core.configuration.config import settings
from app.core.logging.logger import get_logger
from app.core.middleware.request_logging import add_request_logging_middleware
from app.core.exception_handling.error_handler import register_exception_handlers

# Set up logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Handle application startup and shutdown events.

    This context manager replaces the deprecated on_event handlers
    with the recommended lifespan approach in FastAPI.

    Args:
        _: The FastAPI application instance (unused)
    """
    # Startup code
    logger.info("Application started successfully")

    yield

    # Shutdown code
    logger.info("Application is shutting down")


# Initialize the FastAPI application
app = FastAPI(
    title=settings.app_name if settings else "Neighbour Approved API",
    description=(
        settings.app_description if settings else "API for Neighbour Approved platform"
    ),
    version=settings.version if settings else "0.1.0",
    lifespan=lifespan,
)

# Log application startup
logger.info("Starting Neighbour Approved API")

# Register exception handlers
register_exception_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
add_request_logging_middleware(app)

# Include the system routers
app.include_router(
    health_router,
    prefix=f"{settings.api_base_url}/system" if settings else "/api/v1/system",
)

# Log application configuration
logger.info("Application configured with %s routes", len(app.routes))
logger.debug("Using settings: %s", settings)
