"""
secrets.py
~~~~~~~~~~~~~~~~~

This module provides functionality for securely storing and validating API keys using Azure Key Vault.
It serves as the security layer for the DocumentalIngestAPI, enabling secure storage of API key credentials
and validation mechanisms for both administrative and user-level access.

Key Features:
------------
- Secure storage of hashed API keys in Azure Key Vault
- Optional expiration for stored secrets
- Admin-level API key validation using a fixed key ID
- User-level API key validation by checking all available keys in the vault
- Integration with FastAPI's dependency injection and security headers

Dependencies:
-------------
- Azure Identity and Key Vault SDK for authentication and secret management
- FastAPI for API key extraction and HTTP exception handling
- `hash_key` from the `.api_keys` module to validate key integrity
- `.env.vault` for loading the Azure Key Vault connection string

Usage:
------
This module is used in conjunction with FastAPI endpoints to protect access to routes via API keys.
It supports distinguishing between admin-only access and general user access.

Examples:
---------
- `validate_admin_api_key("admin-key-id")` to protect sensitive routes
- `validate_users_api_key()` for general authenticated access
- `store_key_in_vault()` to register new API keys (e.g., from an admin endpoint)

"""
from collections.abc import Callable
import os
from typing import Optional
from urllib.parse import unquote

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import status, Security
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyHeader

from .api_keys import hash_key


KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_CONNECTION_STRING")

# Set up Azure Key Vault client
credentials = DefaultAzureCredential()
secrets_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credentials)

# Define FastAPI security scheme
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def store_key_in_vault(
        key_id: str,
        hashed_key: str,
        description: str,
        expire_in_days: Optional[int] = None
) -> None:
    """
    Stores a hashed API key in Azure Key Vault under the given key ID with optional expiration.

    Args:
        key_id (str): The unique identifier to store the secret under.
        hashed_key (str): The hashed API key to store.
        description (str): A short description of the key.
        expire_in_days (Optional[int]): Optional expiration in days.

    Raises:
        HTTPException: If the secret fails to be stored due to an Azure or network error.
    """
    from datetime import datetime, timedelta, timezone
    from azure.core.exceptions import HttpResponseError

    expires_on = None
    if expire_in_days:
        expires_on = datetime.now(timezone.utc) + timedelta(days=expire_in_days)

    try:
        secrets_client.set_secret(
            name=key_id,
            value=hashed_key,
            expires_on=expires_on,
            tags={
                "description": description,
                "type": "api_key"
            }
        )
    except HttpResponseError as httpe:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failure to store API key: {str(httpe)}"
        )

def validate_admin_api_key(required_id_key: str) -> Callable:
    """
    Validates that the incoming API key matches the stored admin API key.

    Args:
        required_id_key (str): The ID of the admin key to validate against.

    Returns:
        Callable: A FastAPI dependency function for route protection.
    """
    async def dependency(api_key: str = Security(api_key_header)) -> str | bool | None:
        stored_hashed_key = secrets_client.get_secret(name=required_id_key)
        if not stored_hashed_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin key not found"
            )
        corrected_api_key = unquote(api_key)  #This line is essential as we need to reparse the api_key to read the salt and pepper characters.
        if hash_key(corrected_api_key) != stored_hashed_key.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid admin key"
            )
        return api_key
    return dependency

def validate_users_api_key() -> Callable:
    """
    Validates that the incoming API key matches any of the keys stored in Azure Key Vault.

    Returns:
        Callable: A FastAPI dependency function for user-level route protection.
    """
    async def dependency(api_key: str = Security(api_key_header)) -> str | None:
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key not found"
            )

        # List and check against all stored API keys
        corrected_api_key = unquote(api_key) #This line is essential as we need to reparse the api_key to read the salt and pepper characters.
        secret_names = secrets_client.list_properties_of_secrets()
        secret_names = {i.name for i in secret_names}
        for key_id in secret_names:
            stored_hashed_key = secrets_client.get_secret(name=key_id)
            if stored_hashed_key and hash_key(corrected_api_key) == stored_hashed_key.value:
                return api_key

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or unauthorized API key"
        )
    return dependency
