"""
Main application entry point for the Neighbour Approved backend.

This module initializes the FastAPI application instance and configures core
functionality including error handling, routing, and middleware. It uses the
recommended lifespan approach for handling application lifecycle events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.routers import api_router
from app.core.error_handling import setup_error_handlers
import structlog

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application lifecycle events.

    This context manager handles startup and shutdown events for the application,
    ensuring proper initialization and cleanup of resources.
    """
    # Startup
    logger.info("🟢 Application starting up.")
    # Add any startup initialization here (database connections, caches, etc.)

    yield  # Application running

    # Shutdown
    logger.info("🔴 Application shutting down.")
    # Add any cleanup code here (closing connections, etc.)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        A configured FastAPI application instance.
    """
    application = FastAPI(
        title="Neighbour Approved",
        description="A platform for community-driven endorsements of contractors.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Set up error handlers
    setup_error_handlers(application)

    # Include API routers
    application.include_router(api_router)

    return application


app = create_application()
