""" This file contains the instanciation of the router class for post docs as well as the controller function that are going to be used in the main entry program"""
from typing import Any, Dict



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