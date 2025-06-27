
"""
api_endpointfuncs.py
~~~~~~~~~~~~~~~~~~~

FastAPI endpoint controller functions for the DocumentalIngestAPI service.

This module contains the implementation of controller functions and router instantiation
for the document ingestion API. It provides endpoints for uploading Word documents to
a Qdrant knowledge base, retrieving API information, and managing document processing
workflows through a state graph architecture.

The module serves as the bridge between FastAPI routing and the core application logic,
handling HTTP request/response cycles, input validation, error handling, and coordinating
the document processing pipeline. It implements both development and production versions
of API endpoints with appropriate versioning and response formatting.

Key Features:
    - REST full API endpoints for document ingestion
    - Input validation using Pydantic models
    - Asynchronous document processing with state graph architecture
    - Error handling and structured response formatting
    - Development and production environment support
    - Integration with Qdrant vector database for knowledge storage

Architecture:
    The module follows a controller pattern where each function handles specific
    API endpoints and coordinates with the application layer for business logic
    execution. The document processing workflow uses a self-reflecting state graph
    that manages the transformation and upload process through various processing nodes.

Dependencies:
    - FastAPI: Web framework for API endpoints
    - Pydantic: Data validation and serialization
    - Application layer: Core business logic and state graph processing
    - Models: Data validation and type definitions

Functions:
    dev_get_post_docs_root(): Development version of root endpoint information
    get_post_docs_root(): Production version of root endpoint information
    get_uploaded_docs_info(): Retrieve information about uploaded documents
    upload_docx(): Process and upload Word documents to the knowledge base

Usage:
    This module is used as the controller layer in a FastAPI application for
    document ingestion services. Functions are typically decorated with FastAPI
    route decorators to create HTTP endpoints.
"""

from typing import Annotated, Any, Dict, Set

import json
from fastapi import Query, Depends
from multipart import file_path
from pydantic_core import ValidationError

from src.application import (
    self_reflecting_stategraph_factory_constructor,
    stategraph_run,
    NODES_FUNCS,
    evaluator_router
)
from src.models import (
    DocxValidator,
    SearchQueryParameters,
    UploadDocsParameters,
    StateDictionary,
    ApiKeyGenerationRequest
)
from src.security import (
    API_KEY_PREFIX,
    hash_key,
    generate_api_key,
    store_key_in_vault
)

from src.utils import simplify_items_for_search


async def dev_get_post_docs_root() -> Dict[str, Any]:
    """
    Return API information and available endpoints for development environment.

    Provides comprehensive information about the DocumentalIngestAPI service
    including version details, service description, and available endpoints
    specifically configured for development usage. This function serves as
    the root endpoint response for development deployments.

    The response includes:
    - Service welcome message in Spanish
    - Service description explaining document ingestion functionality
    - Development version identifier
    - Complete endpoint documentation with descriptions

    Returns:
        Dict[str, Any]: A dictionary containing API metadata and endpoint information
            with the following structure:
            - "message": Welcome message for the service
            - "description": Service functionality description
            - "version": Development version identifier
            - "endpoints": Dictionary mapping endpoint paths to descriptions
            """
    return {
        "message" : "Bienvenido a DocumentalIngestAPI",
        "description" : "Servicio de Ingesta Documental para Bases de Conocimiento",
        "version" : "DEV VERSION 2.0",
        "endpoints" : {
            "/generate-key" : "Endpoint para generar nuevas claves API, protegido por una clave de administrador si está configurada. Genera y almacena las claves API.",
            "/search" : "REQUIERE API KEY. Recupera información sobre los documentos previamente subidos en función de los parámetros de consulta.",
            "/uploadocs": "REQUIERE API KEY. Procesa y sube documentos de Word a la base de conocimiento de Qdrant de forma asíncrona utilizando un flujo de trabajo basado en grafos potenciado por GenAI.",
            "/docs": "Documentación de la API (Swagger UI).",
            "/openapi.json": "Esquema OpenAPI.",
        }
    }

