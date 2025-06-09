from typing import List, NamedTuple, Optional, Union
from src.abstractions.controller_protocols import  ApiEndPointProtocolFunction, AsyncApiEndpointProtocolFunction
from src.models.response_schemas import FastApiGetResponse, FastApiPostResponse, APIInfoResponse

class EndpointSpec(NamedTuple):
    """
    FastAPI endpoint specification formating class
    """
    path: str
    handler: Union[type[ApiEndPointProtocolFunction], type[AsyncApiEndpointProtocolFunction]]
    required_params: List[str]
    response_model: Optional[Union[type[FastApiGetResponse], type[FastApiPostResponse], type[APIInfoResponse]]]