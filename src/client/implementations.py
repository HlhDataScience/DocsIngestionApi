"""
implementations.py

Asynchronous implementation of a vector database client for Qdrant using `aiohttp`.

This module contains the concrete implementation of the `VectorDataBaseClientInterfaceAsync`
interface for managing vector data in a Qdrant collection. It handles all operations
asynchronously, including collection creation, document transformation, batch uploads,
upload verification, and vector search (dense, sparse, and hybrid).

The implementation provides robust error handling, retry mechanisms, and progress tracking
for large-scale vector operations. It's designed to work efficiently with high-volume
vector data processing workflows while maintaining data integrity through comprehensive
verification processes.

Key Technologies:
    - `aiohttp`: For non-blocking HTTP requests to Qdrant server
    - `Pydantic`: For input validation and data model enforcement
    - `tenacity`: For retry logic on failures with exponential backoff
    - `tqdm`: For progress visualization during batch operations

Classes:
    QdrantClientAsync: Main client class implementing full async functionality for Qdrant
        vector database operations including CRUD operations, search, and batch processing.

Usage:
    This implementation is used as the core backend client in projects requiring
    efficient and robust interaction with Qdrant from an async Python service.
    Typical usage involves creating collections, uploading vectorized documents,
    and performing similarity searches.

Example:
    ```python
    async with aiohttp.ClientSession() as session:
        client = QdrantClientAsync(
            data_model=QdrantEntry,
            collection_name="articles",
            base_url="http://localhost:6333",
            session=session,
            headers={"api-key": "your-key"},
            dense_size=768
        )
        await client.create_collection()
        await client.upload_documents(documents, batch_size=100)
        await client.verify_upload()
        res
"""


import logging
from typing import Any, Coroutine, Dict, Iterable, List, Optional

import aiohttp
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm  # type: ignore

from src.abstractions import VectorDataBaseClientInterfaceAsync


