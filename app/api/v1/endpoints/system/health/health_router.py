"""
Health Router Module for the Neighbour Approved API.

This module provides the health router for the API, which includes all health check endpoints.
"""

from fastapi import APIRouter

health_router = APIRouter(
    prefix="/health",
    tags=["System", "Health"],
)
