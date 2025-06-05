"""
Data schemas for request/response validation using Pydantic.

These schemas define the structure and constraints of the data exchanged
within the application abstractions (e.g., API payloads, business entities).

Includes:
- DocxValidator: Schema for processing DOCX-related data.
- QdrantValidator: Schema for defining vector database entries.
"""
from typing import List, Dict, NamedTuple, Union, Optional

from src.abstractions import ApiEndPointProtocolFunction, AsyncApiEndpointProtocolFunction
from pydantic import BaseModel  # type: ignore
from .response_schemas import  FastApiGetResponse, FastApiPostResponse

class QdrantValidator(BaseModel):
    """class to validate Qdrant data against a schema
    attributes:
    id(str): uuid4 string version identifier
    vector(Dict[str, List[Any]]): dense vector  database entries
    payload(Dict[str, List[Any]]): string database entries
    """
    id: str
    vector: Dict[str, List[float]]
    payload: Dict[str, str]

class DocxValidator(BaseModel):
    ...


class EndpointSpec(NamedTuple):
    """
    FastAPI endpoint specification formating class
    """
    path: str
    handler: Union[ApiEndPointProtocolFunction, AsyncApiEndpointProtocolFunction]
    required_params: List[str]
    response_model: Optional[BaseModel] = None