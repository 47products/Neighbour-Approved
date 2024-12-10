"""
This module defines Pydantic schemas for the `/info` endpoint.

Schemas are used for data validation and serialization/deserialization of request and
response bodies.
"""

from pydantic import BaseModel


class InfoResponse(BaseModel):
    """
    Schema for the `/info` endpoint response.

    Attributes:
        name (str): The name of the application.
        version (str): The current version of the application.
    """

    name: str
    version: str
