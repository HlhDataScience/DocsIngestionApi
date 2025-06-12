from unittest.mock import patch

from aiohttp.client_exceptions import ClientResponseError
import pytest
from yarl import URL
from aioresponses import aioresponses
from pydantic import ValidationError










@pytest.mark.asyncio
async def test_created_collection_success(qdrant_client):
    with aioresponses() as mock:
        mock.put(
            "http://localhost:6333/collections/testing_qdrant_client",
            status=200,
            payload={"status": "ok"}
        )
        await qdrant_client.create_collection()

@pytest.mark.asyncio
async def test_created_collection_failure(qdrant_client):
    url = URL("http://localhost:6333/collections/testing_qdrant_client")

    with aioresponses() as mocked:
        # Simulate a 404 error from the Qdrant server
        mocked.put(url, status=404, payload={"status": "error"})

        with pytest.raises(ClientResponseError) as exc_info:
            await qdrant_client.create_collection()

        assert exc_info.value.status == 404
        assert ("PUT", url) in mocked.requests


@pytest.mark.asyncio
async def test_batch_queries_success(qdrant_client):
    """Test successful batch queries."""
    url = URL("http://localhost:6333/collections/testing_qdrant_client/points/search/batch")

    query_vectors = [
        {"vector": [0.1, 0.2, 0.3], "query": "first query"},
        {"vector": [0.4, 0.5, 0.6], "query": "second query"}
    ]

    batch_response = {
        "result": [
            [
                {"id": "point1", "score": 0.95, "payload": {"content": "result 1 for query 1"}}
            ],
            [
                {"id": "point2", "score": 0.88, "payload": {"content": "result 1 for query 2"}},
                {"id": "point3", "score": 0.82, "payload": {"content": "result 2 for query 2"}}
            ]
        ],
        "status": "ok"
    }

    with aioresponses() as mocked:
        mocked.post(url, payload=batch_response, status=200)

        result = await qdrant_client.batch_queries(query_vectors, top_k=3)

        assert len(result) == 2
        assert result[0]["query"] == "first query"
        assert result[1]["query"] == "second query"
        assert result[0]["results"] == batch_response["result"][0]
        assert result[1]["results"] == batch_response["result"][1]

        assert ("POST", url) in mocked.requests

        # Verify batch payload structure
        request_data = mocked.requests[("POST", url)][0].kwargs["json"]
        assert "searches" in request_data
        assert len(request_data["searches"]) == 2

        for i, search in enumerate(request_data["searches"]):
            assert search["vector"]["name"] == "dense"
            assert search["vector"]["vector"] == query_vectors[i]["vector"]
            assert search["limit"] == 3
            assert search["with_payload"] is True


@pytest.mark.asyncio
async def test_batch_queries_without_query_field(qdrant_client):
    """Test batch queries when query field is not provided."""
    url = URL("http://localhost:6333/collections/testing_qdrant_client/points/search/batch")

    query_vectors = [
        {"vector": [0.1, 0.2, 0.3]},  # No "query" field
        {"vector": [0.4, 0.5, 0.6]}  # No "query" field
    ]

    batch_response = {
        "result": [
            [{"id": "point1", "score": 0.95}],
            [{"id": "point2", "score": 0.88}]
        ],
        "status": "ok"
    }

    with aioresponses() as mocked:
        mocked.post(url, payload=batch_response, status=200)

        result = await qdrant_client.batch_queries(query_vectors, top_k=5)

        assert len(result) == 2
        assert result[0]["query"] is None  # Should be None when not provided
        assert result[1]["query"] is None
        assert result[0]["results"] == batch_response["result"][0]
        assert result[1]["results"] == batch_response["result"][1]


@pytest.mark.asyncio
async def test_batch_queries_empty_list(qdrant_client):
    """Test batch queries with empty query list."""
    url = URL("http://localhost:6333/collections/testing_qdrant_client/points/search/batch")

    batch_response = {
        "result": [],
        "status": "ok"
    }

    with aioresponses() as mocked:
        mocked.post(url, payload=batch_response, status=200)

        result = await qdrant_client.batch_queries([], top_k=5)

        assert result == []
        assert ("POST", url) in mocked.requests