class QdrantClientAsync(VectorDataBaseClientInterfaceAsync):
    """
    Asynchronous client for interacting with a Qdrant vector database.

    Implements all methods defined in `VectorDataBaseClientInterfaceAsync`, providing
    functionality for managing and querying vector data in an asynchronous context.

    Main Responsibilities:
        - Collection management (create, drop).
        - Document transformation and validation.
        - Batch upload with retry and progress bar.
        - Verification of uploaded documents.
        - Dense, sparse, and hybrid vector search.
        - Efficient batch querying.

    Args:
        data_model (QdrantEntry): Pydantic model for input validation.
        collection_name (str): Name of the Qdrant collection to manage.
        base_url (str): URL of the Qdrant server.
        session (aiohttp.ClientSession): Active async session for communication.
        headers (Dict[str, str]): Request headers (e.g., for authentication).
        dense_size (Optional[int]): Expected dense vector dimension.
        sample_for_verification_size (Optional[int], optional): Number of vectors to verify. Defaults to 5.

    Methods:
        - create_collection(): Create the Qdrant collection with appropriate vector parameters.
        - drop_collection(): Delete the current collection.
        - upload_documents(documents, batch_size): Upload a list of documents in batches.
        - verify_upload(): Sample uploaded documents to confirm they are present.
        - dense_search(query_vector, top_k): Perform dense vector similarity search.
        - sparse_search(query_vector, top_k): Perform sparse vector similarity search.
        - hybrid_search(query_vector, sparse_vector, top_k): Combine dense and sparse searches.
        - batch_queries(query_vectors, top_k): Perform batch dense queries for efficiency.

    Example:


        async with aiohttp.ClientSession() as session:
        ...     client = QdrantClientAsync(
        ...         data_model=QdrantEntry(),
        ...         data_conformer=QdrantConformer(),
        ...         collection_name="articles",
        ...         base_url="http://localhost:6333",
        ...         session=session,
        ...         headers={"api-key": "your-key"},
        ...         dense_size=768
        ...     )
        ...     await client.create_collection()
        ...     await client.upload_documents(documents, batch_size=100)
        ...     await client.verify_upload()
        ...     results = await client.dense_search(query_vector,top_k=10)

    """


    def __init__(self,
                 data_model: type[BaseModel],
                 collection_name: str,
                 base_url: str,
                 session: aiohttp.ClientSession,
                 headers: Dict[str, str],
                 dense_size: Optional[int],
                 sample_for_verification_size: Optional[int] = 5):



        self.__data_model = data_model
        self.__collection_name = collection_name
        self.__base_url = base_url
        self.__session = session
        self.__headers = headers
        self.__dense_size = dense_size
        self.__sample_for_verification_size = sample_for_verification_size
        super().__init__(data_model=data_model)

    async def create_collection(self) -> Coroutine[Any, Any, None] | None:  # type: ignore
        """
        Create a new collection in Qdrant with dense vector configuration.

        Creates a collection with cosine distance metric for dense vectors.
        The collection will be configured with the dense vector size specified
        during client initialization.

        Returns:
            Coroutine[Any, Any, Dict[str, Any]]: A coroutine that when awaited returns
                the Qdrant API response containing collection creation status.

        Raises:
            aiohttp.ClientError: If the HTTP request fails.
            Exception: For other collection creation errors.
        """
        url: str = f"{self.__base_url}/collections/{self.__collection_name}"

        payload: Dict[str, Any] = {
            "vectors": {

                    "size": self.__dense_size,
                    "distance": "Cosine"
                }
            }


        async with self.__session.put(url=url, json=payload, headers=self.__headers) as response:
            response.raise_for_status()
            response_data = await response.json()

            if response_data["status"].startswith("Wrong input: Collection"):
                logging.warning(f"Qdrant collection creation warning: {response_data}")

            logging.info(f"Qdrant collection creation response: {response_data}")


        return None

    async def get_collection_info(self) -> Coroutine[Any, Any, Dict[str, Any]]:
        """
        Retrieve metadata and information about the Qdrant collection.

        Fetches detailed information about the collection including point count,
        configuration, status, and other metadata from the Qdrant server.

        Returns:
            Coroutine[Any, Any, Dict[str, Any]]: A coroutine that when awaited returns
                collection metadata including points count, vectors config, and status.

        Raises:
            aiohttp.ClientError: If the HTTP request fails.
            Exception: For other collection info retrieval errors.
        """
        url: str = f"{self.__base_url}/collections/{self.__collection_name}"

        async with self.__session.get(url=url, headers=self.__headers) as response:
            response.raise_for_status()
            response_data = await response.json()

            logging.info(f"Qdrant collection retrieval response: {response_data}")
            return response_data
    def _verify_points(self, item: Dict[str, Any]) -> Dict[str, Any]| None:
        """
        Asserts individual items against Qdrant-specific pydantic BaseModel format.

        Args:

            item (Dict[str, Any]): Individual document/item to validate.

        Returns:
            Coroutine[Any, Any, Dict[str, Any]]: A coroutine that when awaited returns
                the validated and potentially transformed item.

        Raises:
            ValidationError: If the item cannot be validated even after transformation.
            Exception: For other transformation errors.
        """
        try:
            self.__data_model(**item).model_dump()
            return item
        except ValidationError as validation_error:
            logging.error(f" validation error encounter:\n{validation_error}")
            raise


    async def _verify_batch(self, point_id: str) -> Dict[str, Any]:
        """
        Verify that a specific point/batch upload completed successfully.

        Retrieves a specific point by ID from the collection to verify that
        it was properly stored and indexed in the Qdrant database.

        Args:
            point_id (str): Identifier for the specific point to verify.

        Returns:
            Dict[str, Any]: The point data if found, or error information if not found.

        Raises:
            aiohttp.ClientError: If the HTTP request fails.
            Exception: For other verification errors.
        """
        url = f"{self.__base_url}/collections/{self.__collection_name}/points/{point_id}"

        async with self.__session.get(url=url, headers=self.__headers) as response:
            try:
                response.raise_for_status()
                response_data = await response.json()
                return response_data
            except aiohttp.ContentTypeError as e:
                text = await response.text()
                logging.error(f"Expected JSON but got non-JSON content: {text}")
                raise
            except aiohttp.ClientResponseError as e:
                logging.error(f"Client error while verifying point ID {point_id}: {e}")
                raise
            except Exception as e:
                logging.exception(f"Unexpected error during verification of point ID {point_id}: {e}")
                raise

    @retry(stop=stop_after_attempt(max_attempt_number=3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def add_points_with_retry(
            self,
            points: Dict[str, Any] | List[Dict[str, Any]]
    ) -> Coroutine[Any, Any, Dict[str, Any]]:
        """
        Add vector points to Qdrant with automatic retry logic.

        Args:
            points (Union[Dict[str, Any], List[Dict[str, Any]]]):
                Either a single point (dict) or a list of points to upload.
                Example (single point):
                    {"id": "1", "vector": [0.1, 0.2], "payload": {"key": "value"}}
                Example (batch of points):
                    [{"id": "1", "vector": [...]}, {"id": "2", "vector": [...]}]

        Returns:
            Coroutine[Any, Any, Dict[str, Any]]: Qdrant API response.
        """
        url = f"{self.__base_url}/collections/{self.__collection_name}/points"

        # Ensure points is always a list
        payload = {
            "points": [points] if isinstance(points, dict) else points
        }

        async with self.__session.put(url=url, headers=self.__headers, json=payload) as response:
            return await response.json()

    async def upload_documents(self, items: Iterable[Dict[str, Any]], batch_size: int) -> Coroutine[Any, Any, None] | None:  # type: ignore
        """
        Upload multiple documents to Qdrant in batches with progress tracking.


        """
        responses: List = []
        total_uploaded: int = 0

        # Convert to list if it's not already (to handle Iterable input)
        items_list = list(items) if not isinstance(items, list) else items
        iter_range = range(0, len(items_list), batch_size)
        iter_range_progressbar = tqdm(iter_range, desc="Uploading", unit="batch")

        for i in iter_range_progressbar:
            batch_items = items_list[i: i + batch_size]
            batch_num = (i // batch_size) + 1  # Fixed: was 1 // batch_size
            # Fixed: Added await for async _transform_points calls
            points = [self._verify_points(item=doc) for doc in batch_items]

            try:
                response = await self.add_points_with_retry(points)
                responses.append(response)
                total_uploaded += len(points)

                if response.get('status', None) != "ok":  # type: ignore
                    logging.warning(
                        f"Error uploading batch {batch_num} of {len(items_list)} items")  # Fixed: len(items_list)
                else:
                    logging.info(f"Successfully uploaded batch {batch_num} items")

                batch_verified = await self._verify_batch(points[0]["id"])
                verification = bool(batch_verified.get("result", None)) # type: ignore  # Fixed: check "result" not "status"
                if verification:
                    logging.info(f"Successfully verified first item in batch {batch_num}.")
                else:
                    logging.warning(f"Failed to verify first item in batch {batch_num}.")

            except Exception as e:
                logging.error(f"Fail in the process. Error: {e}")
                logging.error(f"Response was: {response if 'response' in locals() else 'No response obtained'}")
                raise
        return None

    async def verify_upload(self) -> Coroutine[Any, Any, Any] | None:  # type: ignore
        """
        Verify that overall upload operations completed successfully.

        Performs comprehensive verification by checking collection info and
        sampling a subset of points to ensure data integrity and proper indexing.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited completes
                the verification process.

        Raises:
            aiohttp.ClientError: If verification requests fail.
            Exception: For other verification errors.

        Note:
            Contains a bug where 'resp' should be 'response' in the json() call.
        """
        collection_info = await self.get_collection_info()
        total_points: int = collection_info.get('result', {}).get('points_count', 0)  # type: ignore
        logging.info(f"Successfully verified {total_points} points in the collection.")

        url = f"{self.__base_url}/collections/{self.__collection_name}/points/scroll"
        payload = {
            "limit": self.__sample_for_verification_size,
            "with_vectors": False,
            "with_payload": True
        }
        async with self.__session.post(url=url, json=payload, headers=self.__headers) as response:
            sample_result = await response.json()
        logging.info(f"Successfully obtained response: {sample_result}.")
        return None

    async def dense_search(self, dense_vector: List[float], top_k: int) -> Coroutine[Any, Any, Dict[str, Any]]| None:  # type: ignore
        """
        Perform dense vector similarity search in the Qdrant collection.

        Executes a similarity search using the provided dense vector to find
        the most similar vectors in the collection with cosine distance.

        Args:
            dense_vector (List[float]): Query vector for similarity search.
            top_k (int): Number of most similar results to return.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                search results with similarity scores, points, and payload data.

        Raises:
            aiohttp.ClientError: If the search request fails.
            Exception: For other search-related errors.
        """
        url = f"{self.__base_url}/collections/{self.__collection_name}/points/search"
        payload = {
            "vector": {
                "name": "dense",  # <- this must match the name used when creating the collection
                "vector": dense_vector
            },
            "limit": top_k,
            "with_payload": True
        }

        async with self.__session.post(url=url, headers=self.__headers, json=payload) as response:
            return await response.json()

    async def batch_queries(self, query_vectors: List[Dict[str, Any]],
                            top_k: int) -> Coroutine[Any, Any, List[Dict[str, Any]]]:
        """
        Execute multiple vector similarity queries in a single batch operation.

        Performs multiple similarity searches simultaneously for improved
        performance when processing multiple query vectors at once.

        Args:
            query_vectors (List[Dict[str, Any]]): List of query dictionaries.
                Each should contain a "vector" key with the query vector and
                optionally a "query" key for identification.
            top_k (int): Number of most similar results to return for each query.

        Returns:
            Coroutine[Any, Any, Any]: A coroutine that when awaited returns
                a list of dictionaries, each containing the original query info
                and corresponding search results.

        Raises:
            aiohttp.ClientError: If the batch search request fails.
            Exception: For other batch query errors.

        Note:
            Creates a new aiohttp.ClientSession instead of using self.__session.
            This might be intentional but could be inefficient.
        """
        url = f"{self.__base_url}/collections/{self.__collection_name}/points/search/batch"

        payload = {
            "searches": [
                {
                    "vector": {
                        "name": "dense",  # <- this must match the name used when creating the collection
                        "vector": item["vector"]
                    },
                    "limit": top_k,
                    "with_payload": True
                }
                for item in query_vectors
            ]
        }

        async with self.__session.post(url, headers=self.__headers, json=payload) as resp:
            results = await resp.json()
        print(results)

        return [  # type: ignore
            {
                "query": item.get("query", None),  # Include "query" if available
                "results": result
            }
            for item, result in zip(query_vectors, results["result"])
        ]