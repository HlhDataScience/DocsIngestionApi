"""
security_schemas.py

This module provides a pydantic BaseModel for security keys.
"""
from typing import Optional

from pydantic import BaseModel, Field


class ApiKeyGenerationRequest(BaseModel):
    key_id: str = Field(..., description="Nombre del secreto. Muy importante que este escrito del siguiente modo: pro-nombredepartamente-nombre-colección")
    description: str
    expire_in_days: Optional[int] = None