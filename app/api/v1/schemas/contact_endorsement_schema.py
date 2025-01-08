""" Pydantic schemas for contact endorsements. """

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ContactEndorsementCreate(BaseModel):
    """Schema for creating a new contact endorsement."""

    contact_id: int
    user_id: int
    community_id: int
    endorsed: bool = True
    rating: Optional[int]
    comment: Optional[str] = Field(None, max_length=500)


class ContactEndorsementUpdate(BaseModel):
    """Schema for updating an existing contact endorsement."""

    endorsed: Optional[bool]
    rating: Optional[int]
    comment: Optional[str] = Field(None, max_length=500)
    is_verified: Optional[bool]


class ContactEndorsementResponse(BaseModel):
    """Schema for contact endorsement responses."""

    id: int
    contact_id: int
    user_id: int
    community_id: int
    endorsed: bool
    rating: Optional[int]
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    verification_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
