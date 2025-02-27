"""
Main application module for Neighbour Approved API.

This module initializes the FastAPI application and includes the API router.
"""

from fastapi import FastAPI

from app.api.v1.endpoints.system.health.health_check import health_router

app = FastAPI(
    title="Neighbour Approved API",
    description="API for Neighbour Approved platform",
    version="0.1.0",
)

# Include the system routers
app.include_router(health_router, prefix="/api/v1/system")
