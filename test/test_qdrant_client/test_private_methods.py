import pytest
from aioresponses import aioresponses
from yarl import URL

from pydantic import ValidationError
def test_transform_points(qdrant_client):
    fake_conformed_document = {'id': '36867605-88e1-4a14-ae45-d930396178ed',
     'vector': {'dense': [-0.013694579] *3072},
     'payload': {'title': '¿Qué sucede si se superan asignaturas en convocatoria extraordinaria?',
      'document': 'La defensa del TFE se programará automáticamente para la convocatoria extraordinaria de defensa.'}}
    conformed_item = qdrant_client._verify_points(item=fake_conformed_document)

    assert isinstance(conformed_item, dict)
    assert conformed_item



def test_transform_points_fail(qdrant_client):
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