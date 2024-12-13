"""
This module defines the `/info` endpoint for the Neighbour Approved backend application.

It uses FastAPI's `APIRouter` to create a modular and reusable router instance.
The `/info` endpoint provides basic information about the application, such as its name and version.
"""

from fastapi import APIRouter
from app.api.v1.schemas.info import InfoResponse

# Initialize the APIRouter
router = APIRouter(
    prefix="/info", tags=["Info"], responses={404: {"description": "Not Found"}}
)


@router.get("/", response_model=InfoResponse, summary="Get Application Info")
def get_info() -> InfoResponse:
    """
    ## Retrieve Basic Application Information.

    This endpoint returns the application's **name** and current **version**.

    **Returns:**
    - **InfoResponse:** A Pydantic model containing the application's name and version.

    **Example:**

    **Request:**
    ```http
    GET /api/v1/info
    ```

    **Response:**
    ```json
    {
        "name": "Neighbour Approved",
        "version": "0.1.0"
    }
    ```
    """
    return InfoResponse(name="Neighbour Approved", version="0.1.0")
