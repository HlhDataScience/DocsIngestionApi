
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
import os
from typing import  Any, Dict, Set
from uuid import uuid4

import json
from fastapi import Depends, UploadFile, File
from pydantic_core import ValidationError
import shutil
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
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
    hash_key,
    generate_api_key,
    store_key_in_vault,
    validate_users_api_key,
    validate_admin_api_key

)

from src.utils import simplify_items_for_search
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")
BLOB_NAME = os.getenv("BLOB_NAME")

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
        "message" : "Bienvenido al servicio API de pre_ingesta_documental_be" ,
        "description" : "Servicio de Ingesta Documental para Bases de Conocimiento",
        "version" : "PRE VERSION 3.0 // Imagen de Docker version latest",
        "endpoints" : {
            "/generate-key" : "REQUIERE API KEY. Endpoint para generar nuevas claves API, protegido por una clave de administrador. Genera y almacena las claves API en un secrets Vault.",
            "/index": "REQUIERE API KEY. Índice de búsqueda de los documentos procesados con anterioridad. Devuelve los datos esenciales que luego se pueden usar para usar el siguiente endpoint, '/search'.",
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
        "message": "Bienvenido al servicio API de ingesta_documental_be",
        "description": "Servicio de Ingesta Documental para Bases de Conocimiento",
        "version": "PRODUCTION VERSION 1.0",
        "endpoints": {
            "/generate-key": "REQUIERE API KEY. Endpoint para generar nuevas claves API, protegido por una clave de administrador. Genera y almacena las claves API en un secrets Vault.",
            "/index": "REQUIERE API KEY. Índice de búsqueda de los documentos procesados con anterioridad. Devuelve los datos esenciales que luego se pueden usar para usar el siguiente endpoint, '/search'.",
            "/search": "REQUIERE API KEY. Recupera información sobre los documentos previamente subidos en función de los parámetros de consulta.",
            "/uploadocs": "REQUIERE API KEY. Procesa y sube documentos de Word a la base de conocimiento de Qdrant de forma asíncrona utilizando un flujo de trabajo basado en grafos potenciado por GenAI.",
            "/docs": "Documentación de la API (Swagger UI).",
            "/openapi.json": "Esquema OpenAPI.",
        }
    }
