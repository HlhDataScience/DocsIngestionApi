from src.models import EndpointSpec, FastApiGetResponse, FastApiPostResponse, APIInfoResponse
from .api_endpointfuncs import dev_get_post_docs_root, upload_docx, get_uploaded_docs_info
from src.abstractions import protocol_checker, ApiEndPointProtocolFunction, AsyncApiEndpointProtocolFunction

if not protocol_checker(
        fn_list= [dev_get_post_docs_root, upload_docx, get_uploaded_docs_info],
        protocols=(AsyncApiEndpointProtocolFunction,ApiEndPointProtocolFunction)
):
    raise ValueError(f"All the functions must conform to  {ApiEndPointProtocolFunction.__name__} or {AsyncApiEndpointProtocolFunction.__name__}")


root_spec = EndpointSpec(
    path= "/v1",
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
    path="/docs",
    handler= get_uploaded_docs_info, # type: ignore
    required_params= ["GET"],
    response_model= FastApiGetResponse,
)