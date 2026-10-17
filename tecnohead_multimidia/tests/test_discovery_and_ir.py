from __future__ import annotations

import pytest
from conftest import FakeClock

from app.core.discovery import AreaValidationError, DiscoveryService
from app.core.ir_transport import HomeAssistantRemoteTransport


@pytest.mark.asyncio
async def test_entities_are_strictly_scoped_to_effective_area(fake_ha):
    discovery = DiscoveryService(fake_ha)
    areas = await discovery.areas({"cinema": None}, refresh=True)
    cinema = next(area for area in areas if area.area_id == "cinema")
    ids = {entity.entity_id for entity in cinema.entities}
    assert "remote.ir_cinema" in ids
    assert "remote.ir_infra" not in ids
    assert discovery.suggest_remote("cinema") == "remote.ir_cinema"


@pytest.mark.asyncio
async def test_remote_validation_rejects_entity_from_other_area(fake_ha, cinema_profile):
    discovery = DiscoveryService(fake_ha)
    with pytest.raises(AreaValidationError):
        await discovery.validate_remote("cinema", "remote.ir_infra")


@pytest.mark.asyncio
async def test_off_is_two_independent_ha_calls_with_five_seconds_after_first_return(fake_ha, cinema_profile):
    discovery = DiscoveryService(fake_ha)
    clock = FakeClock()
    transport = HomeAssistantRemoteTransport(fake_ha, discovery, sleep=clock.sleep, monotonic=clock.monotonic)
    result = await transport.send_off(cinema_profile)
    remote_calls = [call for call in fake_ha.calls if call["domain"] == "remote"]
    assert len(remote_calls) == 2
    assert all(call["service"] == "send_command" for call in remote_calls)
    assert all(call["entity_id"] == "remote.ir_cinema" for call in remote_calls)
    assert all(call["data"]["command"].startswith("b64:") for call in remote_calls)
    assert all("num_repeats" not in call["data"] for call in remote_calls)
    assert result["gaps_after_return_seconds"] == [5.0]
