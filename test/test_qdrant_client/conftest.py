
import aiohttp
import pytest_asyncio

from src.client.implementations import QdrantClientAsync
from src.models.validation_schemas import QdrantValidator
QDRANT_API_KEY = "your-api-key"
QDRANT_BASE_URL = "http://localhost:6333"
@pytest_asyncio.fixture()
async def qdrant_client():


    async with aiohttp.ClientSession() as session:
        client = QdrantClientAsync(data_model=QdrantValidator, collection_name="testing_qdrant_client",
                                   base_url=QDRANT_BASE_URL, session=session, headers={
                "Content-Type": "application/json",
                "api-key": QDRANT_API_KEY,
            }, dense_size=3072)
        yield client