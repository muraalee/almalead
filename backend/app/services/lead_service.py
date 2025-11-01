"""
Lead service for business logic.
"""
import uuid
from typing import Optional, BinaryIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import LeadState
from app.models.lead import Lead
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate
from app.services.email_service import email_service
from app.utils.minio_storage import storage


class LeadService:
    """Service for lead business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.lead_repo = LeadRepository(db)
        self.storage = storage
        self.email_service = email_service

    async def create_lead(
        self,
        lead_data: LeadCreate,
        resume_file: BinaryIO,
        filename: str
    ) -> Lead:
        """
        Create a new lead with resume upload and email notifications.

        Args:
            lead_data: Lead creation data
            resume_file: Resume file object
            filename: Original filename

        Returns:
            Created Lead object
        """
        # Generate unique filename for storage
        file_extension = filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Upload resume to MinIO
        resume_url = self.storage.upload_file(resume_file, unique_filename)

        # Create lead in database
        lead = Lead(
            first_name=lead_data.first_name,
            last_name=lead_data.last_name,
            email=lead_data.email,
            resume_url=resume_url,
            state=LeadState.PENDING,
        )
        lead = self.lead_repo.create(lead)

        # Send emails asynchronously
        await self.email_service.send_prospect_confirmation(
            lead.email,
            lead.first_name
        )
        await self.email_service.send_attorney_notification(
            settings.ATTORNEY_EMAIL,
            lead.first_name,
            lead.last_name,
            lead.email,
            str(lead.id)
        )

        return lead

    def get_lead(self, lead_id: UUID) -> Optional[Lead]:
        """Get a lead by ID."""
        return self.lead_repo.get_by_id(lead_id)

    def get_all_leads(
        self,
        skip: int = 0,
        limit: int = 100,
        state: Optional[LeadState] = None
    ) -> tuple[list[Lead], int]:
        """Get all leads with pagination and optional filtering."""
        return self.lead_repo.get_all(skip, limit, state)

    def update_lead_state(self, lead_id: UUID, state: LeadState) -> Optional[Lead]:
        """Update lead state."""
        return self.lead_repo.update_state(lead_id, state)
