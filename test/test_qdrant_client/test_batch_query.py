import pytest
from yarl import URL
from aioresponses import aioresponses

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