async def docs_index(
        valid_api_key: str = Depends(validate_users_api_key())
) -> Dict[str, Any]:
    """
    Return the uploaded and transformed documents info to make the search easier for the endpoint "search".
    """
    non_simplified_keys: Set[str] = {
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
        async for doc in simplify_items_for_search(non_simplified_keys):
            indexable_documents.append(doc)

        return {
            "status_code": 200,
            "message": "Success",
            "content": {"results": indexable_documents}
        }
    except Exception as e:
        return {
            "status_code": 500,
            "message": str(e),
            "content": {}
        }

async def get_uploaded_docs_info(
        query_parameters: SearchQueryParameters = Depends(),
        valid_key: str = Depends(validate_users_api_key())
) -> Dict[str, Any]:
    """
    Retrieve information about previously uploaded documents from Blob based on optional query parameters.
    Returns a single result if 'index' is provided, or a list of all matched documents otherwise.
    """
    from azure.storage.blob.aio import BlobServiceClient
    from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

    matched_docs = []
    upload_author_string_rep = (
        str(query_parameters.upload_author) if query_parameters.upload_author else None
    )

    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    blob_client = container_client.get_blob_client(BLOB_NAME)

    try:
        stream = await blob_client.download_blob()
        contents = (await stream.readall()).decode("utf-8")
        lines = contents.strip().splitlines()

        for index, line in enumerate(lines):
            item = json.loads(line)
            item["index_id"] = index + 1

            matches_any_doc = (
                    (query_parameters.upload_author and item.get("upload_author", "") == upload_author_string_rep)
                    or
                    (query_parameters.doc_name and item.get("doc_name", "") == query_parameters.doc_name)
            )

            if matches_any_doc or (not query_parameters.upload_author and not query_parameters.doc_name):
                matched_docs.append(item)

        if not matched_docs:
            return {
                "status_code": 404,
                "message": "No documents were found under those filters.",
                "content": {}
            }

        sorted_docs = sorted(
            matched_docs,
            key=lambda x: x.get(query_parameters.order_by)
        )

        if query_parameters.index is not None:
            if query_parameters.index > len(sorted_docs):
                return {
                    "status_code": 404,
                    "message": "Index out of range.",
                    "content": {}
                }

            selected_doc = sorted_docs[query_parameters.index - 1]
            return {
                "status_code": 200,
                "message": "Single document retrieved successfully.",
                "content": {"documents_selected": selected_doc}
            }

        return {
            "status_code": 200,
            "message": f"{len(sorted_docs)} documents retrieved successfully.",
            "content": {"selected_documents": sorted_docs}
        }

    except (ResourceNotFoundError, HttpResponseError) as e:
        return {
            "status_code": 404,
            "message": f"Blob error: {str(e)}",
            "content": {}
        }

    except Exception as e:
        return {
            "status_code": 500,
            "message": f"Internal server error: {str(e)}",
            "content": {}
        }

    finally:
        await blob_service_client.close()


async def upload_docx(input_file: UploadFile = File(...),
                      query_parameters: UploadDocsParameters = Depends(), # This is because it has nested field that we use, so we use it insteaf of Annotated[UploadDocsParameters, Query()]
                      valid_key: str = Depends(validate_users_api_key()) #uncommnet for production
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
        :param valid_key:
        :param query_parameters:
        :param input_file:
    """
    temp_file ="/tmp/uploaded_docs"
    os.makedirs(temp_file, exist_ok=True)
    temp_file_path = os.path.join(temp_file, f"{uuid4()}_{input_file.filename}")

    try:
        with open(temp_file_path, "wb") as temp_file:
            shutil.copyfileobj(input_file.file, temp_file)
    except Exception as e:
        return {
            "status_code": 500,
            "message": f"Internal server error: {str(e)}",
            "content": {}
        }

    try:

        DocxValidator(file_name=temp_file_path)
    except ValidationError as ve:
        return {"status" : 400,
                "message": str(ve),
                "content": {}

        }
    try:
        examples_docs_path = "assets/real_user_questions/qdrant_data_export.json"
        initial_state = StateDictionary(
            status=None,
            upload_author=query_parameters.upload_author,
            doc_name=query_parameters.doc_name,
            collection=query_parameters.collection,
            updated_collection=query_parameters.update_collection,
            original_document=None,
            original_document_path=temp_file_path,
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
        if result["error"] is not None:
            return {"status_code" : 500,
                    "message" : f"error within the processing pipeline: {result["status"]}",
                    "content" : result["error"]

                    }
        not_necessary_for_presentation = frozenset({
            "original_document",
            "generated_qa",
            "examples_path",
            "evaluator_response",
            "max_retry" ,
            "error",
            "updated_collection",
            "original_document_path",
            "examples_qa",


        })
        filtered_result = {k:v for k, v in result.items() if k not in not_necessary_for_presentation}
        presented_results = {
            k: (
                [
                    {ik: iv for ik, iv in item.items() if ik != "vector"}
                    for item in v
                ]
                if k == "refined_qa" and isinstance(v, list)
                else v
            )
            for k, v in filtered_result.items()
        }
        return {
            "status_code": 200,
            "message": "Successfully transformed and uploaded documents...",
            "content": presented_results
        }
    except Exception as e:
        return {
            "status_code": 500,
            "message": f"Internal server error: {str(e)}",
            "content": {}
        }
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)



ADMIN_KEY_ID = "pre-ingesta-documental-bc-admin-key"

async def generate_api_key_point(
        request: ApiKeyGenerationRequest,
        admin_key: str = Depends(validate_admin_api_key(required_id_key=ADMIN_KEY_ID)) # Uncomment this in case you whish to get ready for testing to release in production.
)-> Dict[str, Any]:
    """
    Public endpoint to generate new api keys protected by admin key if configured. It generates and stores the api_keys.
    :param request: The request object
    :param admin_key: The admin api key
    :return: Dictionary containing the new api key
    """



    raw_key = generate_api_key()
    hashed_key = hash_key(raw_key)


    await store_key_in_vault(
        key_id=request.key_id,
        hashed_key=hashed_key,
        description=request.description,
        expire_in_days=request.expire_in_days,
    )
    return {
        "status_code": 200,
        "message": "success",
        "content": {
            "api_key": raw_key,
            "id_key": request.key_id,
            "description": request.description,
            "expire_in_days": request.expire_in_days,
            "warning": "ATENCIÓN: Guarde la clave de forma segura. No volverá a ver la clave nunca más."
        }
    }