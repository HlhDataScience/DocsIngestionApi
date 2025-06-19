"""
query_filter_schemas.py

This module defines Pydantic models for query parameter validation and filtering
operations. It provides structured schemas for filtering, indexing, and ordering
query results with built-in validation constraints.

The module is designed to handle query parameters for document-based operations
where results need to be filtered by document identifiers, retrieved by specific
indices, and ordered according to various criteria.

Key Features:
    - Document name filtering with validation constraints (1-5 range)
    - Index-based result retrieval
    - Configurable ordering by multiple fields
    - Built-in Pydantic validation for type safety and constraint enforcement

Classes:
    SearchQueryParameters: Main query parameter model with filtering and ordering options

Usage:
    This module is typically used in API endpoints or database query operations
    where structured parameter validation is required.
"""

from typing import Literal

from pydantic import BaseModel, Field, NameEmail


class SearchQueryParameters(BaseModel):
    """
    SearchQueryParameters

    A class that defines the parameters for querying predictions, including
    class constraints, index, and order by criteria.

    Attributes:
        doc_name (int): The class to filter predictions, constrained between 1 and 5.
        index (int): The index of the result to retrieve.
        order_by (Literal): The field to order the results by, can be 'index_id',
                            'prediction', or 'time_stamp'.
    """
    upload_author: NameEmail = Field(..., title="Upload author", description="Autor original del procesado del documento.")
    doc_name: str = Field(..., title="Document name", description="Nombre original del documento word.")
    index: int =  Field(..., ge=1, le=10, title="Index", description="índice de documentos transformados y subidos a Qdrant")
    order_by: Literal["index_id", "doc_name"] = "index_id"

class UploadDocsParameters(BaseModel):
    """
    UploadDocsParameters
    A class that defines the parameters for uploading documents to be transformed as Q&A pairs and
    uploaded to Qdrant
    """
    upload_author: NameEmail = Field(..., title="Upload author", description="Autor original del procesado del documento.")
    doc_name: str = Field(..., title="Document name", description="Nombre original del documento word.")
    collection: Literal["Coll1", "Coll2", "Coll3", "Coll4", "Coll5", "Coll6"] = Field(..., title="Collection", description="Colección a la que subir el documento")
    update_collection: bool = Field(..., title="Update document", description=" Si la condición es verdadera, sobreescribe y actualiza los datos de la colección en Qdrant")