async def get_post_docs_root() -> Dict[str, Any]:
    """

    Return API information and available endpoints for production environment.

    Provides comprehensive information about the DocumentalIngestAPI service
    including version details, service description, and available endpoints
    specifically configured for production usage. This function serves as
    the root endpoint response for production deployments.

    The response includes:
    - Service welcome message in Spanish
    - Service description explaining document ingestion functionality
    - Production version identifier (1.0.0)
    - Complete endpoint documentation with descriptions

    Returns:
        Dict[str, Any]: A dictionary containing API metadata and endpoint information
            with the following structure:
            - "message": Welcome message for the service
            - "description": Service functionality description
            - "version": Production version identifier
            - "endpoints": Dictionary mapping endpoint paths to descriptions

    """
    return {
        "message" : "Bienvenido a DocumentalIngestAPI",
        "description" : "Servicio de Ingesta Documental para Bases de Conocimiento",
        "version" : "1.0",
        "endpoints" : {
            "/generate-key" : "Endpoint para generar nuevas claves API. Genera y almacena las claves API.",
            "/search" : "REQUIERE API KEY. Recupera información sobre los documentos previamente subidos en función de los parámetros de consulta.",
            "/uploadocs": "REQUIERE API KEY. Procesa y sube documentos de Word a la base de conocimiento de Qdrant de forma asíncrona utilizando un flujo de trabajo basado en grafos potenciado por GenAI.",
            "/docs": "Documentación de la API (Swagger UI).",
            "/openapi.json": "Esquema OpenAPI.",
        }
    }
async def docs_index() -> Dict[str, Any]:
    """
    Return the uploaded and transformed documents info to make the search easier for the endpoint "search".
    :return:
        docs_index: Dict[str, Any] The json formatted documents index
    """
    file_path = "assets/processed_docs/processed_documents.jsonl"
    non_simplified_keys: Set[str] =  {
        "status",
        "original_document",
        "generated_qa",
        "examples_path",
        "updated_collection",
        "original_document_path",
        "examples_qa",
        "evaluator_response",
        "refined_qa",
        "max_retry",
        "error"

    }

    try:
        indexable_documents = []
        async for doc in simplify_items_for_search(file_path, non_simplified_keys):
            indexable_documents.append(doc)

        return {
            "status_code" : 200,
            "message" : "Success",
            "content" : {"results": indexable_documents}
        }
    except Exception as e:
        return {
            "status_code" : 500,
            "message" : str(e),
            "content" : {}
        }

async def get_uploaded_docs_info(
    query_parameters: Annotated[SearchQueryParameters, Query()]
) -> Dict[str, Any]:
    """
    Retrieve information about previously uploaded documents based on query parameters.
    """
    matched_docs = []

    try:
        with open("assets/processed_docs/processed_documents.jsonl", "r") as f:
            for index, line in enumerate(f):
                item = json.loads(line)
                item["index_id"] = index + 1

                if (
                    item.get("upload_author", {})== str(query_parameters.upload_author) and
                    item.get("doc_name") == query_parameters.doc_name
                ):
                    matched_docs.append(item)

        if not matched_docs:
            return {
                "status_code": 404,
                "message": "No documents were found under those filters.",
                "content": {}
            }

        # Sort by the selected field
        sorted_docs = sorted(
            matched_docs,
            key=lambda x: x.get(query_parameters.order_by)
        )

        if query_parameters.index > len(sorted_docs):
            return {
                "status_code": 404,
                "message": "Index out of range.",
                "content": {}
            }

        selected_doc = sorted_docs[query_parameters.index - 1]

        return {
            "status_code": 200,
            "message": "Success",
            "content": selected_doc
        }

    except Exception as e:
        return {
            "status_code": 500,
            "message": f"Internal server error: {str(e)}",
            "content": {}
        }

