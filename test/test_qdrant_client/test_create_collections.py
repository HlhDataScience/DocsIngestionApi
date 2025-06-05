import pytest
from aioresponses import aioresponses
from yarl import URL  # type: ignore


@pytest.mark.asyncio
async def test_created_collection_success(qdrant_client):
    url = URL("http://localhost:6333/collections/testing_qdrant_client")

    with aioresponses() as mocked:

        mocked.put(url, status=200)

        result = await qdrant_client.create_collection()

        assert result is None
        assert ("PUT", url) in mocked.requests


@pytest.mark.asyncio
async def test_created_collection_failure(qdrant_client):
    url = URL("http://localhost:6333/collections/testing_qdrant_client")

    with aioresponses() as mocked:
        mocked.put(url, status=404)
        result = await qdrant_client.create_collection()

        assert result is None
        assert ("PUT", url) in mocked.requests

