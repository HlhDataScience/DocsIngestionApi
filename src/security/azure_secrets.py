
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import status, Security
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyHeader

from .api_keys import hash_key

KEY_VAULT_URL = "https://vault.azure.net"
API_KEY_PREFIX = "api-key-"

credentials =  DefaultAzureCredential()
secrets_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credentials)
api_key_header =  APIKeyHeader(name= "X-API-KEY",
                               auto_error = False)
async def store_key_in_vault(key_id: str, hashed_key: str, description: str, expire_in_days: Optional[int] = None) -> None:
    """
    Takes generated api keys and hashes and stores them into a secure azure vault secret.
    :param key_id:
    :param hashed_key:
    :param description:
    :param expire_in_days:
    :return:
    """
    from datetime import datetime, timedelta, timezone
    from azure.core.exceptions import HttpResponseError

    expires_on = None
    if expire_in_days:
        expires_on = datetime.now(timezone.utc) + timedelta(days=expire_in_days)

    try:
        secrets_client.set_secret(
            name=key_id,
            secret=hashed_key,
            expires_on=expires_on,
            tags= {
                "description": description,
                "type" : "api_key"
            }
        )
    except HttpResponseError as httpe:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failure to store api key: {str(httpe)}"
        )
async def validate_api_key(
        api_key: str = Security(api_key_header) #enable in production.
)-> str| None:
    """
    Validates the provided api key against the azure key vault secret.
    :param api_key: api key to validate
    :return: the api key validated
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )
    hashed_key = hash_key(api_key)
    key_id = f"{API_KEY_PREFIX}{hashed_key}"

    try:
        secret = secrets_client.get_secret(key_id)
        if secret.value == hashed_key:
            return api_key
    except HttpResponseError as _:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