async def upload_docx(input_docs_path: str,
                      query_parameters: UploadDocsParameters = Depends(), # This is because it has nested field that we use, so we use it insteaf of Annotated[UploadDocsParameters, Query()]
                      #valid_key: str = Depends(validate_api_key) #uncommnet for production
                      ) -> Dict[str, Any]:
    """
    Process and upload Word documents to the Qdrant knowledge base asynchronously.

    Handles the complete workflow for ingesting Word documents (.docx files) into
    the knowledge base system. This includes document validation, processing through
    a self-reflecting state graph architecture, transformation into vector embeddings,
    and storage in the Qdrant vector database.

    The function implements a comprehensive document processing pipeline:
    1. Input validation using DocxValidator to ensure file format compliance
    2. State graph construction for document processing workflow
    3. Asynchronous execution of the processing pipeline
    4. Error handling with structured response formatting
    5. Success confirmation with processing results

    Processing Workflow:
    - Document validation and format checking
    - Text extraction and preprocessing
    - Content chunking and embedding generation
    - Vector storage in Qdrant knowledge base
    - Metadata indexing and relationship mapping

    Args:
        input_docs_path (str): File path to the Word document to be processed.
            Should be a valid path to a .docx file that exists and is readable.
            The path can be absolute or relative to the application's working directory.

            Example: "/path/to/documents/contract.docx" or "uploads/report.docx"
        query_parameters: Query parameters to use when processing documents.

    Returns:
        Dict[str, Any]: A structured response dictionary containing:
            Success case (HTTP 200):
            {
                "response": {
                    "code": 200,
                    "message": "Successfully transformed and uploaded document...",
                    "content": <processing_results>
                }
            }

            Error case (HTTP 400):
            {
                "response": {
                    "code": 400,
                    "message": "<validation_error_details>"
                }
            }

    Raises:
        ValidationError: Caught internally and returned as HTTP 400 response
        Exception: Other processing errors are propagated to the caller
    """
    try:

        DocxValidator(file_name=input_docs_path)
    except ValidationError as ve:
        return {"status" : 400,
                "message": str(ve),
                "content": {}

        }
    examples_docs_path = "assets/real_user_questions/qdrant_data_export.json"
    initial_state = StateDictionary(
        status=None,
        upload_author=query_parameters.upload_author,
        doc_name=query_parameters.doc_name,
        updated_collection=query_parameters.update_collection,
        original_document=None,
        original_document_path=input_docs_path,
        generated_qa=None,
        examples_qa=None,
        examples_path=examples_docs_path,
        evaluator_response=None,
        refined_qa=None,
        max_retry=0,
        error=None)

    uncompiled_graph = self_reflecting_stategraph_factory_constructor(state_dict=StateDictionary,
                                                                      node_functions=NODES_FUNCS,
                                                          router_function=evaluator_router)
    result = await stategraph_run(
        initial_state=initial_state,
        uncompiled_graph=uncompiled_graph,
    )

    return {
        "status_code": 200,
        "message": "Successfully transformed and uploaded documents...",
        "content": result
    }

async def generate_api_key_point(
        request: ApiKeyGenerationRequest,
        # admin_key: Optional[str] = Security(api_key_header) # Uncomment this in case you whish to get ready for testing to release in production.
)-> Dict[str, Any]:
    """
    Public endpoint to generate new api keys protected by admin key if configured. It generates and stores the api_keys.
    :param request: The request object
    :param admin_key: The admin api key
    :return: Dictionary containing the new api key
    """

    # We should implement a security measure for the admin in the production case

    raw_key = generate_api_key()
    hashed_key = hash_key(raw_key)
    key_id = f"{API_KEY_PREFIX}{hashed_key}"

    await store_key_in_vault(
        key_id=key_id,
        hashed_key=hashed_key,
        description=request.description,
        expire_in_days=request.expire_in_days,
    )
    return {
        "api_key": raw_key,
        "description": request.description,
        "expire_in_days": request.expire_in_days,
        "warning": "ATENCIÓN: Guarde la clave de forma segura. No volverá a ver la clave nunca más."
    }