"""
API Router Aggregation Module for Neighbour Approved Backend.

This module serves as the central aggregation point for all API routers under version 1 (`v1`)
of the Neighbour Approved backend application. By using FastAPI's `APIRouter`, it allows for
modular and scalable organization of API endpoints, facilitating easy maintenance and extension
of the application's functionality.

Currently, this module includes the `info` router, which provides basic application information.
As the application grows, additional routers can be included following the established pattern.

Attributes:
    api_router (APIRouter): The main API router that includes all sub-routers for version 1.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import info

# Initialize the main API router for version 1 of the API
api_router = APIRouter(tags=["API v1"], responses={404: {"description": "Not Found"}})

# Include the `info` router with a specific prefix and tag
api_router.include_router(
    info.router, tags=["Info"], responses={404: {"description": "Info Not Found"}}
)

# Future routers can be included here following the same pattern
# Example:
# from app.api.v1.endpoints import users
# api_router.include_router(
#     users.router,
#     prefix="/users",
#     tags=["Users"],
#     responses={404: {"description": "User Not Found"}}
# )
