"""
framework_interfaces.py

Abstract interfaces defining the core application behavior and data validation contracts.

This module contains the abstract base classes that define the contracts for web application
frameworks and routers. These interfaces ensure consistent behavior across different
implementations and provide a clean separation between the abstraction layer and
concrete implementations.

Classes:
    AppInterface: Interface for web application adapters (e.g., FastAPI, Flask)

Features:
    - Framework-agnostic application interface
    - Support for dependency injection and response models
    - Factory method pattern for bulk route creation
    - Type-safe method signatures with comprehensive documentation
    - Input validation and error handling contracts

Usage Example:
    # Implement the interfaces for your specific framework
    class MyAppFramework(AppInterface):
        def add_route(self, path, endpoint, methods, **kwargs):
            # Your implementation here
            pass

        def run_application(self, host, port):
            # Your implementation here
            pass

Version: 1.1.0
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel  # type: ignore

from src.abstractions.controller_protocols import ApiEndPointProtocolFunction


class AppInterface(ABC):
    """
    Abstract base class defining the contract for a web application framework adapter.

    This interface provides a consistent API for different web frameworks (FastAPI, Flask, etc.)
    enabling framework-agnostic application development. Implementing classes must provide
    mechanisms to add routes, manage routers, and start the application server.

    The interface supports:
    - Dependency injection
    - Response models
    - Bulk route creation through factory methods
    - Input validation
    - Error handling
    - Route documentation
    """

    def __init__(self, app_instance: Any) -> None:
        """
        Initialize the application interface with a framework-specific app_framework instance.

        Args:
            app_instance: The underlying application object (e.g., FastAPI instance, Flask app_framework)

        Raises:
            TypeError: If app_instance is not of the expected type
        """
        self._app = app_instance

    def get_app(self) -> Any:
        """
        Return the underlying application instance.

        Returns:
            Any: The framework-specific application instance

        Note:
            This method provides access for integration, testing, or framework-specific extensions.
        """
        return self._app

    @abstractmethod
    def add_route(
        self,
        path: str | Path,
        endpoint: ApiEndPointProtocolFunction,
        methods: Sequence[str],
        response_model: Optional[BaseModel] = None,
        status_code: Optional[int] = None,
        tags: Optional[list[str]] = None,
        dependencies: Optional[list[Any]] = None,
    ) -> None:
        """
        Abstract method to register a new route with the application.

        Args:
            path: The URL path at which the endpoint will be available
            endpoint: The function that will handle requests to this route
            methods: HTTP methods allowed for this route (e.g., ['GET', 'POST'])
            response_model: Optional response model for serialization and documentation
            status_code: HTTP status code for successful responses
            tags: List of tags for API documentation and organization
            dependencies: List of dependencies to inject into the endpoint

        Raises:
            ValueError: If path is empty, methods are invalid, or endpoint is None
            TypeError: If types don't match expected values
            NotImplementedError: Must be implemented by concrete classes
        """
        raise NotImplementedError

    @abstractmethod
    def add_router(self, router: Any) -> None:
        """
        Abstract method to add a router to the application.

        Args:
            router: A RouterInterface implementation containing grouped routes

        Raises:
            TypeError: If router doesn't implement RouterInterface
            ValueError: If router is None
            NotImplementedError: Must be implemented by concrete classes
        """
        raise NotImplementedError

    @abstractmethod
    def run_application(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """
        Abstract method to start the web server and begin serving requests.

        Args:
            host: The IP address or hostname to bind the server to
            port: The TCP port on which the server will listen

        Raises:
            ValueError: If host is invalid or port is out of range
            NotImplementedError: Must be implemented by concrete classes
        """
        raise NotImplementedError