@pytest.mark.asyncio
async def test_get_collection_info(qdrant_client):
    url = URL("http://localhost:6333/collections/testing_qdrant_client")
    fake_paylod = {'result':
                       {'status': 'green',
                        'optimizer_status': 'ok',
                        'indexed_vectors_count': 0,
                        'points_count': 6,
                        'segments_count': 2,
                        'config': {'params':
                                       {'vectors':
                                            {'dense':
                                                 {'size': 3072, 'distance': 'Cosine'}},
                                        'shard_number': 1,
                                        'replication_factor': 1,
                                        'write_consistency_factor': 1,
                                        'on_disk_payload': True},
                                   'hnsw_config':
                                       {'m': 16, 'ef_construct': 100,
                                        'full_scan_threshold': 10000,
                                        'max_indexing_threads': 0,
                                        'on_disk': False},
                                   'optimizer_config':
                                       {'deleted_threshold': 0.2,
                                        'vacuum_min_vector_number': 1000,
                                        'default_segment_number': 0,
                                        'max_segment_size': None,
                                        'memmap_threshold': None,
                                        'indexing_threshold': 20000,
                                        'flush_interval_sec': 5,
                                        'max_optimization_threads': None},
                                   'wal_config': {'wal_capacity_mb': 32, 'wal_segments_ahead': 0},
                                   'quantization_config': None, 'strict_mode_config': {'enabled': False}},
                        'payload_schema': {}}, 'status': 'ok', 'time': 0.09945158}
    with aioresponses() as mocked:
        mocked.get(url, status=200, payload=fake_paylod)

        response = await qdrant_client.get_collection_info()

        assert isinstance(response, dict)
        assert isinstance(response.get('result', None), dict)
        assert response["result"]["status"] == "green"


def test_verify_points(qdrant_client):
    fake_conformed_document = {'id': '36867605-88e1-4a14-ae45-d930396178ed',
                               'vector': {'dense': [-0.013694579] * 3072},
                               'payload': {
                                   'title': '¿Qué sucede si se superan asignaturas en convocatoria extraordinaria?',
                                   'document': 'La defensa del TFE se programará automáticamente para la convocatoria extraordinaria de defensa.'}}
    conformed_item = qdrant_client._verify_points(item=fake_conformed_document)

    assert isinstance(conformed_item, dict)
    assert conformed_item


def test_verify_points_fail(qdrant_client):
    # This document is likely malformed, e.g., missing 'id' or 'metadata'
    fake_not_conformed_document = {
        'vector': [0.01] * 3072  # Assuming this vector size is valid, but structure is not
    }

    with pytest.raises(ValidationError):  # or your custom error
        qdrant_client._verify_points(fake_not_conformed_document)


@pytest.mark.asyncio
async def test_verify_batch_success(qdrant_client):
    """Test successful verification of a batch point."""
    point_id = "test_point_123"
    url = URL(f"http://localhost:6333/collections/testing_qdrant_client/points/{point_id}")

    # Mock response data for successful verification
    mock_response = {
        "result": {
            "id": point_id,
            "payload": {"content": "test content"},
            "vector": [0.1, 0.2, 0.3]
        },
        "status": "ok",
        "time": 0.001
    }

    with aioresponses() as mocked:
        mocked.get(url, payload=mock_response, status=200)

        result = await qdrant_client._verify_batch(point_id)

        assert result == mock_response
        assert ("GET", url) in mocked.requests


@pytest.mark.asyncio
async def test_verify_batch_point_not_found(qdrant_client):
    """Test verification when point is not found."""
    point_id = "nonexistent_point"
    url = URL(f"http://localhost:6333/collections/testing_qdrant_client/points/{point_id}")

    # Mock response for point not found
    mock_response = {
        "result": None,
        "status": "ok",
        "time": 0.001
    }

    with aioresponses() as mocked:
        mocked.get(url, payload=mock_response, status=200)

        result = await qdrant_client._verify_batch(point_id)

        assert result == mock_response
        assert result["result"] is None
        assert ("GET", url) in mocked.requests


