"""
Health Check Endpoint Module.

This module defines the `/health` endpoint which allows clients to verify the application's
health status.
"""

from fastapi import APIRouter
from app.api.v1.schemas.health import HealthResponse

router = APIRouter(tags=["Health"], responses={404: {"description": "Not Found"}})


@router.get("/", response_model=HealthResponse, summary="Health Check Endpoint")
def health_check() -> HealthResponse:
    """
    ## Check Health Status.

    This endpoint checks the health status of the application.

    **Returns:**
    - **HealthResponse:** A JSON object containing a simple status message.

    **Example:**

    **Request:**
    ```http
    GET /api/v1/health
    ```

    **Response:**
    ```json
    {
        "status": "ok"
    }
    ```
    """
    return HealthResponse(status="ok")
