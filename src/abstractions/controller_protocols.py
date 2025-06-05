"""
Defines protocol-based interfaces for API endpoint functions.

Includes:
- ApiEndpointProtocolFunction: A runtime-checkable protocol ensuring API endpoints match expected async signature.
- protocol_checker: A utility to validate whether a list of functions conforms to the specified protocol.
"""

from typing import Any, Callable, Coroutine, Dict, List, Protocol, runtime_checkable

@runtime_checkable
class AsyncApiEndpointProtocolFunction(Protocol):
    """
    A runtime-checkable protocol to define the expected structure of asynchronous API endpoint functions.

    Functions conforming to this protocol must be `async` callables that accept any number of
    positional or keyword arguments and return a Coroutine that yields either:
    - a dictionary with string keys and arbitrary values (e.g., a JSON response), or
    - any other return type (to allow for flexible response handling).
    """
    async def __call__(self, *args: Any, **kwargs: Any) -> Coroutine[Any, Any, Dict[str, Any] | Any]:
        ...
@runtime_checkable
class ApiEndPointProtocolFunction(Protocol):
    """
    A runtime-checkable protocol to define the expected structure of API endpoint functions.

    Functions conforming to this protocol must be callables that accept any number of
    positional or keyword arguments and return a Callable that yields either:
    - a dictionary with string keys and arbitrary values (e.g., a JSON response), or
    - any other return type (to allow for flexible response handling).
    """
    def __call__(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        ...



def protocol_checker(fn_list: List[Callable[..., Any]], protocol: ApiEndPointProtocolFunction | AsyncApiEndpointProtocolFunction) -> bool:
    """
    
    Checks whether all functions in a given list conform to a specified runtime-checkable protocol.

    Parameters:
    - fn_list (List[Callable[..., Any]]): A list of functions to validate.
    - protocol (ApiEndpointProtocolFunction): A protocol instance used to verify function compliance.

    Returns:
    - bool: True if all functions implement the given protocol, False otherwise.

    This is useful for validating dynamic API endpoint registration or plugin systems where behavior contracts are important.
    """
    return all(isinstance(fn, protocol) for fn in fn_list)  # type: ignore
