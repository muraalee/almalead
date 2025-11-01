"""
Lead repository for database operations.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import LeadState
from app.models.lead import Lead


class LeadRepository:
    """Repository for Lead database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, lead: Lead) -> Lead:
        """Create a new lead."""
        self.db.add(lead)
        try:
            self.db.commit()
            self.db.refresh(lead)
        except Exception:
            self.db.rollback()
            raise
        return lead

    def get_by_id(self, lead_id: UUID) -> Optional[Lead]:
        """Get lead by ID."""
        return self.db.query(Lead).filter(Lead.id == lead_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        state: Optional[LeadState] = None
    ) -> tuple[list[Lead], int]:
        """
        Get all leads with pagination and optional filtering.

        Returns:
            Tuple of (list of leads, total count)
        """
        query = self.db.query(Lead)

        if state:
            query = query.filter(Lead.state == state)

        total = query.count()
        leads = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()

        return leads, total

    def update_state(self, lead_id: UUID, state: LeadState) -> Optional[Lead]:
        """Update lead state."""
        lead = self.get_by_id(lead_id)
        if lead:
            lead.state = state
            lead.updated_at = datetime.now(timezone.utc)
            try:
                self.db.commit()
                self.db.refresh(lead)
            except Exception:
                self.db.rollback()
                raise
        return lead
