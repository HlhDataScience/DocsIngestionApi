"""
specs.py

API Endpoint Specifications Module

This module defines the endpoint specifications for a document management API.
It validates handler functions against protocol requirements and creates structured
endpoint configurations for FastAPI routing.

The module enforces that all handler functions conform to either AsyncApiEndpointProtocolFunction
or ApiEndPointProtocolFunction protocols to ensure consistent API behavior.

Endpoints:
    - /v1: Root endpoint providing API information
    - /uploadocs: Document upload endpoint (POST)
    - /docs: Retrieve uploaded document information (GET)

Raises:
    ValueError: If any handler function doesn't conform to the required protocols

Example:
    The endpoint specifications defined here can be used to configure FastAPI routes:

    ```python
    from specs import root_spec, post_documents_spec, get_docs_uploaded_spec

    app.add_api_route(
        root_spec.path,
        root_spec.handler,
        methods=root_spec.required_params
    )
    ```
"""


from src.abstractions import (
    AsyncApiEndpointProtocolFunction,
    ApiEndPointProtocolFunction,
    protocol_checker,
)
from src.models import (
    APIInfoResponse,
    EndpointSpec,
    FastApiGetResponse,
    FastApiPostResponse,
)
from .api_endpointfuncs import dev_get_post_docs_root, get_uploaded_docs_info, upload_docx

if not protocol_checker(
        fn_list= [dev_get_post_docs_root, upload_docx, get_uploaded_docs_info],
        protocols=(AsyncApiEndpointProtocolFunction,ApiEndPointProtocolFunction)
):
    raise ValueError(f"All the functions must conform to  {ApiEndPointProtocolFunction.__name__} or {AsyncApiEndpointProtocolFunction.__name__}")


dev_root_spec = EndpointSpec(
    path= "/",
    handler= dev_get_post_docs_root, # type: ignore
    required_params= ["GET"],
    response_model= APIInfoResponse,

)
pro_root_spec = EndpointSpec(
    path= "/",
    handler= dev_get_post_docs_root, # type: ignore
    required_params= ["GET"],
    response_model= APIInfoResponse,

)

post_documents_spec = EndpointSpec(
    path="/uploadocs",
    handler= upload_docx, # type: ignore
    required_params= ["POST"],
    response_model= FastApiPostResponse,

)

get_docs_uploaded_spec = EndpointSpec(
    path="/search",
    handler= get_uploaded_docs_info, # type: ignore
    required_params= ["GET"],
    response_model= FastApiGetResponse,
)