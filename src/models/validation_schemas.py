"""
validation_schemas.py

Data schemas for request/response validation using Pydantic.

These schemas define the structure and constraints of the data exchanged
within the application abstractions (e.g., API payloads, business entities).

Includes:
- DocxValidator: Schema for processing DOCX-related data.
- QdrantValidator: Schema for defining vector database entries.
- QdrantDataPointConformer: Schema for validating data points.
-
"""
from typing import Any, Dict, List

from pydantic import BaseModel, field_validator  # type: ignore


class QdrantValidator(BaseModel):
    """class to validate Qdrant data against a schema
    attributes:
    id(str): uuid4 string version identifier
    vector(Dict[str, List[Any]]): dense vector  database entries
    payload(Dict[str, List[Any]]): string database entries
    """
    id: str
    vector: Dict[str, List[float]]
    payload: Dict[str, Any]

class DocxValidator(BaseModel):

    """Validation model for docx file inputs in the application.

    This class defines a simple validation mechanism for ensuring that the
    provided file name corresponds to a docx file. It includes a single field
    with validation rules.

    Attributes:
        file_name (str): The name of the file to validate, which must end with
            the '.docx' extension.

    Validators:
        validate_docx: Ensures that the file name ends with '.pdf'.
    """

    file_name: str

    @classmethod
    @field_validator("file_name")
    def validate_docx(cls, file_name: str) -> str:
        """Validates that the file name corresponds to a docx file.

        Args:
            cls: The class itself.
            file_name (str): The name of the file to validate.

        Returns:
            str: The validated file name.

        Raises:
            ValueError: If the file name does not end with '.pdf'.
        """
        if not file_name.endswith(".docx"):
            raise ValueError("File must be a valid Microsoft Word document.")
        return file_name

class QdrantDataPointConformer(BaseModel):
    id: str
    vector: Dict[str, List[float]]
    payload: Dict[str, Any]

class QdrantBotAnswerConformer(BaseModel):
    id: str
    vector: List[float]
    payload: Dict[str, Any]