from __future__ import annotations

import asyncio
import json
import logging
import re
import ssl
from collections.abc import Awaitable, Callable
from typing import Any

import aiomqtt

from app.core.ha_client import HomeAssistantClient
from app.models import AreaProfile, Mode
from app.settings import Settings

LOGGER = logging.getLogger("tecnohead.mqtt")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "_", value.casefold()).strip("_") or "area"


class MqttBridge:
    """MQTT Discovery publisher and command listener, optional by design."""

    def __init__(
        self,
        settings: Settings,
        ha: HomeAssistantClient,
        installation_id: str,
        profiles: Callable[[], Awaitable[list[AreaProfile]]],
        states: Callable[[], Awaitable[list[dict[str, Any]]]],
        command_handler: Callable[[str, Mode, bool], Awaitable[None]],
        audio_payload: Callable[[], Awaitable[dict[str, Any]]] | None = None,
        audio_command_handler: Callable[[str, str, str], Awaitable[None]] | None = None,
    ):
        self.settings = settings
        self.ha = ha
        self.installation_id = installation_id
        self.profiles = profiles
        self.states = states
        self.command_handler = command_handler
        self.audio_payload = audio_payload
        self.audio_command_handler = audio_command_handler
        self.connected = False
        self.last_error: str | None = None
        self._stop = asyncio.Event()
        self._wake = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._client: aiomqtt.Client | None = None
        self._connection_lock = asyncio.Lock()

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="tecnohead-mqtt")

    async def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.connected = False
        self._client = None

    async def sync_discovery(self) -> None:
        self._wake.set()
        if self.connected:
            await self.publish_discovery()

    def status(self) -> dict[str, Any]:
        return {"connected": self.connected, "last_error": self.last_error}

    async def _run(self) -> None:
        delay = 2.0
        while not self._stop.is_set():
            service = await self.ha.get_mqtt_service()
            if not service:
                self.connected = False
                self.last_error = "serviço MQTT não disponível no Supervisor"
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=30.0)
                except TimeoutError:
                    continue
                return
            try:
                will = aiomqtt.Will(
                    topic=self._availability_topic(),
                    payload="offline",
                    qos=1,
                    retain=True,
                )
                client_kwargs: dict[str, Any] = {
                    "hostname": str(service["host"]),
                    "port": int(service["port"]),
                    "username": service.get("username"),
                    "password": service.get("password"),
                    "identifier": f"tecnohead-{self.installation_id[:12]}",
                    "will": will,
                }
                if service.get("ssl", False):
                    client_kwargs["tls_context"] = ssl.create_default_context()
                client = aiomqtt.Client(**client_kwargs)
                async with client:
                    async with self._connection_lock:
                        self._client = client
                        self.connected = True
                        self.last_error = None
                    await client.publish(self._availability_topic(), payload="online", qos=1, retain=True)
                    await self._subscribe_command_topics(client)
                    await self.publish_discovery()
                    delay = 2.0
                    await self._consume_messages(client)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.connected = False
                self._client = None
                self.last_error = "broker MQTT indisponível"
                LOGGER.warning("MQTT desconectado: %s", exc)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=delay)
                except TimeoutError:
                    delay = min(delay * 2, 60.0)
        self.connected = False
        self._client = None

    async def _subscribe_command_topics(self, client: aiomqtt.Client) -> None:
        for profile in await self.profiles():
            if profile.enabled:
                for key in ("modo_cinema", "modo_tv", "multimidia"):
                    await client.subscribe(self._command_topic(profile.area_id, key), qos=1)
        if self.audio_command_handler:
            for zone_id in ("kitchen", "pool"):
                for key in ("volume", "mute", "source"):
                    await client.subscribe(self._audio_command_topic(zone_id, key), qos=1)
            for key in ("share_pool_to_kitchen", "unjoin_pool"):
                await client.subscribe(self._audio_command_topic("group", key), qos=1)
        await client.subscribe("homeassistant/status", qos=1)

    async def _consume_messages(self, client: aiomqtt.Client) -> None:
        async for message in client.messages:
            if self._stop.is_set():
                return
            topic = str(message.topic)
            payload = bytes(message.payload).decode("utf-8", errors="replace").strip()
            if topic == "homeassistant/status":
                if payload == "online":
                    await self.publish_discovery()
                continue
            audio_match = re.match(
                rf"^{re.escape(self.settings.mqtt_topic_prefix)}/{re.escape(self.installation_id)}/audio/([^/]+)/([^/]+)/set$",
                topic,
            )
            if audio_match and self.audio_command_handler:
                zone_id, key = audio_match.groups()
                await self.audio_command_handler(zone_id, key, payload)
                continue
            match = re.match(
                rf"^{re.escape(self.settings.mqtt_topic_prefix)}/{re.escape(self.installation_id)}/([^/]+)/([^/]+)/set$",
                topic,
            )
            if not match:
                continue
            area_slug, key = match.groups()
            for profile in await self.profiles():
                if _slug(profile.area_id) == area_slug and profile.enabled:
                    mode = profile.default_mode if key == "multimidia" and payload.casefold() in {"on", "1", "true"} else self._mode_for_key(key, payload)
                    if mode is None:
                        break
                    await self.command_handler(profile.area_id, mode, True)
                    break

    @staticmethod
    def _mode_for_key(key: str, payload: str) -> Mode | None:
        is_on = payload.casefold() in {"on", "1", "true"}
        is_off = payload.casefold() in {"off", "0", "false"}
        if key == "modo_cinema":
            return Mode.CINEMA if is_on else Mode.OFF if is_off else None
        if key == "modo_tv":
            return Mode.TV if is_on else Mode.OFF if is_off else None
        if key == "multimidia":
            return Mode.TV if is_on else Mode.OFF if is_off else None
        return None

    def _base(self, area_id: str) -> str:
        return f"{self.settings.mqtt_topic_prefix}/{self.installation_id}/{_slug(area_id)}"

    def _availability_topic(self) -> str:
        return f"{self.settings.mqtt_topic_prefix}/{self.installation_id}/availability"

    def _state_topic(self, area_id: str, key: str) -> str:
        return f"{self._base(area_id)}/{key}/state"

    def _command_topic(self, area_id: str, key: str) -> str:
        return f"{self._base(area_id)}/{key}/set"

    def _diagnostic_topic(self, area_id: str) -> str:
        return f"{self._base(area_id)}/diagnostic/state"

    def _audio_base(self, zone_id: str) -> str:
        return f"{self.settings.mqtt_topic_prefix}/{self.installation_id}/audio/{_slug(zone_id)}"

    def _audio_state_topic(self, zone_id: str, key: str) -> str:
        return f"{self._audio_base(zone_id)}/{key}/state"

    def _audio_command_topic(self, zone_id: str, key: str) -> str:
        return f"{self._audio_base(zone_id)}/{key}/set"

    def _audio_device(self, zone: dict[str, Any]) -> dict[str, Any]:
        return {
            "identifiers": [f"tecnohead:{self.installation_id}:audio:{zone.get('zone_id', 'zone')}"],
            "name": f"TecnoHead Áudio — {zone.get('label', zone.get('zone_id', 'zona'))}",
            "manufacturer": "TecnoHead",
            "model": "Áudio Multiroom",
            "sw_version": self.settings.app_version,
            "suggested_area": zone.get("area_id"),
        }

    def _device(self, profile: AreaProfile) -> dict[str, Any]:
        return {
            "identifiers": [f"tecnohead:{self.installation_id}:{profile.area_id}"],
            "name": f"TecnoHead Multimídia — {profile.area_id}",
            "manufacturer": "TecnoHead",
            "model": "Multimídia",
            "sw_version": self.settings.app_version,
            "suggested_area": profile.area_id,
        }

    def _switch_config(self, profile: AreaProfile, key: str, name: str) -> dict[str, Any]:
        return {
            "name": name,
            "unique_id": f"tecnohead_{self.installation_id}_{_slug(profile.area_id)}_{key}",
            "object_id": f"tecnohead_{_slug(profile.area_id)}_{key}",
            "state_topic": self._state_topic(profile.area_id, key),
            "command_topic": self._command_topic(profile.area_id, key),
            "availability_topic": self._availability_topic(),
            "payload_on": "ON",
            "payload_off": "OFF",
            "state_on": "ON",
            "state_off": "OFF",
            "qos": 1,
            "retain": False,
            "device": self._device(profile),
            "origin": {
                "name": "TecnoHead Multimídia",
                "sw_version": self.settings.app_version,
                "support_url": "https://github.com/aoliveira07/tecnohead-multimidia",
            },
        }

    async def publish_discovery(self) -> None:
        client = self._client
        if not client or not self.connected:
            return
        async with self._connection_lock:
            for profile in await self.profiles():
                if not profile.enabled:
                    continue
                for component, key, name in (
                    ("switch", "modo_cinema", "TecnoHead Cinema"),
                    ("switch", "modo_tv", "TecnoHead TV"),
                    ("switch", "multimidia", "TecnoHead Multimídia"),
                ):
                    topic = f"{self.settings.mqtt_discovery_prefix}/{component}/{self.installation_id}_{_slug(profile.area_id)}/{key}/config"
                    await client.publish(topic, json.dumps(self._switch_config(profile, key, name), ensure_ascii=False), qos=1, retain=True)
                sensor_specs = (
                    ("modo", "Modo", "mode"),
                    ("fase", "Fase", "phase"),
                    ("diagnostico", "Diagnóstico", "diagnostic"),
                )
                for key, name, state_key in sensor_specs:
                    topic = f"{self.settings.mqtt_discovery_prefix}/sensor/{self.installation_id}_{_slug(profile.area_id)}/{key}/config"
                    payload = {
                        "name": f"TecnoHead {name} — {profile.area_id}",
                        "unique_id": f"tecnohead_{self.installation_id}_{_slug(profile.area_id)}_{key}",
                        "object_id": f"tecnohead_{_slug(profile.area_id)}_{key}",
                        "state_topic": self._state_topic(profile.area_id, key),
                        "availability_topic": self._availability_topic(),
                        "qos": 1,
                        "device": self._device(profile),
                        "origin": {"name": "TecnoHead Multimídia", "sw_version": self.settings.app_version},
                    }
                    await client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=True)
                await self.publish_area_state(profile.area_id)
            await self.publish_audio_discovery()

    async def publish_audio_discovery(self) -> None:
        client = self._client
        if not client or not self.connected or not self.audio_payload:
            return
        payload = await self.audio_payload()
        for zone in payload.get("zones", []):
            if not zone.get("enabled") or not zone.get("area_id"):
                continue
            zone_id = str(zone.get("zone_id"))
            device = self._audio_device(zone)
            entity = zone.get("entity") or {}
            supports = entity.get("supports") or {}
            if supports.get("volume"):
                config = {
                    "name": f"Volume {zone.get('label', zone_id)}",
                    "unique_id": f"tecnohead_{self.installation_id}_audio_{_slug(zone_id)}_volume",
                    "object_id": f"tecnohead_audio_{_slug(zone_id)}_volume",
                    "state_topic": self._audio_state_topic(zone_id, "volume"),
                    "command_topic": self._audio_command_topic(zone_id, "volume"),
                    "min": 0,
                    "max": zone.get("max_volume_percent", 30),
                    "step": 1,
                    "mode": "slider",
                    "availability_topic": self._availability_topic(),
                    "retain": False,
                    "device": device,
                    "origin": {"name": "TecnoHead Multimídia", "sw_version": self.settings.app_version},
                }
                await client.publish(f"{self.settings.mqtt_discovery_prefix}/number/{self.installation_id}_audio_{_slug(zone_id)}_volume/config", json.dumps(config, ensure_ascii=False), qos=1, retain=True)
            if supports.get("mute"):
                config = {
                    "name": f"Mudo {zone.get('label', zone_id)}",
                    "unique_id": f"tecnohead_{self.installation_id}_audio_{_slug(zone_id)}_mute",
                    "object_id": f"tecnohead_audio_{_slug(zone_id)}_mute",
                    "state_topic": self._audio_state_topic(zone_id, "mute"),
                    "command_topic": self._audio_command_topic(zone_id, "mute"),
                    "payload_on": "ON",
                    "payload_off": "OFF",
                    "state_on": "ON",
                    "state_off": "OFF",
                    "availability_topic": self._availability_topic(),
                    "retain": False,
                    "device": device,
                    "origin": {"name": "TecnoHead Multimídia", "sw_version": self.settings.app_version},
                }
                await client.publish(f"{self.settings.mqtt_discovery_prefix}/switch/{self.installation_id}_audio_{_slug(zone_id)}_mute/config", json.dumps(config, ensure_ascii=False), qos=1, retain=True)
            for key, name in (("status", "Estado"), ("source", "Fonte"), ("airplay", "AirPlay 2")):
                config = {
                    "name": f"{name} {zone.get('label', zone_id)}",
                    "unique_id": f"tecnohead_{self.installation_id}_audio_{_slug(zone_id)}_{key}",
                    "object_id": f"tecnohead_audio_{_slug(zone_id)}_{key}",
                    "state_topic": self._audio_state_topic(zone_id, key),
                    "availability_topic": self._availability_topic(),
                    "device": device,
                    "origin": {"name": "TecnoHead Multimídia", "sw_version": self.settings.app_version},
                }
                await client.publish(f"{self.settings.mqtt_discovery_prefix}/sensor/{self.installation_id}_audio_{_slug(zone_id)}_{key}/config", json.dumps(config, ensure_ascii=False), qos=1, retain=True)
            await self.publish_audio_state(zone)

        if payload.get("config", {}).get("zones"):
            device = {"identifiers": [f"tecnohead:{self.installation_id}:audio:groups"], "name": "TecnoHead Áudio — Grupos", "manufacturer": "TecnoHead", "model": "Áudio Multiroom", "sw_version": self.settings.app_version}
            config = {
                "name": "Compartilhar TV Piscina na Cozinha",
                "unique_id": f"tecnohead_{self.installation_id}_audio_share_pool_to_kitchen",
                "object_id": "tecnohead_audio_share_pool_to_kitchen",
                "state_topic": self._audio_state_topic("group", "share_pool_to_kitchen"),
                "command_topic": self._audio_command_topic("group", "share_pool_to_kitchen"),
                "payload_on": "ON",
                "payload_off": "OFF",
                "state_on": "ON",
                "state_off": "OFF",
                "availability_topic": self._availability_topic(),
                "retain": False,
                "device": device,
                "origin": {"name": "TecnoHead Multimídia", "sw_version": self.settings.app_version},
            }
            await client.publish(f"{self.settings.mqtt_discovery_prefix}/switch/{self.installation_id}_audio_share_pool_to_kitchen/config", json.dumps(config, ensure_ascii=False), qos=1, retain=True)
            await client.publish(self._audio_state_topic("group", "share_pool_to_kitchen"), "ON" if payload.get("config", {}).get("share_pool_tv_to_kitchen") else "OFF", qos=1, retain=True)

    async def publish_audio_state(self, zone: dict[str, Any]) -> None:
        client = self._client
        if not client or not self.connected:
            return
        zone_id = str(zone.get("zone_id"))
        entity = zone.get("entity") or {}
        volume = entity.get("volume_level")
        if volume is not None:
            await client.publish(self._audio_state_topic(zone_id, "volume"), str(round(float(volume) * 100, 1)), qos=1, retain=True)
        await client.publish(self._audio_state_topic(zone_id, "mute"), "ON" if entity.get("is_volume_muted") else "OFF", qos=1, retain=True)
        await client.publish(self._audio_state_topic(zone_id, "status"), str(zone.get("status", "unknown")), qos=1, retain=True)
        await client.publish(self._audio_state_topic(zone_id, "source"), str(entity.get("source") or "unknown"), qos=1, retain=True)
        await client.publish(self._audio_state_topic(zone_id, "airplay"), str((zone.get("airplay") or {}).get("pairing_state", "not_configured")), qos=1, retain=True)

    async def publish_area_state(self, area_id: str) -> None:
        client = self._client
        if not client or not self.connected:
            return
        state = next((item for item in await self.states() if item.get("area_id") == area_id), None)
        if not state:
            return
        mode = state.get("mode", "off")
        for key, on_mode in (("modo_cinema", "cinema"), ("modo_tv", "tv")):
            await client.publish(
                self._state_topic(area_id, key),
                "ON" if mode == on_mode else "OFF",
                qos=1,
                retain=True,
            )
        await client.publish(
            self._state_topic(area_id, "multimidia"),
            "ON" if mode in {"cinema", "tv"} else "OFF",
            qos=1,
            retain=True,
        )
        await client.publish(self._state_topic(area_id, "modo"), mode, qos=1, retain=True)
        await client.publish(self._state_topic(area_id, "fase"), state.get("phase", "idle"), qos=1, retain=True)
        await client.publish(self._state_topic(area_id, "diagnostico"), state.get("diagnostic", ""), qos=1, retain=True)
