"""
Authentication service.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_token_for_user(self, user: User) -> str:
        """
        Create an access token for a user.

        Args:
            user: User object

        Returns:
            JWT access token
        """
        token_data = {
            "sub": str(user.id),
            "email": user.email,
        }
        return create_access_token(token_data)
