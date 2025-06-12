"""
abstractions module
Domain module: defines core interfaces, validation contracts, and schemas.

This includes:
- Abstract interfaces for application behavior (e.g. AppInterface)
- Abstract classes for vector database client (e.g. VectorDBClientInterfaceAsync)
- Protocols for Duck Typing (e.g. ApiEndPointProtocolFunction)
"""

from .client_interfaces import VectorDataBaseClientInterfaceAsync
from .controller_protocols import  ApiEndPointProtocolFunction, AsyncApiEndpointProtocolFunction, protocol_checker
from .framework_interfaces import AppInterface


__all__ = [

    "VectorDataBaseClientInterfaceAsync",
    "protocol_checker",
    "ApiEndPointProtocolFunction",
    "AsyncApiEndpointProtocolFunction",
    "AppInterface",


]