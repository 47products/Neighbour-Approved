"""
Schema Module for Health Check Endpoint.

This module defines the Pydantic model used for the health check response.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """
    ## Health Check Response Schema.

    This schema defines the response structure for the `/health` endpoint.

    **Attributes:**

    - **status** (str): The status of the application (e.g., "ok").

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

    status: str
