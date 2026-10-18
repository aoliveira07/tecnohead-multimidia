from __future__ import annotations

from app.core.audio import AudioActionError, AudioManager
from app.core.discovery import DiscoveryService
from app.core.store import ConfigStore
from app.models import AudioPriority, AudioVolumeRequest, AudioZoneProfile, MultiroomConfig


def _audio_snapshot(fake_ha):
    fake_ha.snapshot["areas"] = [
        {"id": "kitchen", "name": "Cozinha", "aliases": []},
        {"id": "pool", "name": "Piscina", "aliases": []},
    ]
    fake_ha.snapshot["devices"] = [
        {"id": "dev-kitchen", "area_id": "kitchen"},
        {"id": "dev-pool", "area_id": "pool"},
    ]
    fake_ha.snapshot["entities"] = [
        {"entity_id": "media_player.kitchen_amp", "device_id": "dev-kitchen", "area_id": None, "platform": "linkplay"},
        {"entity_id": "media_player.pool_amp", "device_id": "dev-pool", "area_id": None, "platform": "linkplay"},
        {"entity_id": "media_player.other_room", "device_id": "dev-kitchen", "area_id": "other_area", "platform": "linkplay"},
        {"entity_id": "media_player.pool_tv_wrapper", "device_id": "dev-pool", "area_id": None, "platform": "universal"},
    ]
    fake_ha.snapshot["states"] = [
        {
            "entity_id": "media_player.kitchen_amp",
            "state": "idle",
            "attributes": {
                "friendly_name": "Amplificador Cozinha",
                "source": "Network",
                "source_list": ["Network", "Spotify Connect"],
                "volume_level": 0.2,
                "is_volume_muted": False,
                "supported_features": 524297,
            },
        },
        {
            "entity_id": "media_player.pool_amp",
            "state": "idle",
            "attributes": {
                "friendly_name": "Amplificador Piscina",
                "source": "TV ARC",
                "source_list": ["TV ARC", "Network"],
                "volume_level": 0.15,
                "is_volume_muted": False,
                "supported_features": 524297,
                "group_members": [],
            },
        },
        {
            "entity_id": "media_player.pool_tv_wrapper",
            "state": "off",
            "attributes": {"friendly_name": "TV Piscina", "source_list": ["TV", "HDMI"], "supported_features": 1},
        },
    ]


def _config():
    return MultiroomConfig(
        enabled=True,
        zones=[
            AudioZoneProfile(zone_id="kitchen", area_id="kitchen", enabled=True, media_player_entity_id="media_player.kitchen_amp", max_volume_percent=30),
            AudioZoneProfile(zone_id="pool", area_id="pool", enabled=True, media_player_entity_id="media_player.pool_amp", max_volume_percent=30, priority=AudioPriority.HDMI_ARC),
        ],
    )


async def test_audio_discovery_is_area_strict_and_reports_linkplay(fake_ha):
    _audio_snapshot(fake_ha)
    discovery = DiscoveryService(fake_ha)
    manager = AudioManager(fake_ha, discovery)

    payload = await manager.discovery_payload(_config())
    kitchen = next(area for area in payload["areas"] if area["area_id"] == "kitchen")
    pool = next(area for area in payload["areas"] if area["area_id"] == "pool")

    assert [entity["entity_id"] for entity in kitchen["media_players"]] == ["media_player.kitchen_amp"]
    assert [entity["entity_id"] for entity in pool["media_players"]] == ["media_player.pool_amp"]
    assert payload["airplay"]["state"] == "not_homologated"
    assert payload["airplay"]["physical_audio"] == "not_tested"


async def test_audio_volume_uses_ha_and_enforces_zone_limit(fake_ha):
    _audio_snapshot(fake_ha)
    discovery = DiscoveryService(fake_ha)
    manager = AudioManager(fake_ha, discovery)

    result = await manager.set_volume(_config(), "kitchen", AudioVolumeRequest(volume_percent=25, confirmed=True))
    assert result["requested_percent"] == 25
    assert fake_ha.calls[-1] == {
        "domain": "media_player",
        "service": "volume_set",
        "entity_id": "media_player.kitchen_amp",
        "data": {"volume_level": 0.25},
    }

    try:
        await manager.set_volume(_config(), "kitchen", AudioVolumeRequest(volume_percent=31, confirmed=True))
    except AudioActionError as exc:
        assert "limite seguro" in str(exc)
    else:  # pragma: no cover - protects the safety assertion
        raise AssertionError("volume acima do limite deveria ser recusado")


async def test_airplay_volume_forwards_to_physical_player_with_zone_ceiling(fake_ha):
    _audio_snapshot(fake_ha)
    discovery = DiscoveryService(fake_ha)
    manager = AudioManager(fake_ha, discovery)

    result = await manager.set_airplay_volume(_config(), "kitchen", 80)

    assert result["requested_percent"] == 80
    assert result["applied_percent"] == 30
    assert fake_ha.calls[-1] == {
        "domain": "media_player",
        "service": "volume_set",
        "entity_id": "media_player.kitchen_amp",
        "data": {"volume_level": 0.3},
    }


async def test_v13_migration_preserves_v12_areas(tmp_path):
    store = ConfigStore(tmp_path)
    migrated = store._migrate({"schema_version": 2, "areas": [{"area_id": "cinema", "enabled": True}]})
    assert migrated.schema_version == 3
    assert migrated.areas[0].area_id == "cinema"
    assert migrated.audio.zones == []