@pytest.mark.asyncio
async def test_verify_batch_http_error(qdrant_client):
    """Test verification when HTTP error occurs."""
    point_id = "test_point_error"
    url = URL(f"http://localhost:6333/collections/testing_qdrant_client/points/{point_id}")

    with aioresponses() as mocked:
        mocked.get(url, status=404)

        # The method doesn't handle HTTP errors explicitly, so it should propagate
        with pytest.raises(Exception):
            await qdrant_client._verify_batch(point_id)

        assert ("GET", url) in mocked.requests


@pytest.mark.asyncio
async def test_verify_batch_with_different_point_types(qdrant_client):
    """Test verification with different point ID types (string, int)."""
    # Test with string ID
    string_point_id = "string_point_123"
    url_string = URL(f"http://localhost:6333/collections/testing_qdrant_client/points/{string_point_id}")

    mock_response_string = {
        "result": {"id": string_point_id, "payload": {}},
        "status": "ok"
    }

    # Test with integer ID
    int_point_id = 12345
    url_int = URL(f"http://localhost:6333/collections/testing_qdrant_client/points/{int_point_id}")

    mock_response_int = {
        "result": {"id": int_point_id, "payload": {}},
        "status": "ok"
    }

    with aioresponses() as mocked:
        mocked.get(url_string, payload=mock_response_string, status=200)
        mocked.get(url_int, payload=mock_response_int, status=200)

        # Test string ID
        result_string = await qdrant_client._verify_batch(string_point_id)
        assert result_string == mock_response_string

        # Test integer ID
        result_int = await qdrant_client._verify_batch(int_point_id)
        assert result_int == mock_response_int

        assert ("GET", url_string) in mocked.requests
        assert ("GET", url_int) in mocked.requests


@pytest.mark.asyncio
async def test_dense_search_success(qdrant_client):
    """Test successful dense vector search."""
    url = URL("http://localhost:6333/collections/testing_qdrant_client/points/search")

    query_vector = [0.1, 0.2, 0.3, 0.4]
    top_k = 5

    search_response = {
        "result": [
            {
                "id": "point1",
                "score": 0.95,
                "payload": {"content": "most similar document"},
                "vector": None
            },
            {
                "id": "point2",
                "score": 0.87,
                "payload": {"content": "second most similar"},
                "vector": None
            }
        ],
        "status": "ok",
        "time": 0.003
    }

    with aioresponses() as mocked:
        mocked.post(url, payload=search_response, status=200)

        result = await qdrant_client.dense_search(query_vector, top_k)

        assert result == search_response
        assert ("POST", url) in mocked.requests

        # Verify search payload
        request_data = mocked.requests[("POST", url)][0].kwargs["json"]
        assert request_data["vector"]["name"] == "dense"
        assert request_data["vector"]["vector"] == query_vector
        assert request_data["limit"] == top_k
        assert request_data["with_payload"] is True


@pytest.mark.asyncio
async def test_dense_search_no_results(qdrant_client):
    """Test dense search with no results."""
    url = URL("http://localhost:6333/collections/testing_qdrant_client/points/search")

    query_vector = [0.1, 0.2, 0.3]

    search_response = {
        "result": [],
        "status": "ok",
        "time": 0.001
    }

    with aioresponses() as mocked:
        mocked.post(url, payload=search_response, status=200)

        result = await qdrant_client.dense_search(query_vector, 10)

        assert result == search_response
        assert len(result["result"]) == 0


@pytest.mark.asyncio
async def test_upload_documents_success(qdrant_client):
    """Test successful document upload."""
    url = URL("http://localhost:6333/collections/testing_qdrant_client/points")
    verify_url_pattern = "http://localhost:6333/collections/testing_qdrant_client/points/"

    documents = [
        {"id": "doc1", "vector": {"dense": [0.1, 0.2, 0.3]}, "payload": {"content": "doc 1"}},
        {"id": "doc2", "vector": {"dense": [0.4, 0.5, 0.6]}, "payload": {"content": "doc 2"}}
    ]

    upload_response = {"result": {"operation_id": 12348}, "status": "ok"}
    verify_response = {"result": {"id": "doc1"}, "status": "ok"}

    with aioresponses() as mocked:
        # Mock upload response
        mocked.put(url, payload=upload_response, status=200)
        # Mock verification response
        mocked.get(URL(f"{verify_url_pattern}doc1"), payload=verify_response, status=200)

        # Mock the _verify_points method to return the input unchanged
        with patch.object(qdrant_client, '_verify_points', side_effect=lambda item: item):
            await qdrant_client.upload_documents(documents, batch_size=2)

        # Verify upload was called
        assert ("PUT", url) in mocked.requests
        # Verify verification was called
        assert ("GET", URL(f"{verify_url_pattern}doc1")) in mocked.requests


