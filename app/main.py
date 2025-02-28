"""
Main application module for Neighbour Approved API.

This module initializes the FastAPI application and includes the API router.
"""

from fastapi import FastAPI

from app.api.v1.endpoints.system.health.health_check import health_router
from app.core.configuration.config import settings

app = FastAPI(
    title=settings.app_name if settings else "Neighbour Approved API",
    description=(
        settings.app_description if settings else "API for Neighbour Approved platform"
    ),
    version=settings.version if settings else "0.1.0",
)

# Include the system routers
app.include_router(
    health_router,
    prefix=f"{settings.api_base_url}/system" if settings else "/api/v1/system",
)
