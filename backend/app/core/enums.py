"""
Enums for the application.
"""
from enum import Enum


class LeadState(str, Enum):
    """Lead state enum - extensible for future states."""
    PENDING = "PENDING"
    REACHED_OUT = "REACHED_OUT"
    # Future extensibility:
    # QUALIFIED = "QUALIFIED"
    # REJECTED = "REJECTED"
    # CONVERTED = "CONVERTED"
