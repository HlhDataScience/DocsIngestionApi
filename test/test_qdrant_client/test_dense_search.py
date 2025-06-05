import pytest
from yarl import URL
from aioresponses import aioresponses

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