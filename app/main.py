"""
Main application module for Neighbour Approved API.

This module initializes the FastAPI application and includes the API router.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Neighbour Approved API",
    description="API for Neighbour Approved platform",
    version="0.1.0",
)


@app.get("/api/v1/system/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        dict: A dictionary with the status and version.
    """
    return {"status": "ok", "version": "0.1.0"}
