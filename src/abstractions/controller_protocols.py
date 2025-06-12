"""
controler_protocols.py

Defines protocol-based interfaces for API endpoint functions.

Includes:
- ApiEndpointProtocolFunction: A runtime-checkable protocol ensuring API endpoints match expected signature.
- AsyncApiEndpointProtocolFunction: A runtime-checkable asynchronous protocol ensuring API endpoints match expected async signature.
- protocol_checker: A utility to validate whether a list of functions conforms to the specified protocol.
"""

from typing import Any, Callable, Coroutine, Dict, List, Protocol, runtime_checkable, Type, Union

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
    def __call__(self, *args: Any, **kwargs: Any) -> Dict[str, Any] | Any:
        ...


def protocol_checker(
    fn_list: List[Callable[..., Any]],
    protocols: Union[
        Type[ApiEndPointProtocolFunction],
        Type[AsyncApiEndpointProtocolFunction],
        tuple[Type[ApiEndPointProtocolFunction | AsyncApiEndpointProtocolFunction], ...]
    ]
) -> bool:
    """
    Checks whether all functions in the list conform to at least one of the given runtime-checkable protocols.

    Parameters:
    - fn_list: A list of functions to validate.
    - protocols: A single protocol class or a tuple of protocol classes.

    Returns:
    - True if all functions match at least one of the specified protocols, False otherwise.
    """
    if not isinstance(protocols, tuple):
        protocols = (protocols,)

    return all(any(isinstance(fn, proto) for proto in protocols) for fn in fn_list)
