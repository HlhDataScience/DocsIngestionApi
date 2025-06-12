"""
specs_schemas.py

This module defines structured schemas for FastAPI endpoint specifications.
It provides a standardized way to configure API endpoints with type-safe
handler functions, request parameters, and response models.

The module enforces protocol compliance by requiring handler functions to
implement either ApiEndPointProtocolFunction or AsyncApiEndpointProtocolFunction,
ensuring consistent API behavior across all endpoints.

Key Features:
    - Structured endpoint configuration using NamedTuple
    - Protocol-based handler function validation
    - Support for both sync and async endpoint handlers
    - Type-safe response model specification
    - HTTP method parameter validation

Classes:
    EndpointSpec: Main specification class for FastAPI endpoint configuration

Usage:
    This module is used to create structured endpoint specifications that can
    be consumed by FastAPI route registration systems or API documentation
    generators.
"""

from typing import List, NamedTuple, Optional, Union

from src.abstractions import (
    ApiEndPointProtocolFunction,
    AsyncApiEndpointProtocolFunction,
)
from .response_schemas import (
    APIInfoResponse,
    FastApiGetResponse,
    FastApiPostResponse,
)
class EndpointSpec(NamedTuple):
    """
    FastAPI endpoint specification formating class
    """
    path: str
    handler: Union[ApiEndPointProtocolFunction, AsyncApiEndpointProtocolFunction]
    required_params: List[str]
    response_model: Optional[Union[type[FastApiGetResponse], type[FastApiPostResponse], type[APIInfoResponse]]]