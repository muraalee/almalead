"""seed attorney user

Revision ID: 2c65a210a18f
Revises: 001
Create Date: 2025-11-01 13:38:29.549698

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c65a210a18f'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed attorney user from environment variables."""
    from app.core.config import settings
    from app.core.security import get_password_hash

    # Get database connection
    conn = op.get_bind()

    # Check if attorney user already exists
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM users WHERE email = :email"),
        {"email": settings.ATTORNEY_EMAIL}
    )
    count = result.scalar()

    if count == 0:
        # Ensure password is within bcrypt limits (72 bytes)
        password = settings.ATTORNEY_PASSWORD[:72]
        hashed_password = get_password_hash(password)

        # Insert attorney user
        conn.execute(
            sa.text("""
                INSERT INTO users (id, email, hashed_password, first_name, last_name, created_at, updated_at)
                VALUES (:id, :email, :hashed_password, :first_name, :last_name, :created_at, :updated_at)
            """),
            {
                "id": str(uuid.uuid4()),
                "email": settings.ATTORNEY_EMAIL,
                "hashed_password": hashed_password,
                "first_name": settings.ATTORNEY_FIRST_NAME,
                "last_name": settings.ATTORNEY_LAST_NAME,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        conn.commit()
        print(f"✓ Seeded attorney user: {settings.ATTORNEY_EMAIL}")
    else:
        print(f"✓ Attorney user already exists: {settings.ATTORNEY_EMAIL}")


def downgrade() -> None:
    """Remove seeded attorney user."""
    from app.core.config import settings

    # Get database connection
    conn = op.get_bind()

    # Delete attorney user
    conn.execute(
        sa.text("DELETE FROM users WHERE email = :email"),
        {"email": settings.ATTORNEY_EMAIL}
    )
    conn.commit()
    print(f"✓ Removed attorney user: {settings.ATTORNEY_EMAIL}")
