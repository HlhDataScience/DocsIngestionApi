from fastapi import FastAPI  # type: ignore

from src import (
    dev_root_spec,
    post_documents_spec,
    get_docs_uploaded_spec,
    FastApiFramework,
    post_generated_api_key_spec,
    get_docs_index_spec
)



app_ = FastApiFramework.from_constructor(app_type=FastAPI,
                                         title="pre_ingesta_documental_be",
                                         version="PRE VERSION 3.0",
                                         api_spec=(
                                            dev_root_spec,
                                            post_generated_api_key_spec,
                                            get_docs_index_spec,
                                            get_docs_uploaded_spec,
                                            post_documents_spec,
                                            ) #This is because to have a tuple with only one element it is necessary to have a final coma at the end.
                                         )



app= app_.get_app()

