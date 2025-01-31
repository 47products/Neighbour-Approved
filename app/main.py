"""
Main application entry point for the Neighbour Approved backend.

This module initializes the FastAPI application instance and configures core
functionality including error handling, routing, and middleware. It uses the
recommended lifespan approach for handling application lifecycle events.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from app.api.v1.routers import api_router
from app.core.error_handling import setup_error_handlers
from app.core.logging_configuration import setup_logging
from app.core.logging_middleware import setup_logging_middleware
from app.core.config import get_settings

# Initialize logger
logger = structlog.get_logger(__name__)

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Handle application lifecycle events with enhanced logging."""
    # Startup
    logger.info(
        "application_starting",
        environment=os.getenv("ENVIRONMENT", "development"),
        debug_mode=application.debug,
    )

    yield  # Application running

    # Shutdown
    logger.info("application_shutdown")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application with logging."""
    # Initialize logging first
    setup_logging()

    # Get settings
    settings = get_settings()

    application = FastAPI(
        title="Neighbour Approved",
        description="A platform for community-driven endorsements of contractors.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Set up middleware (including logging middleware)
    setup_logging_middleware(application)

    # Set up error handlers
    setup_error_handlers(application)

    # Include API routers
    application.include_router(api_router)

    return application


app = create_application()
