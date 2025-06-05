from fastapi import FastAPI

from src.controllers import FastApiFramework, dev_get_post_docs_root
from src.models import APIInfo
from src.models.validation_schemas import EndpointSpec

root_spec = EndpointSpec(
    path= "/",
    handler= dev_get_post_docs_root,
    required_params= ["GET"],
    response_model= APIInfo,

)


app_ = FastApiFramework.from_constructor(app_type=FastAPI,
                                         title="DocumentalIngestAPI",
                                         version="1.0.0.",
                                         api_spec=(root_spec,)
                                         )



app= app_.get_app()

