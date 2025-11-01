"""
Lead model for prospect submissions.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.enums import LeadState
from app.db.session import Base


class Lead(Base):
    """Lead model representing a prospect submission."""
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    resume_url = Column(String, nullable=False)
    state = Column(
        SQLEnum(LeadState, name="lead_state"),
        default=LeadState.PENDING,
        nullable=False,
        index=True
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Lead {self.email} - {self.state}>"
