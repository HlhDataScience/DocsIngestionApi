import pytest
from yarl import URL
from aioresponses import aioresponses


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