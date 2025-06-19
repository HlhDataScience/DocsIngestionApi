"""
security_schemas.py

This module provides a pydantic BaseModel for security keys.
"""
from typing import Optional

from pydantic import BaseModel


class ApiKeyGenerationRequest(BaseModel):
    description: str
    expire_in_days: Optional[int] = None