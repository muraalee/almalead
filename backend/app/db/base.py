"""
Import all models here for Alembic to detect them.
"""
from app.db.session import Base  # noqa
from app.models.user import User  # noqa
from app.models.lead import Lead  # noqa
