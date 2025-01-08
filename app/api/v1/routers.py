"""
API Router Aggregation Module for Neighbour Approved Backend.

This module serves as the central aggregation point for all API routers under version 1 (`v1`)
of the Neighbour Approved backend application. By using FastAPI's `APIRouter`, it allows for
modular and scalable organization of API endpoints, facilitating easy maintenance and extension
of the application's functionality.

Currently, this module includes the `info` and `health` routers. As the application grows,
additional routers can be included following the established pattern.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health_check_endpoint, info_endpoint

# Initialize the main API router without a prefix
api_router = APIRouter(
    prefix="/api/v1", tags=["API v1"], responses={404: {"description": "Not Found"}}
)

# Include the `info` router with its specific prefix and tag
api_router.include_router(
    info_endpoint.router,
    prefix="/info",
    tags=["Info"],
    responses={404: {"description": "Info Not Found"}},
)

# Include the `health` router without an additional prefix
api_router.include_router(
    health_check_endpoint.router,
    prefix="/health",
    tags=["Health"],
    responses={404: {"description": "Health Endpoint Not Found"}},
)
