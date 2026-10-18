from __future__ import annotations

import asyncio
import base64
import contextlib
import socket

import pytest
from test_audio import _audio_snapshot, _config

from app.core.airplay import (
    METADATA_STREAM_LIMIT,
    AirPlayEndpointManager,
    AudioStreamBroker,
    _Endpoint,
    airplay_volume_to_percent,
)
from app.core.audio import AudioManager
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
    assert 'regtype = "_airplay._tcp";' in config
    assert 'nqptp_shared_memory_interface_name = "/tecnohead-kitchen"' in config
    assert 'ignore_volume_control = "yes";' in config
    assert "run_this_when_volume_is_set = \"/usr/local/bin/tecnohead-airplay-volume-hook" in config
    assert 'pipe_name = "' in config
    assert 'metadata = {' in config


def test_airplay_volume_maps_source_db_to_linear_player_percent():
    assert airplay_volume_to_percent("0.00") == 100
    assert airplay_volume_to_percent("-15.00") == 50
    assert airplay_volume_to_percent("-30.00") == 0
    assert airplay_volume_to_percent("-144.00") == 0
    assert airplay_volume_to_percent("not-a-volume") is None


async def test_airplay_metadata_reader_decodes_pvol_payload(tmp_path):
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    payload = b"-15.00,-15.00,-30.00,0.00"
    encoded = base64.b64encode(payload)
    stream = asyncio.StreamReader()
    stream.feed_data(
        b"<item><type>73736e63</type><code>70766f6c</code><length>"
        + str(len(payload)).encode()
        + b"</length>\n<data encoding=\"base64\">\n"
        + encoded
        + b"\n</data></item>\n"
    )
    stream.feed_eof()
    header = await stream.readline()
    assert await manager._read_metadata_item(stream, header) == ("ssnc", "pvol", payload)


async def test_airplay_metadata_reader_accepts_large_item_before_pvol(tmp_path):
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    payload = b"x" * 70000
    encoded = base64.b64encode(payload)
    stream = asyncio.StreamReader(limit=METADATA_STREAM_LIMIT)
    stream.feed_data(
        b"<item><type>73736e63</type><code>636f706c</code><length>"
        + str(len(payload)).encode()
        + b"</length>\n<data encoding=\"base64\">\n"
        + encoded
        + b"\n</data></item>\n"
    )
    stream.feed_eof()
    header = await stream.readline()
    item = await manager._read_metadata_item(stream, header)
    assert item == ("ssnc", "copl", payload)


async def test_airplay_pvol_is_forwarded_to_zone_player(fake_ha, tmp_path):
    _audio_snapshot(fake_ha)
    discovery = DiscoveryService(fake_ha)
    audio = AudioManager(fake_ha, discovery)
    events = []

    async def record(**kwargs):
        events.append(kwargs)

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), fake_ha, audio, record)
    manager._config = _config()
    zone = manager._config.zones[0]
    endpoint = _Endpoint(zone=zone, port=7000)

    await manager._forward_airplay_volume(endpoint, 50)

    assert endpoint.last_airplay_volume_percent == 50
    assert fake_ha.calls[-1]["service"] == "volume_set"
    assert fake_ha.calls[-1]["data"] == {"volume_level": 0.3}
    assert events[-1]["event"] == "airplay_volume_forwarded"


async def test_airplay_volume_hook_is_forwarded_to_zone_player(tmp_path):
    if not hasattr(socket, "AF_UNIX"):
        pytest.skip("sockets Unix são usados somente no runtime Linux do App")
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    zone = AudioZoneProfile(
        zone_id="kitchen",
        area_id="kitchen",
        media_player_entity_id="media_player.kitchen",
        airplay={"enabled": True, "service_name": "TecnoHead Cozinha", "stable_id": "0123456789abcdef"},
    )
    endpoint = _Endpoint(zone=zone, port=7000)
    socket_path = tmp_path / "volume.sock"
    endpoint.volume_socket = manager._prepare_volume_socket(socket_path)
    forwarded: list[int] = []

    async def forward(_endpoint, volume_percent):
        forwarded.append(volume_percent)

    manager._forward_airplay_volume = forward  # type: ignore[method-assign]
    client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    task = asyncio.create_task(manager._consume_volume_hook(endpoint))
    try:
        client.sendto(b"-15.00", str(socket_path))
        await asyncio.wait_for(_wait_for_value(forwarded), timeout=1)
        assert forwarded == [50]
        assert endpoint.last_airplay_volume_source == "shairport_volume_hook"
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        client.close()
        manager._close_volume_socket(endpoint.volume_socket, socket_path)


async def _wait_for_value(values: list[int]) -> None:
    while not values:
        await asyncio.sleep(0.01)


def test_airplay_config_binds_runtime_lan_address_without_persisting_it(tmp_path):
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    manager._lan_address = "192.0.2.10"
    zone = AudioZoneProfile(
        zone_id="pool",
        airplay={"enabled": True, "service_name": "TecnoHead Piscina", "stable_id": "fedcba9876543210"},
    )
    config = manager._config_text(zone, 7001)
    assert 'address = "192.0.2.10";' in config


def test_private_mdns_fallback_uses_one_shared_bus_and_avahi(tmp_path):
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    dbus_config = manager._private_dbus_config(tmp_path / "system_bus_socket")
    avahi_config = manager._private_avahi_config()
    assert "org.freedesktop.Avahi" in dbus_config
    assert "unix:path=" in dbus_config
    assert '<allow send_destination="*"/>' in dbus_config
    assert '<allow receive_type="method_return"/>' in dbus_config
    assert '<allow receive_type="signal"/>' in dbus_config
    assert "enable-dbus=yes" in avahi_config
    assert "disable-user-service-publishing=no" in avahi_config


async def test_airplay_output_allows_pool_request_when_last_source_is_arc(fake_ha):
    _audio_snapshot(fake_ha)
    discovery = DiscoveryService(fake_ha)
    manager = AudioManager(fake_ha, discovery)
    config = _config()
    result = await manager.start_airplay_output(config, "pool", "http://192.0.2.1:18199/stream")
    assert result["transport"] == "home_assistant_media_player_play_media"
    assert fake_ha.calls[-1] == {
        "domain": "media_player",
        "service": "play_media",
        "entity_id": "media_player.pool_amp",
        "data": {
            "media_content_type": "music",
            "media_content_id": "http://192.0.2.1:18199/stream",
        },
    }


async def test_airplay_output_uses_ha_play_media_for_kitchen(fake_ha):
    _audio_snapshot(fake_ha)
    discovery = DiscoveryService(fake_ha)
    manager = AudioManager(fake_ha, discovery)
    config = _config()
    result = await manager.start_airplay_output(config, "kitchen", "http://192.0.2.1:18199/stream")
    assert result["transport"] == "home_assistant_media_player_play_media"
    assert fake_ha.calls[-1] == {
        "domain": "media_player",
        "service": "play_media",
        "entity_id": "media_player.kitchen_amp",
        "data": {
            "media_content_type": "music",
            "media_content_id": "http://192.0.2.1:18199/stream",
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
