import pytest
from yarl import URL
from aioresponses import aioresponses
from unittest.mock import patch

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

        # Mock the _transform_points method to return the input unchanged
        with patch.object(qdrant_client, '_transform_points', side_effect=lambda item: item):
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
        with patch.object(qdrant_client, '_transform_points', return_value=transformed_doc):
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

    with patch.object(qdrant_client, '_transform_points', side_effect=lambda item: item), \
            patch.object(qdrant_client, 'add_points_with_retry', return_value=upload_response) as mock_add, \
            patch.object(qdrant_client, '_verify_batch', return_value=verify_response) as mock_verify:
        await qdrant_client.upload_documents(documents, batch_size=2)

        # Verify add_points_with_retry was called 3 times (for 3 batches)
        assert mock_add.call_count == 3
        # Verify _verify_batch was called 3 times
        assert mock_verify.call_count == 3