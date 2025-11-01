"""
Integration tests for API endpoints.

Tests the complete API flow end-to-end including:
- Lead creation (public endpoint)
- Authentication
- Lead retrieval and management (protected endpoints)
"""
import pytest
from io import BytesIO
from unittest.mock import patch, AsyncMock

from app.core.enums import LeadState


class TestLeadCreationAPI:
    """Test public lead creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_lead_success(self, client, mock_storage):
        """Test successful lead creation with file upload."""
        with patch('app.services.lead_service.storage', mock_storage), \
             patch('app.services.lead_service.email_service') as mock_email:
            mock_email.send_prospect_confirmation = AsyncMock(return_value=True)
            mock_email.send_attorney_notification = AsyncMock(return_value=True)

            # Create lead with resume
            response = client.post(
                "/api/v1/leads",
                data={
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane.smith@example.com",
                },
                files={
                    "resume": ("resume.pdf", BytesIO(b"fake resume content"), "application/pdf")
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["first_name"] == "Jane"
            assert data["last_name"] == "Smith"
            assert data["email"] == "jane.smith@example.com"
            assert data["state"] == "PENDING"
            assert "resume_url" in data
            assert "id" in data

            # Verify emails were sent
            mock_email.send_prospect_confirmation.assert_called_once()
            mock_email.send_attorney_notification.assert_called_once()

    def test_create_lead_missing_fields(self, client):
        """Test lead creation with missing required fields."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Jane",
                # Missing last_name and email
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"fake resume content"), "application/pdf")
            }
        )

        assert response.status_code == 422  # Validation error

    def test_create_lead_invalid_email(self, client):
        """Test lead creation with invalid email format."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "not an email at all",  # Clearly invalid email
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"fake resume content"), "application/pdf")
            }
        )

        assert response.status_code == 422  # Validation error

    def test_create_lead_invalid_file_type(self, client):
        """Test lead creation with invalid file type."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com",
            },
            files={
                "resume": ("resume.exe", BytesIO(b"fake exe content"), "application/x-msdownload")
            }
        )

        assert response.status_code == 400
        assert "File type not allowed" in response.json()["detail"]

    def test_create_lead_no_resume(self, client):
        """Test lead creation without resume file."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com",
            }
        )

        assert response.status_code == 422  # Missing required file


class TestAuthenticationAPI:
    """Test authentication endpoints."""

    def test_login_success(self, client, db_session, sample_user_data):
        """Test successful login."""
        from app.models.user import User
        from app.core.security import get_password_hash

        # Create test user
        user = User(
            email=sample_user_data["email"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"],
        )
        db_session.add(user)
        db_session.commit()

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, db_session, sample_user_data):
        """Test login with wrong password."""
        from app.models.user import User
        from app.core.security import get_password_hash

        # Create test user
        user = User(
            email=sample_user_data["email"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"],
        )
        db_session.add(user)
        db_session.commit()

        # Try login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": "wrongpassword",
            }
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            }
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                # Missing password
            }
        )

        assert response.status_code == 422  # Validation error


class TestProtectedLeadEndpoints:
    """Test protected lead management endpoints."""

    @pytest.mark.asyncio
    async def test_list_leads_unauthorized(self, client):
        """Test listing leads without authentication."""
        response = client.get("/api/v1/leads")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 when no auth

    @pytest.mark.asyncio
    async def test_list_leads_success(self, client, auth_headers, db_session):
        """Test listing leads with authentication."""
        from app.models.lead import Lead

        # Create test leads
        for i in range(3):
            lead = Lead(
                first_name=f"User{i}",
                last_name="Test",
                email=f"user{i}@example.com",
                resume_url="http://test.com/resume.pdf",
                state=LeadState.PENDING,
            )
            db_session.add(lead)
        db_session.commit()

        response = client.get("/api/v1/leads", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["leads"]) == 3

    @pytest.mark.asyncio
    async def test_list_leads_with_state_filter(self, client, auth_headers, db_session):
        """Test listing leads filtered by state."""
        from app.models.lead import Lead

        # Create leads with different states
        for i in range(2):
            lead = Lead(
                first_name=f"Pending{i}",
                last_name="Test",
                email=f"pending{i}@example.com",
                resume_url="http://test.com/resume.pdf",
                state=LeadState.PENDING,
            )
            db_session.add(lead)

        for i in range(3):
            lead = Lead(
                first_name=f"Reached{i}",
                last_name="Test",
                email=f"reached{i}@example.com",
                resume_url="http://test.com/resume.pdf",
                state=LeadState.REACHED_OUT,
            )
            db_session.add(lead)
        db_session.commit()

        # Filter by PENDING
        response = client.get(
            "/api/v1/leads?state=PENDING",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(lead["state"] == "PENDING" for lead in data["leads"])

    @pytest.mark.asyncio
    async def test_list_leads_pagination(self, client, auth_headers, db_session):
        """Test lead list pagination."""
        from app.models.lead import Lead

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

        # First page
        response = client.get(
            "/api/v1/leads?skip=0&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["leads"]) == 10

        # Second page
        response = client.get(
            "/api/v1/leads?skip=10&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["leads"]) == 5

    @pytest.mark.asyncio
    async def test_get_lead_by_id_unauthorized(self, client, db_session):
        """Test getting lead by ID without authentication."""
        from app.models.lead import Lead

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

        response = client.get(f"/api/v1/leads/{lead.id}")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 when no auth

    @pytest.mark.asyncio
    async def test_get_lead_by_id_success(self, client, auth_headers, db_session):
        """Test getting lead by ID with authentication."""
        from app.models.lead import Lead

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

        response = client.get(f"/api/v1/leads/{lead.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(lead.id)
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john@example.com"
        assert data["state"] == "PENDING"

    @pytest.mark.asyncio
    async def test_get_lead_not_found(self, client, auth_headers):
        """Test getting non-existent lead."""
        from uuid import uuid4

        fake_id = uuid4()
        response = client.get(f"/api/v1/leads/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_lead_state_unauthorized(self, client, db_session):
        """Test updating lead state without authentication."""
        from app.models.lead import Lead

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

        response = client.patch(
            f"/api/v1/leads/{lead.id}/state",
            json={"state": "REACHED_OUT"}
        )
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 when no auth

    @pytest.mark.asyncio
    async def test_update_lead_state_success(self, client, auth_headers, db_session):
        """Test updating lead state from PENDING to REACHED_OUT."""
        from app.models.lead import Lead

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

        response = client.patch(
            f"/api/v1/leads/{lead.id}/state",
            json={"state": "REACHED_OUT"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "REACHED_OUT"
        assert data["id"] == str(lead.id)

    @pytest.mark.asyncio
    async def test_update_lead_state_invalid(self, client, auth_headers, db_session):
        """Test updating lead state with invalid state value."""
        from app.models.lead import Lead

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

        response = client.patch(
            f"/api/v1/leads/{lead.id}/state",
            json={"state": "INVALID_STATE"},
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error


class TestHealthEndpoints:
    """Test utility endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestEndToEndFlow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_lead_workflow(self, client, auth_headers, db_session, mock_storage):
        """Test complete lead workflow: create → list → get → update state."""
        with patch('app.services.lead_service.storage', mock_storage), \
             patch('app.services.lead_service.email_service') as mock_email:
            mock_email.send_prospect_confirmation = AsyncMock(return_value=True)
            mock_email.send_attorney_notification = AsyncMock(return_value=True)

            # Step 1: Create lead (public)
            create_response = client.post(
                "/api/v1/leads",
                data={
                    "first_name": "Alice",
                    "last_name": "Johnson",
                    "email": "alice.johnson@example.com",
                },
                files={
                    "resume": ("resume.pdf", BytesIO(b"fake resume"), "application/pdf")
                }
            )
            assert create_response.status_code == 201
            lead_data = create_response.json()
            lead_id = lead_data["id"]
            assert lead_data["state"] == "PENDING"

            # Step 2: List leads (protected)
            list_response = client.get("/api/v1/leads", headers=auth_headers)
            assert list_response.status_code == 200
            assert list_response.json()["total"] >= 1

            # Step 3: Get specific lead (protected)
            get_response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
            assert get_response.status_code == 200
            assert get_response.json()["email"] == "alice.johnson@example.com"

            # Step 4: Update state to REACHED_OUT (protected)
            update_response = client.patch(
                f"/api/v1/leads/{lead_id}/state",
                json={"state": "REACHED_OUT"},
                headers=auth_headers
            )
            assert update_response.status_code == 200
            assert update_response.json()["state"] == "REACHED_OUT"

            # Step 5: Verify state was updated
            verify_response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
            assert verify_response.status_code == 200
            assert verify_response.json()["state"] == "REACHED_OUT"
