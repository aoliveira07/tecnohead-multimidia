from __future__ import annotations

import asyncio
import base64
import contextlib
import plistlib
import socket
import time
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from test_audio import _audio_snapshot, _config

from app.core.airplay import (
    MAX_METADATA_ITEM_BYTES,
    METADATA_STREAM_LIMIT,
    AirPlayEndpointManager,
    AudioStreamBroker,
    MediaRemoteProbe,
    _Endpoint,
    _monotonic_to_iso,
    airplay_volume_to_percent,
    percent_to_airplay_volume_db,
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
    assert 'dbus_service_bus = "session"' in config
    assert 'mpris_service_bus = "session"' in config
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


def test_airplay_volume_maps_physical_player_percent_to_source_db():
    assert percent_to_airplay_volume_db(0) == -144.0
    assert percent_to_airplay_volume_db(50) == -15.0
    assert percent_to_airplay_volume_db(100) == 0.0
    assert percent_to_airplay_volume_db(150) == 0.0


def test_volume_diagnostic_uses_wall_clock_not_monotonic_epoch():
    rendered = _monotonic_to_iso(time.monotonic())
    assert rendered is not None
    assert abs((datetime.now(UTC) - datetime.fromisoformat(rendered)).total_seconds()) < 2


async def test_airplay_dbus_property_poll_forwards_slider_change(tmp_path):
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    zone = AudioZoneProfile(
        zone_id="kitchen",
        media_player_entity_id="media_player.kitchen",
        max_volume_percent=100,
        airplay={"enabled": True, "service_name": "TecnoHead Cozinha", "stable_id": "0123456789abcdef"},
    )
    endpoint = _Endpoint(zone=zone, port=7000)
    endpoint.output_started = True
    process = SimpleNamespace(returncode=None)
    endpoint.process = process  # type: ignore[assignment]
    readings = iter([52, 31])
    forwarded: list[int] = []

    async def read(_endpoint):
        try:
            return next(readings)
        except StopIteration:
            process.returncode = 0
            return 31

    async def forward(_endpoint, volume_percent, **_kwargs):
        forwarded.append(volume_percent)

    manager._read_airplay_volume_from_source = read  # type: ignore[method-assign]
    manager._forward_airplay_volume = forward  # type: ignore[method-assign]

    await manager._watch_airplay_volume(endpoint)
    await asyncio.gather(*endpoint.volume_forward_tasks)

    assert forwarded == [31]
    assert endpoint.last_dbus_airplay_volume_percent == 31


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


async def test_airplay_metadata_reader_skips_oversized_item_without_losing_next_volume(tmp_path):
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    oversize = b"x" * (MAX_METADATA_ITEM_BYTES + 1)
    volume = b"-15.00,-15.00,-30.00,0.00"
    stream = asyncio.StreamReader(limit=METADATA_STREAM_LIMIT)
    for code, payload in ((b"636f706c", oversize), (b"70766f6c", volume)):
        stream.feed_data(
            b"<item><type>73736e63</type><code>" + code + b"</code><length>"
            + str(len(payload)).encode() + b"</length>\n<data encoding=\"base64\">\n"
            + base64.b64encode(payload) + b"\n</data></item>\n"
        )
    stream.feed_eof()
    assert await manager._read_metadata_item(stream, await stream.readline()) is None
    assert await manager._read_metadata_item(stream, await stream.readline()) == ("ssnc", "pvol", volume)


def test_mediaremote_probe_records_only_presence_and_supported_commands():
    probe = MediaRemoteProbe()
    artwork = b"a" * 194000
    now_playing = {
        "type": "updateMRNowPlayingInfo",
        "params": {"params": {
            "kMRMediaRemoteNowPlayingInfoTitle": "PRIVATE TRACK",
            "kMRMediaRemoteNowPlayingInfoArtist": "PRIVATE ARTIST",
            "kMRMediaRemoteNowPlayingInfoArtworkData": artwork,
        }},
    }
    commands = {
        "type": "updateMRSupportedCommands",
        "params": {"mrSupportedCommandsFromSender": [
            plistlib.dumps({"kCommandInfoCommandKey": 1, "kCommandInfoEnabledKey": True}),
            plistlib.dumps({"kCommandInfoCommandKey": 4, "kCommandInfoEnabledKey": False}),
        ]},
    }
    probe.observe(plistlib.dumps(now_playing))
    probe.observe(plistlib.dumps(commands))
    report = probe.report()
    assert report["now_playing_updates"] == 1
    assert report["supported_commands_updates"] == 1
    assert report["observed_fields"] == ["artist", "artwork", "title"]
    assert report["enabled_command_codes"] == [1]
    assert report["apple_home_card"] == "not_observed"
    assert "PRIVATE" not in repr(report)
    assert "194000" not in repr(report)


def test_mediaremote_probe_does_not_retain_or_log_invalid_or_oversized_payload():
    probe = MediaRemoteProbe()
    probe.observe(b"invalid")
    probe.observe(b"private" * 200000)
    assert probe.report()["invalid_updates"] == 1
    assert probe.report()["oversized_updates"] == 1
    assert "private" not in repr(probe.report())


async def test_mediaremote_probe_is_opt_in_and_does_not_change_volume_path(tmp_path):
    async def record(**kwargs):
        return None

    payload = plistlib.dumps({
        "type": "updateMRNowPlayingInfo",
        "params": {"params": {"kMRMediaRemoteNowPlayingInfoTitle": "PRIVATE TRACK"}},
    })
    volume = b"-15.00,-15.00,-30.00,0.00"

    def make_endpoint():
        stream = asyncio.StreamReader(limit=METADATA_STREAM_LIMIT)
        for code, body in ((b"636f706c", payload), (b"70766f6c", volume)):
            stream.feed_data(
                b"<item><type>73736e63</type><code>" + code + b"</code><length>"
                + str(len(body)).encode() + b"</length>\n<data encoding=\"base64\">\n"
                + base64.b64encode(body) + b"\n</data></item>\n"
            )
        stream.feed_eof()
        endpoint = _Endpoint(zone=AudioZoneProfile(zone_id="kitchen"), port=7000)
        endpoint.metadata_reader = SimpleNamespace(stdout=stream)  # type: ignore[assignment]
        return endpoint

    for enabled in (False, True):
        manager = AirPlayEndpointManager(
            Settings(data_dir=tmp_path, apple_mediaremote_experimental=enabled), None, None, record
        )  # type: ignore[arg-type]
        forwarded = []
        manager._queue_airplay_volume = lambda _endpoint, percent, *, source: forwarded.append((percent, source))  # type: ignore[method-assign]
        endpoint = make_endpoint()
        await manager._consume_metadata(endpoint)
        assert forwarded == [(50, "metadata")]
        assert endpoint.mediaremote_probe.now_playing_updates == int(enabled)
        if enabled:
            assert "PRIVATE" not in repr(endpoint.mediaremote_probe.report())


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
    forwarded: list[tuple[int, str]] = []

    async def forward(_endpoint, volume_percent, *, source):
        forwarded.append((volume_percent, source))

    manager._forward_airplay_volume = forward  # type: ignore[method-assign]
    client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    task = asyncio.create_task(manager._consume_volume_hook(endpoint))
    try:
        client.sendto(b"-15.00", str(socket_path))
        await asyncio.wait_for(_wait_for_value(forwarded), timeout=1)
        assert forwarded == [(50, "hook")]
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        client.close()
        manager._close_volume_socket(endpoint.volume_socket, socket_path)


async def test_physical_volume_is_forwarded_to_active_airplay_source(tmp_path):
    events = []

    async def record(**kwargs):
        events.append(kwargs)

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    zone = AudioZoneProfile(
        zone_id="kitchen",
        area_id="kitchen",
        media_player_entity_id="media_player.kitchen",
        max_volume_percent=100,
        airplay={"enabled": True, "service_name": "TecnoHead Cozinha", "stable_id": "0123456789abcdef"},
    )
    endpoint = _Endpoint(zone=zone, port=7000)
    endpoint.output_started = True
    endpoint.process = SimpleNamespace(returncode=None)  # type: ignore[assignment]
    manager._endpoints["kitchen"] = endpoint
    sent: list[int] = []

    async def send(_endpoint, volume_percent):
        sent.append(volume_percent)
        return percent_to_airplay_volume_db(volume_percent)

    manager._send_airplay_volume_to_source = send  # type: ignore[method-assign]
    await manager.handle_state_event(
        {
            "data": {
                "entity_id": "media_player.kitchen",
                "old_state": {"attributes": {"volume_level": 0.20}},
                "new_state": {"attributes": {"volume_level": 0.42}},
            }
        }
    )

    assert sent == [42]
    assert endpoint.last_airplay_volume_percent == 42
    assert events[-1]["event"] == "physical_volume_forwarded_to_airplay"


async def test_physical_volume_echo_from_airplay_is_suppressed(tmp_path):
    async def record(**kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    zone = AudioZoneProfile(
        zone_id="pool",
        area_id="pool",
        media_player_entity_id="media_player.pool",
        max_volume_percent=100,
        airplay={"enabled": True, "service_name": "TecnoHead Piscina", "stable_id": "fedcba9876543210"},
    )
    endpoint = _Endpoint(zone=zone, port=7001)
    endpoint.output_started = True
    endpoint.process = SimpleNamespace(returncode=None)  # type: ignore[assignment]
    endpoint.last_airplay_volume_percent = 42
    endpoint.last_airplay_to_physical_percent = 42
    endpoint.last_airplay_to_physical_at = asyncio.get_running_loop().time()
    manager._endpoints["pool"] = endpoint
    sent: list[int] = []

    async def send(_endpoint, volume_percent):
        sent.append(volume_percent)
        return 0.0

    manager._send_airplay_volume_to_source = send  # type: ignore[method-assign]
    await manager.handle_state_event(
        {
            "data": {
                "entity_id": "media_player.pool",
                "old_state": {"attributes": {"volume_level": 0.20}},
                "new_state": {"attributes": {"volume_level": 0.42}},
            }
        }
    )

    assert sent == []


async def test_volume_rounding_echo_does_not_oscillate_between_airplay_and_linkplay(tmp_path):
    events = []

    async def record(**kwargs):
        events.append(kwargs)

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    zone = AudioZoneProfile(
        zone_id="kitchen",
        area_id="kitchen",
        media_player_entity_id="media_player.kitchen",
        max_volume_percent=100,
        airplay={"enabled": True, "service_name": "TecnoHead Cozinha", "stable_id": "0123456789abcdef"},
    )
    endpoint = _Endpoint(zone=zone, port=7000)
    endpoint.output_started = True
    endpoint.process = SimpleNamespace(returncode=None)  # type: ignore[assignment]
    manager._endpoints["kitchen"] = endpoint
    sent_to_airplay: list[int] = []
    sent_to_linkplay: list[int] = []

    async def send(_endpoint, volume_percent):
        sent_to_airplay.append(volume_percent)
        return percent_to_airplay_volume_db(volume_percent)

    async def set_volume(_config, _zone_id, volume_percent):
        sent_to_linkplay.append(volume_percent)
        return {"applied_percent": volume_percent}

    manager._send_airplay_volume_to_source = send  # type: ignore[method-assign]
    manager.audio = SimpleNamespace(set_airplay_volume=set_volume)

    # A real physical change requests 42% on the iPhone. Shairport may report
    # the resulting AirPlay value as 41%; that callback must be ignored rather
    # than sent back to HA and started as a new cycle.
    await manager.handle_state_event(
        {
            "data": {
                "entity_id": "media_player.kitchen",
                "old_state": {"attributes": {"volume_level": 0.30}},
                "new_state": {"attributes": {"volume_level": 0.42}},
            }
        }
    )
    await manager._forward_airplay_volume(endpoint, 41)

    assert sent_to_airplay == [42]
    assert sent_to_linkplay == []
    assert events[-1]["event"] == "physical_volume_forwarded_to_airplay"

    # Conversely, the iPhone command produces a LinkPlay state callback that
    # can differ by one point. It must not be mirrored back to AirPlay.
    endpoint.last_physical_to_airplay_percent = None
    endpoint.last_physical_to_airplay_at = None
    await manager._forward_airplay_volume(endpoint, 55)
    await manager.handle_state_event(
        {
            "data": {
                "entity_id": "media_player.kitchen",
                "old_state": {"attributes": {"volume_level": 0.54}},
                "new_state": {"attributes": {"volume_level": 0.55}},
            }
        }
    )

    assert sent_to_linkplay == [55]


async def test_rapid_airplay_slider_ignores_delayed_linkplay_states_and_keeps_zones_independent(tmp_path):
    async def record(**_kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    kitchen = _Endpoint(
        zone=AudioZoneProfile(
            zone_id="kitchen", area_id="kitchen", media_player_entity_id="media_player.kitchen", max_volume_percent=100
        ),
        port=7000,
    )
    pool = _Endpoint(
        zone=AudioZoneProfile(
            zone_id="pool", area_id="pool", media_player_entity_id="media_player.pool", max_volume_percent=100
        ),
        port=7001,
    )
    for endpoint in (kitchen, pool):
        endpoint.output_started = True
        endpoint.process = SimpleNamespace(returncode=None)  # type: ignore[assignment]
        manager._endpoints[endpoint.zone.zone_id] = endpoint

    first_started = asyncio.Event()
    release_first = asyncio.Event()
    sent_to_linkplay: list[tuple[str, int]] = []
    sent_to_airplay: list[tuple[str, int]] = []

    async def set_volume(_config, zone_id, volume_percent):
        sent_to_linkplay.append((zone_id, volume_percent))
        if zone_id == "kitchen" and volume_percent == 30:
            first_started.set()
            await release_first.wait()
        return {"applied_percent": volume_percent}

    async def send(endpoint, volume_percent):
        sent_to_airplay.append((endpoint.zone.zone_id, volume_percent))
        return percent_to_airplay_volume_db(volume_percent)

    manager.audio = SimpleNamespace(set_airplay_volume=set_volume)
    manager._send_airplay_volume_to_source = send  # type: ignore[method-assign]

    first = asyncio.create_task(manager._forward_airplay_volume(kitchen, 30, source="hook"))
    await asyncio.wait_for(first_started.wait(), timeout=1)
    await manager._forward_airplay_volume(pool, 22, source="hook")
    assert sent_to_linkplay == [("kitchen", 30), ("pool", 22)]
    middle = asyncio.create_task(manager._forward_airplay_volume(kitchen, 45, source="hook"))
    latest = asyncio.create_task(manager._forward_airplay_volume(kitchen, 60, source="hook"))
    await asyncio.sleep(0)
    release_first.set()
    await asyncio.gather(first, middle, latest)
    assert sent_to_linkplay == [("kitchen", 30), ("pool", 22), ("kitchen", 60)]

    # Even if HA callbacks are delayed beyond the gesture window, every
    # requested intermediate value is still recognized as part of the drag.
    # A slow HA call may complete after the last finger movement. Its delayed
    # state response must still not drive the iPhone slider backwards.
    kitchen.last_airplay_input_at = time.monotonic() - 4
    await manager.handle_state_event(
        {"data": {"entity_id": "media_player.kitchen", "old_state": {"attributes": {"volume_level": 0.60}}, "new_state": {"attributes": {"volume_level": 0.71}}}}
    )
    assert sent_to_airplay == []
    kitchen.last_airplay_to_physical_completed_at = time.monotonic() - 4
    for previous, current in ((20, 30), (30, 45), (45, 60)):
        await manager.handle_state_event(
            {"data": {"entity_id": "media_player.kitchen", "old_state": {"attributes": {"volume_level": previous / 100}}, "new_state": {"attributes": {"volume_level": current / 100}}}}
        )
    assert sent_to_airplay == []

    # A Kitchen gesture must not mute or delay an external Pool change.
    pool.last_airplay_input_at = time.monotonic() - 4
    pool.last_airplay_to_physical_completed_at = time.monotonic() - 4
    await manager.handle_state_event(
        {"data": {"entity_id": "media_player.pool", "old_state": {"attributes": {"volume_level": 0.25}}, "new_state": {"attributes": {"volume_level": 0.65}}}}
    )
    assert sent_to_airplay == [("pool", 65)]

    # Once the Kitchen gesture settles, a real AudioCast change still goes
    # back to the iPhone instead of disabling bidirectional control entirely.
    kitchen.last_airplay_input_at = time.monotonic() - 4
    kitchen.last_airplay_to_physical_completed_at = time.monotonic() - 4
    await manager.handle_state_event(
        {"data": {"entity_id": "media_player.kitchen", "old_state": {"attributes": {"volume_level": 0.60}}, "new_state": {"attributes": {"volume_level": 0.71}}}}
    )
    assert sent_to_airplay == [("pool", 65), ("kitchen", 71)]


async def test_dbus_poll_does_not_replay_stale_volume_while_hook_is_active(tmp_path):
    async def record(**_kwargs):
        return None

    manager = AirPlayEndpointManager(Settings(data_dir=tmp_path), None, None, record)  # type: ignore[arg-type]
    endpoint = _Endpoint(
        zone=AudioZoneProfile(zone_id="kitchen", media_player_entity_id="media_player.kitchen", max_volume_percent=100),
        port=7000,
    )
    forwarded: list[int] = []

    async def set_volume(_config, _zone_id, volume_percent):
        forwarded.append(volume_percent)
        return {"applied_percent": volume_percent}

    manager.audio = SimpleNamespace(set_airplay_volume=set_volume)
    await manager._forward_airplay_volume(endpoint, 50, source="hook")
    await manager._forward_airplay_volume(endpoint, 30, source="poll")
    assert forwarded == [50]
    endpoint.last_volume_hook_at = time.monotonic() - 4
    await manager._forward_airplay_volume(endpoint, 30, source="poll")
    assert forwarded == [50, 30]


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
