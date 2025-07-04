"""
response_schemas.py

Data schemas for request/response validation using Pydantic.

These schemas define the structure and constraints of the data exchanged
within the application abstractions (e.g., API payloads, business entities).

Includes:
- FastApiPostResponse: Schema for processing POST HTTP request responses.
- FastApiGetResponse: Schema for processing GET HTTP request responses.
"""

from typing import Any

from pydantic import BaseModel  # type: ignore


class APIInfoResponse(BaseModel):
    """
    APIInfoResponse

    A class that represents information about the API, including a message,
    description, version, and available endpoints.

    Attributes:
        message (str): A brief message about the API.
        description (str): A detailed description of the API.
        version (float): The version number of the API.
        endpoints (Dict[str, str]): A dictionary mapping endpoint names to their URLs.
    """

    message: str
    description: str
    version: str
    endpoints: dict[str, str]

class FastApiPostResponse(BaseModel):
    status_code: int
    message: str
    content: dict[str, Any]

class FastApiGetResponse(BaseModel):
    status_code: int
    message: str
    content: dict[str, Any]


