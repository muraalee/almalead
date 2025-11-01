"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-11-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if enum already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)

    # Create lead_state enum only if it doesn't exist
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lead_state')"
    ))
    enum_exists = result.scalar()

    if not enum_exists:
        op.execute("CREATE TYPE lead_state AS ENUM ('PENDING', 'REACHED_OUT')")

    # Create users table only if it doesn't exist
    if 'users' not in inspector.get_table_names():
        op.create_table(
            'users',
            sa.Column('id', UUID(as_uuid=True), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('hashed_password', sa.String(), nullable=False),
            sa.Column('first_name', sa.String(), nullable=False),
            sa.Column('last_name', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create leads table only if it doesn't exist
    if 'leads' not in inspector.get_table_names():
        # Use raw SQL to avoid SQLAlchemy trying to auto-create the enum
        op.execute("""
            CREATE TABLE leads (
                id UUID PRIMARY KEY,
                first_name VARCHAR NOT NULL,
                last_name VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                resume_url VARCHAR NOT NULL,
                state lead_state NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """)
        op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)
        op.create_index(op.f('ix_leads_state'), 'leads', ['state'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_leads_state'), table_name='leads')
    op.drop_index(op.f('ix_leads_email'), table_name='leads')
    op.drop_table('leads')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.execute('DROP TYPE lead_state')
