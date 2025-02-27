"""
Health check endpoint for the Neighbour Approved API.

This module provides a health check endpoint to verify the API is running properly.
"""

from app.api.v1.endpoints.system.health.health_router import health_router


@health_router.get("/health_check")
async def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        dict: A dictionary with the status and version.
    """
    return {"status": "ok", "version": "0.1.0"}
