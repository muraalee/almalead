"""
Lead API endpoints.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.enums import LeadState
from app.db.session import get_db
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadResponse, LeadStateUpdate, LeadListResponse
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


# Form dependency to create Pydantic model from form data
def lead_form_data(
    first_name: Annotated[str, Form(...)],
    last_name: Annotated[str, Form(...)],
    email: Annotated[str, Form(...)],
) -> LeadCreate:
    """
    Dependency to parse form data into LeadCreate Pydantic model.

    This provides strong typing and validation for multipart/form-data.

    Args:
        first_name: Prospect's first name
        last_name: Prospect's last name
        email: Prospect's email (validated by Pydantic)

    Returns:
        Validated LeadCreate model

    Raises:
        HTTPException: If validation fails (handled by FastAPI)
    """
    try:
        return LeadCreate(
            first_name=first_name,
            last_name=last_name,
            email=email
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )


# File validation helper
def validate_resume_file(file: UploadFile) -> None:
    """Validate resume file type and size."""
    # Check file extension
    if not any(file.filename.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Check file size (this is approximate since we haven't read the file yet)
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
        )


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: Annotated[LeadCreate, Depends(lead_form_data)],
    resume: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)]
) -> LeadResponse:
    """
    Create a new lead (public endpoint - no authentication required).

    This endpoint uses a dependency to convert form data into a strongly-typed
    Pydantic model, providing automatic validation and better type safety.

    Args:
        lead_data: Validated lead data from form (first_name, last_name, email)
        resume: Resume file (PDF, DOC, or DOCX, max 10MB)
        db: Database session

    Returns:
        Created lead with PENDING state

    Raises:
        HTTPException: If validation fails or file is invalid
    """
    # Validate file
    validate_resume_file(resume)

    # Create lead
    lead_service = LeadService(db)
    lead = await lead_service.create_lead(lead_data, resume.file, resume.filename)

    return LeadResponse.model_validate(lead)


@router.get("", response_model=LeadListResponse)
def get_leads(
    skip: int = 0,
    limit: int = 100,
    state: Optional[LeadState] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LeadListResponse:
    """
    Get all leads with pagination and optional filtering (protected endpoint).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        state: Optional state filter
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of leads with total count
    """
    lead_service = LeadService(db)
    leads, total = lead_service.get_all_leads(skip, limit, state)

    return LeadListResponse(
        total=total,
        leads=[LeadResponse.model_validate(lead) for lead in leads]
    )


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LeadResponse:
    """
    Get a specific lead by ID (protected endpoint).

    Args:
        lead_id: Lead UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Lead details

    Raises:
        HTTPException: If lead not found
    """
    lead_service = LeadService(db)
    lead = lead_service.get_lead(lead_id)

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    return LeadResponse.model_validate(lead)


@router.patch("/{lead_id}/state", response_model=LeadResponse)
def update_lead_state(
    lead_id: UUID,
    state_update: LeadStateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LeadResponse:
    """
    Update lead state (protected endpoint).

    Args:
        lead_id: Lead UUID
        state_update: New state
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated lead

    Raises:
        HTTPException: If lead not found
    """
    lead_service = LeadService(db)
    lead = lead_service.update_lead_state(lead_id, state_update.state)

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    return LeadResponse.model_validate(lead)
