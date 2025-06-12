import pytest
from aioresponses import aioresponses
from yarl import URL  # type: ignore
from aiohttp.client_exceptions import ClientResponseError

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

