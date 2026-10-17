from __future__ import annotations

import pytest
from conftest import FakeClock

from app.core.actions import ActionExecutor
from app.core.discovery import DiscoveryService
from app.core.engine import AreaEngine
from app.core.ir_transport import HomeAssistantRemoteTransport
from app.models import Mode


@pytest.mark.asyncio
async def test_cinema_then_tv_runs_scene_and_off_confirmation(fake_ha, cinema_profile):
    discovery = DiscoveryService(fake_ha)
    events = []

    async def record(**kwargs):
        events.append(kwargs)

    clock = FakeClock()
    actions = ActionExecutor(fake_ha, discovery, record)
    ir = HomeAssistantRemoteTransport(fake_ha, discovery, record, sleep=clock.sleep, monotonic=clock.monotonic)
    engine = AreaEngine(cinema_profile, actions, ir, discovery, record)

    await engine.request_mode(Mode.CINEMA)
    await engine.wait_idle()
    assert engine.mode.value == "cinema"
    assert engine.phase.value == "active"
    assert any(call["entity_id"] == "switch.tela" and call["service"] == "turn_on" for call in fake_ha.calls)
    on_calls = [call for call in fake_ha.calls if call["domain"] == "remote"]
    assert len(on_calls) == 1
    await engine.request_mode(Mode.CINEMA)
    await engine.wait_idle()
    assert len([call for call in fake_ha.calls if call["domain"] == "remote"]) == 1

    await engine.request_mode(Mode.TV)
    await engine.wait_idle()
    off_calls = [call for call in fake_ha.calls if call["domain"] == "remote"]
    assert len(off_calls) == 3
    assert engine.mode.value == "tv"
    assert engine.projector_intent == "off_commanded_unknown_physical"
    assert clock.value == 5.0
    assert any(item["event"] == "transition_completed" for item in events)


@pytest.mark.asyncio
async def test_external_tv_on_does_not_move_screen_or_send_ir(fake_ha, cinema_profile):
    discovery = DiscoveryService(fake_ha)
    events = []

    async def record(**kwargs):
        events.append(kwargs)

    actions = ActionExecutor(fake_ha, discovery, record)
    ir = HomeAssistantRemoteTransport(fake_ha, discovery, record)
    engine = AreaEngine(cinema_profile, actions, ir, discovery, record)
    await engine.handle_state_event(
        {
            "data": {
                "entity_id": "media_player.tv_cinema",
                "old_state": {"state": "off"},
                "new_state": {"state": "on"},
            }
        }
    )
    await engine._external_tv_task
    assert engine.mode.value == "tv"
    assert not [call for call in fake_ha.calls if call["domain"] == "remote"]
    assert not [call for call in fake_ha.calls if call["entity_id"] == "switch.tela"]
    assert any(call["service"] == "select_source" and call["data"]["source"] == "TV Audio" for call in fake_ha.calls)


@pytest.mark.asyncio
async def test_climate_uses_high_then_low_without_fan_oscillation(fake_ha, cinema_profile):
    discovery = DiscoveryService(fake_ha)
    actions = ActionExecutor(fake_ha, discovery)
    await actions.apply_climate(cinema_profile)
    assert any(call["service"] == "set_fan_mode" and call["data"]["fan_mode"] == "high" for call in fake_ha.calls)
    climate_state = next(item for item in fake_ha.snapshot["states"] if item["entity_id"] == "climate.ar_cinema")
    climate_state["attributes"]["current_temperature"] = 22.0
    await actions.apply_climate(cinema_profile)
    assert any(call["service"] == "set_fan_mode" and call["data"]["fan_mode"] == "low" for call in fake_ha.calls)
    fan_calls_before = len([call for call in fake_ha.calls if call["service"] == "set_fan_mode"])
    climate_state["attributes"]["current_temperature"] = 23.0
    await actions.apply_climate(cinema_profile)
    assert len([call for call in fake_ha.calls if call["service"] == "set_fan_mode"]) == fan_calls_before
