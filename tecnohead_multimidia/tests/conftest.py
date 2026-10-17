from __future__ import annotations

import copy

import pytest

from app.core.presets import default_ir_profile
from app.models import AreaProfile, ClimateProfile


class FakeHomeAssistant:
    def __init__(self):
        self.calls: list[dict] = []
        self.snapshot = {
            "areas": [{"id": "cinema", "name": "Cinema", "aliases": []}, {"id": "infra", "name": "Infra"}],
            "devices": [
                {"id": "dev-tv", "area_id": "cinema"},
                {"id": "dev-receiver", "area_id": "cinema"},
                {"id": "dev-screen", "area_id": "cinema"},
                {"id": "dev-climate", "area_id": "cinema"},
                {"id": "dev-remote", "area_id": "cinema"},
                {"id": "dev-light", "area_id": "cinema"},
                {"id": "dev-remote-infra", "area_id": "infra"},
            ],
            "entities": [
                {"entity_id": "media_player.tv_cinema", "device_id": "dev-tv", "area_id": None},
                {"entity_id": "media_player.denon_cinema", "device_id": "dev-receiver", "area_id": None},
                {"entity_id": "switch.tela", "device_id": "dev-screen", "area_id": None},
                {"entity_id": "climate.ar_cinema", "device_id": "dev-climate", "area_id": None},
                {"entity_id": "remote.ir_cinema", "device_id": "dev-remote", "area_id": None},
                {"entity_id": "remote.ir_infra", "device_id": "dev-remote-infra", "area_id": None},
                {"entity_id": "light.luz_cinema", "device_id": "dev-light", "area_id": None},
                {"entity_id": "light.sanca_cinema", "device_id": "dev-light", "area_id": None},
                {"entity_id": "switch.maquina_pipoca", "device_id": "dev-light", "area_id": None},
            ],
            "states": [
                {"entity_id": "media_player.tv_cinema", "state": "off", "attributes": {"friendly_name": "TV Cinema", "supported_features": 1}},
                {"entity_id": "media_player.denon_cinema", "state": "off", "attributes": {"friendly_name": "Denon", "source_list": ["Apple TV", "TV Audio"], "volume_level": 0.2}},
                {"entity_id": "switch.tela", "state": "off", "attributes": {"friendly_name": "Telão"}},
                {"entity_id": "climate.ar_cinema", "state": "off", "attributes": {"friendly_name": "Ar", "hvac_modes": ["off", "cool"], "fan_modes": ["low", "high"], "swing_modes": ["up", "off"], "current_temperature": 26.0}},
                {"entity_id": "remote.ir_cinema", "state": "on", "attributes": {"friendly_name": "Emissor IR Cinema"}},
                {"entity_id": "remote.ir_infra", "state": "on", "attributes": {"friendly_name": "Emissor IR Infra"}},
                {"entity_id": "light.luz_cinema", "state": "on", "attributes": {"friendly_name": "Luz principal"}},
                {"entity_id": "light.sanca_cinema", "state": "on", "attributes": {"friendly_name": "Sanca"}},
                {"entity_id": "switch.maquina_pipoca", "state": "on", "attributes": {"friendly_name": "Máquina de pipoca"}},
            ],
        }

    async def start(self):
        return None

    async def stop(self):
        return None

    async def get_registry_snapshot(self):
        return copy.deepcopy(self.snapshot)

    async def get_state(self, entity_id):
        return next((copy.deepcopy(state) for state in self.snapshot["states"] if state["entity_id"] == entity_id), None)

    async def call_service(self, domain, service, *, entity_id, data=None):
        record = {"domain": domain, "service": service, "entity_id": entity_id, "data": copy.deepcopy(data or {})}
        self.calls.append(record)
        state = next((item for item in self.snapshot["states"] if item["entity_id"] == entity_id), None)
        if state:
            if service in {"turn_on", "open_cover"}:
                state["state"] = "on"
            elif service in {"turn_off", "close_cover"}:
                state["state"] = "off"
            elif service == "set_hvac_mode":
                state["state"] = data["hvac_mode"]
            elif service == "set_fan_mode":
                state["attributes"]["fan_mode"] = data["fan_mode"]
            elif service == "set_swing_mode":
                state["attributes"]["swing_mode"] = data["swing_mode"]
            elif service == "select_source":
                state["attributes"]["source"] = data["source"]
            elif service == "volume_set":
                state["attributes"]["volume_level"] = data["volume_level"]
        return {"ok": True}


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        return self.value

    async def sleep(self, seconds):
        self.value += seconds


@pytest.fixture
def fake_ha():
    return FakeHomeAssistant()


@pytest.fixture
def cinema_profile():
    profile = AreaProfile(
        area_id="cinema",
        enabled=True,
        tv_entity_id="media_player.tv_cinema",
        receiver_entity_id="media_player.denon_cinema",
        screen_entity_id="switch.tela",
        climate_entity_id="climate.ar_cinema",
        receiver_cinema_source="Apple TV",
        receiver_tv_source="TV Audio",
        lights_delay_seconds=0,
        ir=default_ir_profile(),
        climate=ClimateProfile(minimum_fan_change_seconds=0),
    )
    profile.ir.remote_entity_id = "remote.ir_cinema"
    return profile
