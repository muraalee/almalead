"""
Unit tests for AuthService.
"""
import pytest
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.security import get_password_hash


def test_authenticate_user_success(db_session):
    """Test successful user authentication."""
    # Create test user
    password = "testpassword123"
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash(password),
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()

    # Authenticate
    auth_service = AuthService(db_session)
    authenticated_user = auth_service.authenticate_user("test@example.com", password)

    assert authenticated_user is not None
    assert authenticated_user.email == "test@example.com"


def test_authenticate_user_wrong_password(db_session):
    """Test authentication with wrong password."""
    # Create test user
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("correctpassword"),
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()

    # Try to authenticate with wrong password
    auth_service = AuthService(db_session)
    authenticated_user = auth_service.authenticate_user("test@example.com", "wrongpassword")

    assert authenticated_user is None


def test_authenticate_user_not_exists(db_session):
    """Test authentication with non-existent user."""
    auth_service = AuthService(db_session)
    authenticated_user = auth_service.authenticate_user("nonexistent@example.com", "password")

    assert authenticated_user is None


def test_create_token_for_user(db_session):
    """Test JWT token creation."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    auth_service = AuthService(db_session)
    token = auth_service.create_token_for_user(user)

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
