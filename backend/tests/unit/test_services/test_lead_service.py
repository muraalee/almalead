"""
Unit tests for LeadService.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from io import BytesIO

from app.services.lead_service import LeadService
from app.models.lead import Lead
from app.schemas.lead import LeadCreate
from app.core.enums import LeadState


@pytest.mark.asyncio
async def test_create_lead(db_session, mock_storage, sample_lead_data):
    """Test lead creation with file upload and emails."""
    # Mock email service
    with patch('app.services.lead_service.email_service') as mock_email:
        mock_email.send_prospect_confirmation = AsyncMock(return_value=True)
        mock_email.send_attorney_notification = AsyncMock(return_value=True)

        # Create lead
        lead_service = LeadService(db_session)
        lead_service.storage = mock_storage

        lead_data = LeadCreate(**sample_lead_data)
        resume_file = BytesIO(b"fake resume content")

        lead = await lead_service.create_lead(lead_data, resume_file, "resume.pdf")

        # Assertions
        assert lead.first_name == sample_lead_data["first_name"]
        assert lead.last_name == sample_lead_data["last_name"]
        assert lead.email == sample_lead_data["email"]
        assert lead.state == LeadState.PENDING
        assert lead.resume_url.startswith("http://test-storage/")

        # Verify emails were sent
        mock_email.send_prospect_confirmation.assert_called_once()
        mock_email.send_attorney_notification.assert_called_once()


def test_get_lead(db_session):
    """Test getting a lead by ID."""
    # Create test lead
    lead = Lead(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        resume_url="http://test.com/resume.pdf",
        state=LeadState.PENDING,
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    # Get lead
    lead_service = LeadService(db_session)
    retrieved_lead = lead_service.get_lead(lead.id)

    assert retrieved_lead is not None
    assert retrieved_lead.id == lead.id
    assert retrieved_lead.email == "john@example.com"


def test_get_lead_not_found(db_session):
    """Test getting non-existent lead."""
    from uuid import uuid4

    lead_service = LeadService(db_session)
    lead = lead_service.get_lead(uuid4())

    assert lead is None


def test_get_all_leads(db_session):
    """Test getting all leads."""
    # Create test leads
    for i in range(5):
        lead = Lead(
            first_name=f"User{i}",
            last_name="Test",
            email=f"user{i}@example.com",
            resume_url="http://test.com/resume.pdf",
            state=LeadState.PENDING,
        )
        db_session.add(lead)
    db_session.commit()

    # Get all leads
    lead_service = LeadService(db_session)
    leads, total = lead_service.get_all_leads()

    assert total == 5
    assert len(leads) == 5


def test_get_all_leads_with_filter(db_session):
    """Test getting leads with state filter."""
    # Create leads with different states
    for i in range(3):
        lead = Lead(
            first_name=f"User{i}",
            last_name="Test",
            email=f"user{i}@example.com",
            resume_url="http://test.com/resume.pdf",
            state=LeadState.PENDING,
        )
        db_session.add(lead)

    for i in range(2):
        lead = Lead(
            first_name=f"UserR{i}",
            last_name="Test",
            email=f"userr{i}@example.com",
            resume_url="http://test.com/resume.pdf",
            state=LeadState.REACHED_OUT,
        )
        db_session.add(lead)
    db_session.commit()

    # Get only PENDING leads
    lead_service = LeadService(db_session)
    leads, total = lead_service.get_all_leads(state=LeadState.PENDING)

    assert total == 3
    assert len(leads) == 3
    assert all(lead.state == LeadState.PENDING for lead in leads)


def test_update_lead_state(db_session):
    """Test updating lead state."""
    # Create test lead
    lead = Lead(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        resume_url="http://test.com/resume.pdf",
        state=LeadState.PENDING,
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    # Update state
    lead_service = LeadService(db_session)
    updated_lead = lead_service.update_lead_state(lead.id, LeadState.REACHED_OUT)

    assert updated_lead is not None
    assert updated_lead.state == LeadState.REACHED_OUT


def test_pagination(db_session):
    """Test lead pagination."""
    # Create 15 test leads
    for i in range(15):
        lead = Lead(
            first_name=f"User{i}",
            last_name="Test",
            email=f"user{i}@example.com",
            resume_url="http://test.com/resume.pdf",
            state=LeadState.PENDING,
        )
        db_session.add(lead)
    db_session.commit()

    # Test pagination
    lead_service = LeadService(db_session)

    # First page
    leads, total = lead_service.get_all_leads(skip=0, limit=10)
    assert total == 15
    assert len(leads) == 10

    # Second page
    leads, total = lead_service.get_all_leads(skip=10, limit=10)
    assert total == 15
    assert len(leads) == 5
