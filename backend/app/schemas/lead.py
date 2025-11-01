"""
Lead schemas.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict

from app.core.enums import LeadState


class LeadBase(BaseModel):
    """Base lead schema."""
    first_name: str
    last_name: str
    email: EmailStr


class LeadCreate(LeadBase):
    """Lead creation schema (from form submission)."""
    pass


class LeadResponse(LeadBase):
    """Lead response schema."""
    id: UUID
    resume_url: str
    state: LeadState
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadStateUpdate(BaseModel):
    """Lead state update schema."""
    state: LeadState


class LeadListResponse(BaseModel):
    """Lead list response schema with pagination info."""
    total: int
    leads: list[LeadResponse]
