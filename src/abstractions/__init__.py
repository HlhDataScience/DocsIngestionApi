"""
Domain module: defines core interfaces, validation contracts, and schemas.

This includes:
- Abstract interfaces for application behavior (e.g. AppInterface)
- Input/output validation adapters using Pydantic
- Protocols for controller endpoints
- Core data schemas used across the app_framework
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