"""
abstractions.py

This module defines abstract interfaces for asynchronous vector database clients and
data entry models. These abstractions are designed to standardize interactions with
vector stores such as Qdrant, Pinecone, or others, enabling interoperability, testability,
and clear implementation contracts.

Classes:
    VectorDataBaseClientInterfaceAsync: Abstract base class for asynchronous vector
        database clients. It defines all required operations such as collection creation,
        batch uploads, transformation, and similarity search queries.

Usage:
    These interfaces must be implemented by concrete classes that manage the logic for
    vector storage, transformation, and retrieval. Implementations are expected to
    follow asynchronous programming patterns using `async def` and return `Coroutine`.

    This module should be used by developers building custom vector database connectors
    or backends for embedding-based systems (e.g., RAG pipelines, search engines).

Note:
    Implementers of `VectorDataBaseClientInterfaceAsync` are expected to also implement
    the `VectorDataBaseEntryInterface`, ensuring compatibility between data models
    and the vector database logic.
"""

from abc import ABC, abstractmethod
from typing import Coroutine, Any, Iterable, List, Dict

from pydantic import BaseModel


class VectorDataBaseClientInterfaceAsync(ABC):
    """
    Abstract base class for asynchronous client interfaces for Vector Data Bases.

    This interface defines the contract for implementing asynchronous vector database
    clients that can perform operations like creating collections, adding points,
    searching, and batch processing. All concrete implementations must provide
    async implementations of the abstract methods defined here.

    IMPORTANT: Concrete implementations of this class MUST also implement the
    VectorDataBaseEntryInterface to ensure compatibility between the client
    and data model operations.

    Args:
        data_model (VectorDataBaseEntryInterface): The data model interface that
            defines the structure and format of vector database entries. This
            should be an instance of the same class that implements both this
            interface and VectorDataBaseEntryInterface.

    Attributes:
        _data_model (VectorDataBaseEntryInterface): Internal reference to the
            data model used for vector database operations.

    Implementation Requirements:
        - Must inherit from both AsyncVectorDataBaseClientInterface and
          VectorDataBaseEntryInterface
        - The data_model parameter in __init__ should typically be 'self'
          when the same class implements both interfaces

    Abstract Methods:
        create_collection: Creates a new collection in the vector database

        add_points_with_retry: Adds vector points to the database with retry logic.
            This method should internally call _transform_points to convert the
            data model before uploading to the database.

        _transform_points: Transforms data model into database-specific format.
            This is a private method intended to be called by add_points_with_retry
            and used within upload_documents workflow.

        upload_documents: Uploads batched data points to database. This method should call
        add_points_with_retry internally to perform the upload.

        get_collection_info: Retrieves metadata and information about a collection

        verify_upload: Verifies that data upload operations completed successfully

        dense_search: Performs dense vector similarity search operations

        batch_queries: Executes multiple queries in a single batch operation

    Note:
        All methods return Coroutine[Any, Any, Any] and must be implemented
        as async methods in concrete subclasses. This interface follows the
        Abstract Base Class pattern to ensure consistent implementation across
        different vector database providers.

    Example:
        class MyVectorDBClient(VectorDataBaseClientInterfaceAsync, VectorDataBaseEntryModel):
        ...     def __init__(self):
        ...         # Pass self as data_model since this class implements both interfaces
        ...         super().__init__(self)
        ...
        ...     async def create_collection(self):
        ...         # Implementation here
        ...         pass
        ...     # ... implement other abstract methods from both interfaces

        Alternative pattern with separate data model:
        class MyDataModel(VectorDataBaseEntryModel):
        ...     # Implement VectorDataBaseEntryInterface methods
        ...     pass

        class MyVectorDBClient(VectorDataBaseClientInterfaceAsync):
        ...     def __init__(self, data_model: type[BaseModel]):
        ...         super().__init__(data_model)
        ...     # ... implement abstract methods
    """

    def __init__(self, data_model: type[BaseModel]):
        self._data_model = data_model
        if not issubclass(data_model, self._data_model):
            raise TypeError(
                f"data_model must implement BaseModel, "
                f"got {type(self._data_model).__name__}"
            )




    @abstractmethod
    async def create_collection(self) -> Coroutine[Any, Any, Any] | None:
        """
        Create a new collection in the vector database.

        This method should handle the creation of a new collection/index
        in the vector database with appropriate configuration settings.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                collection creation result or confirmation.

        Raises:
            NotImplementedError: If not implemented in concrete class.
        """
        ...

    @abstractmethod
    async def add_points_with_retry(self, points: Any) -> Coroutine[Any, Any, Any]:
        """
        Add vector points to the database with retry logic.

        This method should handle uploading vector data points to the database
        with built-in retry mechanisms for handling transient failures.
        It should internally call _transform_points to convert the data model
        into the appropriate format before upload.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                the result of the upload operation.

        Raises:
            NotImplementedError: If not implemented in concrete class.
        """
        ...

    @abstractmethod
    def _transform_points(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform data model into database-specific format.

        This private method converts the VectorDataBaseEntryModel data
        into the specific format required by the target vector database.
        It is intended to be called internally by add_points_with_retry
        during the upload_documents workflow.

        Args:
            data_model (VectorDataBaseEntryModel): The data model to transform.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                the transformed data in database-specific format.

        Raises:
            NotImplementedError: If not implemented in concrete class.
        """
        ...

    @abstractmethod
    async def upload_documents(self, items: Iterable[Dict[str, Any]], batch_size: int) -> Coroutine[Any, Any, Any]| None:
        """
        Upload a collection of documents to the vector database in batches.

        This method processes an iterable of raw document dictionaries,
        transforms them into the required vector format, and uploads them
        in batches of the specified size. The transformation should be
        handled via `_transform_points`, and the actual upload should
        internally use `add_points_with_retry`.

        Args:
            items (Iterable[Dict[str, Any]]): Raw documents to be converted into vector entries.
            batch_size (int): The number of documents to include in each upload batch.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns the result of the upload process,
            including any batch verification outcomes.

        Raises:
            NotImplementedError: If not implemented in a concrete subclass.
        """
        ...

    @abstractmethod
    async def get_collection_info(self) -> Coroutine[Any, Any, Any]:
        """
        Retrieve metadata and information about a collection.

        This method should return detailed information about the collection
        such as size, configuration, status, and other relevant metadata.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                collection metadata and information.

        Raises:
            NotImplementedError: If not implemented in concrete class.
        """
        ...

    @abstractmethod
    async def _verify_batch(self, point_id:int) -> Coroutine[Any, Any, Any] | None:
        """
        Verify that data upload operations completed successfully.

        This method should check and confirm that previously uploaded
        data has been properly stored and indexed in the vector database.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                verification results or status.

        Raises:
            NotImplementedError: If not implemented in concrete class.
        """
        ...

    @abstractmethod
    async def verify_upload(self) -> Coroutine[Any, Any, Any] | None:
        """
        Verify the success of all recent data upload operations.

        This method should perform validation checks to ensure that the most recent
        upload operations have been completed successfully.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
            a summary or status of the upload verification process.

        Raises:
            NotImplementedError: If not implemented in a concrete subclass.
        """
        ...
    @abstractmethod
    async def dense_search(self, dense_vector: List[float], top_k: int) -> Coroutine[Any, Any, Any] | None:
        """
        Perform dense vector similarity search operations.

        This method should execute similarity searches using dense vector
        representations to find the most similar vectors in the database.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                search results with similarity scores and metadata.

        Raises:
            NotImplementedError: If not implemented in concrete class.
        """
        ...

    @abstractmethod
    async def batch_queries(self, query_vectors: List[Dict[str, Any]], top_k: int) -> Coroutine[Any, Any, Any] | None:
        """
        Execute multiple queries in a single batch operation.

        This method should handle multiple search queries simultaneously
        for improved performance and efficiency when processing multiple
        requests at once.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                batch query results for all submitted queries.

        Raises:
            NotImplementedError: If not implemented in concrete class.
        """
        ...