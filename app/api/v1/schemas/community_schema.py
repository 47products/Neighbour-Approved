""" This module contains schemas for the community model. """

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CommunityCreate(BaseModel):
    """Schema for creating a new community."""

    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    privacy_level: str = Field(default="public")
    owner_id: int


class CommunityUpdate(BaseModel):
    """Schema for updating an existing community."""

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    privacy_level: Optional[str]
    is_active: Optional[bool]


class CommunityResponse(BaseModel):
    """Schema for community responses."""

    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    owner_id: int
    is_active: bool
    privacy_level: str

    model_config = ConfigDict(from_attributes=True)
