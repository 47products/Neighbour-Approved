"""
Main application entry point for the Neighbour Approved backend.

This module initialises the FastAPI application instance and defines
core endpoints. It serves as the starting point of the application and
manages request handling and response formatting.

The application defined here includes a basic health check endpoint
to confirm that the service is running correctly. Additional routes and
APIs should be mounted from their respective routers as the project
evolves.
"""

from fastapi import FastAPI
from app.api.v1.routers import api_router

app = FastAPI(
    title="Neighbour Approved",
    description="A platform for community-driven endorsements of contractors.",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")
