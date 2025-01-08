"""
This module defines the `/info` endpoint for the Neighbour Approved backend application.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.api.v1.schemas.info_schema import InfoResponse

router = APIRouter(tags=["Info"], responses={404: {"description": "Not Found"}})


@router.get(
    "/",
    response_model=InfoResponse,
    summary="Get Application Info",
    response_class=JSONResponse,
    responses={
        200: {
            "description": "Application information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {"name": "Neighbour Approved", "version": "0.1.0"}
                }
            },
        }
    },
)
async def get_info() -> JSONResponse:
    """Get application information"""
    return JSONResponse(
        content={"name": "Neighbour Approved", "version": "0.1.0"},
        headers={"cache-control": "max-age=3600"},
    )
