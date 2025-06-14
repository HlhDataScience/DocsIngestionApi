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
    QueryParameters: Main query parameter model with filtering and ordering options

Usage:
    This module is typically used in API endpoints or database query operations
    where structured parameter validation is required.
"""

from typing import Literal

from pydantic import BaseModel, Field


class QueryParameters(BaseModel):
    """
    QueryParameters

    A class that defines the parameters for querying predictions, including
    class constraints, index, and order by criteria.

    Attributes:
        doc_name (int): The class to filter predictions, constrained between 1 and 5.
        index (int): The index of the result to retrieve.
        order_by (Literal): The field to order the results by, can be 'index_id',
                            'prediction', or 'time_stamp'.
    """

    doc_name: str = Field(..., title="Document name", description="Original docx filename.")
    index: int =  Field(..., ge=1, le=10, title="Index", description="Index of the documents transformed and uploaded for search porpoises.")
    order_by: Literal["index_id", "doc_name", "time_stamp"] = "index_id"