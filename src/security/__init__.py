"""
security

This module contains the security mesuares design for the IngestaDocumental API to avoid security risk.
"""
from fastapi.openapi.models import APIKey

from .api_keys import generate_api_key, hash_key
from .azure_secrets import api_key_header,API_KEY_PREFIX, store_key_in_vault, validate_api_key

__all__ = [
    "API_KEY_PREFIX",
    "api_key_header",
    "generate_api_key",
    "hash_key",
    "store_key_in_vault",
    "validate_api_key",
]