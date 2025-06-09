""" This file contains the instantiation of the router class for post docs as well as the controller function that are going to be used in the main entry program"""
from typing import  Annotated, Any, Dict

from fastapi import Query
from pydantic_core import ValidationError

from src.models.validation_schemas import DocxValidator
from src.models.query_filters_schemas import QueryParameters
from src.application.graph_orchestrator import stategraph_run

def dev_get_post_docs_root() -> Dict[str, Any]:
    return {
        "message" : "Bienvenido a DocumentalIngestAPI",
        "description" : "Servicio de Ingesta Documental para Bases de Conocimiento",
        "version" : "DEV VERSION 0.1.0",
        "endpoints" : {
            "/postdocs" : "Endpoint para el envío de documentos de word a la base de conocimiento de Qdrant",
            "/docs": "Documentación de la API (Swagger UI).",
            "/openapi.json": "Esquema OpenAPI.",
        }
    }



def get_post_docs_root() -> Dict[str, Any]:
    return {
        "message" : "Bienvenido a DocumentalIngestAPI",
        "description" : "Servicio de Ingesta Documental para Bases de Conocimiento",
        "version" : "1.0.0",
        "endpoints" : {
            "/postdocs" : "Endpoint para el envío de documentos de word a la base de conocimiento de Qdrant",
            "/docs": "Documentación de la API (Swagger UI).",
            "/openapi.json": "Esquema OpenAPI.",
        }
    }

def get_uploaded_docs_info(query_parameters: Annotated[QueryParameters, Query()])-> Dict[str, Any]:
    ...

async def upload_docx(input_docs_path: str) -> Dict[str, Any]:

    try:

        DocxValidator(file_name=input_docs_path)
    except ValidationError as ve:
        return {"response" :
                    {"code": 400,
                     "message": f"{ve}"}

        }


    await stategraph_run(input_docs_path=input_docs_path)

    return {"response" :
                    {"code": 200,
                     "message": f"Successfully transformed and uploaded document {input_docs_path} to Qdrant Knowledge Database."}
            }

