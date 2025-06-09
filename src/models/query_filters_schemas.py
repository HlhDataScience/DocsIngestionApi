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

    doc_name: int = Field(None, ge=1, le=5)
    index: int = Field(None)
    order_by: Literal["index_id", "doc_name", "time_stamp"] = "doc_name"