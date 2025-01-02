""" This module contains schemas for role endpoints. """

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    """Schema for creating a new role."""

    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    permissions: str = Field(..., max_length=500)
    is_system_role: bool = False


class RoleUpdate(BaseModel):
    """Schema for updating an existing role."""

    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    permissions: Optional[str] = Field(None, max_length=500)
    is_system_role: Optional[bool]


class RoleResponse(BaseModel):
    """Schema for role responses."""

    id: int
    name: str
    description: Optional[str]
    permissions: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_system_role: bool

    model_config = ConfigDict(from_attributes=True)
