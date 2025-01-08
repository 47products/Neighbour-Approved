"""
This module defines Pydantic schemas for the `/info` endpoint.

Schemas are used for data validation and serialization/deserialization of request and
response bodies.
"""

from pydantic import BaseModel, Field


class InfoResponse(BaseModel):
    """
    ## Schema for the `/info` Endpoint Response.

    This schema defines the response structure for the `/info` endpoint.

    **Attributes:**

    - **name** (str): The name of the application.
    - **version** (str): The current version of the application.

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

    name: str = Field(..., description="The name of the application.")
    version: str = Field(..., description="The current version of the application.")
