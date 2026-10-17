from __future__ import annotations

import pytest

from app.core.store import ConfigStore
from app.models import AreaProfile


@pytest.mark.asyncio
async def test_store_round_trip_is_private_and_atomic(tmp_path):
    store = ConfigStore(tmp_path)
    config = await store.load()
    assert config.installation_id
    await store.upsert_area(AreaProfile(area_id="cinema", enabled=False))
    loaded = await ConfigStore(tmp_path).load()
    assert loaded.areas[0].area_id == "cinema"
    assert (tmp_path / "config.json").exists()