@pytest.mark.asyncio
async def test_upload_documents_with_transformation(qdrant_client):
    """Test document upload with transformation."""
    url = URL("http://localhost:6333/collections/testing_qdrant_client/points")
    verify_url_pattern = "http://localhost:6333/collections/testing_qdrant_client/points/"

    original_doc = {"content": "test", "embedding": [0.1, 0.2, 0.3]}
    transformed_doc = {"id": "transformed_1", "vector": {"dense": [0.1, 0.2, 0.3]}, "payload": {"content": "test"}}

    upload_response = {"result": {"operation_id": 12349}, "status": "ok"}
    verify_response = {"result": {"id": "transformed_1"}, "status": "ok"}

    with aioresponses() as mocked:
        mocked.put(url, payload=upload_response, status=200)
        mocked.get(URL(f"{verify_url_pattern}transformed_1"), payload=verify_response, status=200)

        # Mock transformation
        with patch.object(qdrant_client, '_verify_points', return_value=transformed_doc):
            await qdrant_client.upload_documents([original_doc], batch_size=1)

        assert ("PUT", url) in mocked.requests


@pytest.mark.asyncio
async def test_upload_documents_batch_processing(qdrant_client):
    documents = [
        {"id": f"doc{i}", "vector": {"dense": [0.1, 0.2, 0.3]}, "payload": {"content": f"doc {i}"}}
        for i in range(5)
    ]

    upload_response = {"result": {"operation_id": 12350}, "status": "ok"}
    verify_response = {"result": {"id": "doc0"}, "status": "ok"}

    with patch.object(qdrant_client, '_verify_points', side_effect=lambda item: item), \
            patch.object(qdrant_client, 'add_points_with_retry', return_value=upload_response) as mock_add, \
            patch.object(qdrant_client, '_verify_batch', return_value=verify_response) as mock_verify:
        await qdrant_client.upload_documents(documents, batch_size=2)

        # Verify add_points_with_retry was called 3 times (for 3 batches)
        assert mock_add.call_count == 3
        # Verify _verify_batch was called 3 times
        assert mock_verify.call_count == 3


@pytest.mark.asyncio
async def test_verify_upload_success(qdrant_client):
    """Test successful upload verification."""
    info_url = URL("http://localhost:6333/collections/testing_qdrant_client")
    scroll_url = URL("http://localhost:6333/collections/testing_qdrant_client/points/scroll")

    collection_info_response = {
        "result": {
            "status": "green",
            "points_count": 100,
            "indexed_vectors_count": 100,
            "vectors_count": 100
        },
        "status": "ok"
    }

    scroll_response = {
        "result": {
            "points": [
                {"id": "point1", "payload": {"content": "test 1"}},
                {"id": "point2", "payload": {"content": "test 2"}}
            ],
            "next_page_offset": None
        },
        "status": "ok"
    }

    with aioresponses() as mocked:
        mocked.get(info_url, payload=collection_info_response, status=200)
        mocked.post(scroll_url, payload=scroll_response, status=200)

        await qdrant_client.verify_upload()

        assert ("GET", info_url) in mocked.requests
        assert ("POST", scroll_url) in mocked.requests

        # Verify scroll request payload
        scroll_request = mocked.requests[("POST", scroll_url)][0]
        scroll_payload = scroll_request.kwargs["json"]
        assert scroll_payload["limit"] == 5  # default sample size
        assert scroll_payload["with_vectors"] is False
        assert scroll_payload["with_payload"] is True