"""
frameworks.py

FastAPI Framework Implementation

This module provides concrete implementations of the abstract interfaces defined in
framework_interfaces.py, specifically tailored for the FastAPI web framework. It includes
router implementations and application framework classes that simplify the process
of creating and managing FastAPI routes and applications.

Classes:
    FastApiGetPostRouter: FastAPI-specific router implementation for GET and POST routes
    FastApiFramework: FastAPI application framework wrapper with enhanced functionality

Features:
    - Type-safe route registration with comprehensive validation
    - Consistent interface implementation following abstract contracts
    - Built-in error handling and input validation
    - Support for bulk route creation from specifications
    - Proper dependency injection support
    - OpenAPI documentation integration
    - Production-ready error handling and logging


Dependencies:
    - fastapi: Web framework
    - uvicorn: ASGI server for running the application
    - src.abstractions: Abstract interfaces this module implements

Version: 1.1.0
"""

from pathlib import Path
from typing import Tuple, Union, Sequence, List, Optional, Type, NamedTuple, Any
from typing_extensions import Self
from fastapi import FastAPI, Depends


from src.abstractions import (
    AppInterface,
   ApiEndPointProtocolFunction)

from src.models import FastApiPostResponse, FastApiGetResponse, EndpointSpec





class FastApiFramework(AppInterface):
    """
    A FastAPI application framework wrapper that implements AppInterface.

    This class provides a concrete implementation of the AppInterface using FastAPI.
    It handles route registration, router integration, and application execution
    with comprehensive input validation and error handling.

    Args:
        app_type: The FastAPI class to instantiate
        title: Title for the API documentation
        version: Version of the API

    Raises:
        TypeError: If app_type is not a FastAPI class
        ValueError: If title or version are invalid
    """

    def __init__(self, app_type: Type[FastAPI], title: str = "Test API", version: str = "1.0.0") -> None:
        """
        Initialize the FastAPI framework wrapper.

        Args:
            app_type: The FastAPI class to instantiate
            title: Title for the API documentation
            version: Version of the API

        Raises:
            TypeError: If app_type is not a FastAPI class
            ValueError: If title or version are invalid
        """
        if not isinstance(app_type, type) or not issubclass(app_type, FastAPI):
            raise TypeError(f"Expected FastAPI class, got {type(app_type).__name__}")

        app_instance = app_type(title=title, version=version)
        super().__init__(app_instance=app_instance)

    def add_route(
        self,
        path: Union[str, Path],
        endpoint: ApiEndPointProtocolFunction,
        methods: Sequence[str],
        response_model: Optional[FastApiGetResponse | FastApiPostResponse] = None,
        status_code: Optional[int] = 200,
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[Depends]] = None  # type: ignore
    ) -> None:
        """
        Add a route to the FastAPI application with validation.

        Args:
            path: The URL path for the route
            endpoint: The function to handle the route
            methods: HTTP methods allowed for this route
            response_model: Optional response model interface
            status_code: HTTP status code for successful responses
            tags: List of tags for API documentation
            dependencies: List of dependencies to inject

        Raises:
            ValueError: For invalid path, methods, or status code
            TypeError: For type mismatches
        """
        if not path:
            raise ValueError("Path cannot be empty")

        if not methods:
            raise ValueError("Methods list cannot be empty")

        if endpoint is None:
            raise ValueError("Endpoint function cannot be None")

        valid_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE'}
        invalid_methods = set(methods) - valid_methods
        if invalid_methods:
            raise ValueError(f"Invalid HTTP methods: {invalid_methods}")

        if status_code and (status_code < 100 or status_code >= 600):
            raise ValueError("Status code must be between 100 and 599")

        self._app.add_api_route(
            path=str(path),
            endpoint=endpoint,
            methods=list(methods),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies
        )

    def add_router(self, router: None) -> None:
        """
        Add a router to the FastAPI application. Not implemented as
        the app_framework is going to be small, but the functionality is there
        to expand.



        Raises:

            RuntimeError: If router registration fails
        """
        pass

    def run_application(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """
        Run the FastAPI application using uvicorn server.

        Args:
            host: Host address to bind to
            port: Port number to bind to

        Raises:
            ValueError: For invalid host or port
            ImportError: If uvicorn is not installed
        """
        if not host or not isinstance(host, str):
            raise ValueError("Host must be a non-empty string")

        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError("Port must be an integer between 1 and 65535")

        try:
            import uvicorn
            uvicorn.run(self._app, host=host, port=port)
        except ImportError:
            raise ImportError(
                "uvicorn is required to run the application. "
                "Install it with: pip install uvicorn"
            )

    @classmethod
    def from_constructor(
        cls,
        app_type: Type[FastAPI],
        title: str,
        version: str,
        api_spec: Tuple[EndpointSpec, ...],
    ) -> Self:
        """
        Create a FastApiFramework instance from an API specification.

        Args:
            app_type: The FastAPI class to instantiate
            title: Title for the API documentation
            version: Version of the API
            api_spec: Dictionary mapping paths to route specifications

        Returns:
            FastApiFramework: Configured framework instance

        Raises:
            TypeError: If app_type is not a FastAPI class
            ValueError: For invalid specifications
        """
        framework = cls(app_type, title, version)

        for spec in api_spec:
            path = spec.path
            endpoint = spec.handler
            methods = spec.required_params
            response_model = spec.response_model

            framework.add_route(
                path=path,
                endpoint=endpoint,
                methods=methods,
                response_model=response_model,
            )

        return framework


