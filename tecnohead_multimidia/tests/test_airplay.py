from __future__ import annotations

import asyncio

import pytest
from test_audio import _audio_snapshot, _config

from app.core.airplay import AirPlayEndpointManager, AudioStreamBroker
from app.core.audio import AudioActionError, AudioManager
from app.core.discovery import DiscoveryService
from app.models import AudioZoneProfile
from app.settings import Settings


async def test_audio_stream_broker_replays_recent_chunk_and_fans_out():
    broker = AudioStreamBroker()
    await broker.publish(b"first")
    stream = broker.subscribe()
    assert await anext(stream) == b"first"
    await broker.publish(b"second")
    assert await asyncio.wait_for(anext(stream), timeout=0.2) == b"second"
    await stream.aclose()
    assert broker.client_count == 0


def test_airplay_config_has_distinct_airplay2_identity_and_port(tmp_path):
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    zone = AudioZoneProfile(
        zone_id="kitchen",
        airplay={"enabled": True, "service_name": "TecnoHead Cozinha", "stable_id": "0123456789abcdef"},
    )
    config = manager._config_text(zone, 7000)
    assert 'service_type = "airplay2"' in config
    assert 'name = "TecnoHead Cozinha"' in config
    assert "port = 7000;" in config
    assert 'nqptp_shared_memory_interface_name = "/tecnohead-kitchen"' in config


async def test_airplay_output_never_takes_pool_arc_without_explicit_policy(fake_ha):
    _audio_snapshot(fake_ha)
    discovery = DiscoveryService(fake_ha)
    manager = AudioManager(fake_ha, discovery)
    config = _config()
    with pytest.raises(AudioActionError, match="HDMI ARC tem prioridade"):
        await manager.start_airplay_output(config, "pool", "http://192.0.2.1:8099/stream")
    assert not any(call["service"] == "play_media" for call in fake_ha.calls)


async def test_airplay_output_uses_ha_play_media_for_kitchen(fake_ha):
    _audio_snapshot(fake_ha)
    discovery = DiscoveryService(fake_ha)
    manager = AudioManager(fake_ha, discovery)
    config = _config()
    result = await manager.start_airplay_output(config, "kitchen", "http://192.0.2.1:8099/stream")
    assert result["transport"] == "home_assistant_media_player_play_media"
    assert fake_ha.calls[-1] == {
        "domain": "media_player",
        "service": "play_media",
        "entity_id": "media_player.kitchen_amp",
        "data": {
            "media_content_type": "music",
            "media_content_id": "http://192.0.2.1:8099/stream",
        },
    }


async def test_airplay_report_exposes_not_configured_before_enabled(tmp_path, fake_ha):
    events = []

    async def record(**kwargs):
        events.append(kwargs)

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), fake_ha, None, record)
    report = manager.report()
    assert report["state"] == "not_configured"
    assert report["physical_audio"] == "not_tested"
    assert report["endpoints"] == {}
