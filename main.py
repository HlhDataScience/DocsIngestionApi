from fastapi import FastAPI  # type: ignore

from src.controllers import FastApiFramework, root_spec, post_documents_spec, get_docs_uploaded_spec



app_ = FastApiFramework.from_constructor(app_type=FastAPI,
                                         title="DocumentalIngestAPI",
                                         version="0.1.0",
                                         api_spec=(root_spec, post_documents_spec, get_docs_uploaded_spec) #This is because to have a tuple with only one element it is necessary to have a final coma at the end.
                                         )



app= app_.get_app()

