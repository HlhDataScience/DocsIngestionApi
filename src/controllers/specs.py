from src.models import EndpointSpec, FastApiGetResponse, FastApiPostResponse, APIInfoResponse
from .api_endpointfuncs import dev_get_post_docs_root, upload_docx, get_uploaded_docs_info


root_spec = EndpointSpec(
    path= "/",
    handler= dev_get_post_docs_root,
    required_params= ["GET"],
    response_model= APIInfoResponse,

)

post_documents_spec = EndpointSpec(
    path="/uploadocs",
    handler= upload_docx,
    required_params= ["POST"],
    response_model= FastApiPostResponse,

)

get_docs_uploaded_spec = EndpointSpec(
    path="/docs",
    handler= get_uploaded_docs_info,
    required_params= ["GET"],
    response_model= FastApiGetResponse,
)