import pytest
from aioresponses import aioresponses
from yarl import URL  # type: ignore

@pytest.mark.asyncio
async def test_get_collection_info(qdrant_client):
    url = URL("http://localhost:6333/collections/testing_qdrant_client")
    fake_paylod = {'result':
                       {'status':'green',
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
                                   'wal_config': {'wal_capacity_mb': 32, 'wal_segments_ahead': 0}, 'quantization_config': None, 'strict_mode_config': {'enabled': False}}, 'payload_schema': {}}, 'status': 'ok', 'time': 0.09945158}
    with aioresponses() as mocked:
        mocked.get(url, status=200, payload=fake_paylod)

        response = await qdrant_client.get_collection_info()

        assert isinstance(response, dict)
        assert isinstance(response.get('result', None), dict)
        assert response["result"]["status"] == "green"
