from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from datetime import UTC, datetime
from typing import Any

from app import __version__
from app.core.actions import ActionExecutor
from app.core.airplay import AirPlayEndpointManager
from app.core.audio import AudioActionError, AudioManager
from app.core.discovery import DiscoveryService
from app.core.engine import AreaEngine
from app.core.ha_client import HomeAssistantClient, HomeAssistantError
from app.core.ir_transport import HomeAssistantRemoteTransport, IRSequenceError, IRSequenceUncertain
from app.core.mqtt_bridge import MqttBridge
from app.core.presets import restore_ir_profile
from app.core.store import ConfigStore
from app.models import (
    AppConfig,
    AreaDescriptor,
    AreaProfile,
    AreaProfileUpdate,
    AudioCommandRequest,
    AudioGroupRequest,
    AudioGroupStrategy,
    AudioMuteRequest,
    AudioPlaybackRequest,
    AudioSourceRequest,
    AudioVolumeRequest,
    DiagnosticEvent,
    Mode,
    MultiroomConfig,
    MultiroomUpdate,
)
from app.settings import Settings

LOGGER = logging.getLogger("tecnohead.runtime")


class Runtime:
    def __init__(self, settings: Settings, ha: HomeAssistantClient | None = None):
        self.settings = settings
        self.store = ConfigStore(settings.data_dir)
        self.ha = ha or HomeAssistantClient(settings)
        self.discovery = DiscoveryService(self.ha)
        self.events: deque[DiagnosticEvent] = deque(maxlen=300)
        self.started_at = time.monotonic()
        self.config = AppConfig()
        self.engines: dict[str, AreaEngine] = {}
        self.actions: ActionExecutor | None = None
        self.ir: HomeAssistantRemoteTransport | None = None
        self.audio: AudioManager | None = None
        self.airplay: AirPlayEndpointManager | None = None
        self.mqtt: MqttBridge | None = None
        self._event_stop = asyncio.Event()
        self._event_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self.config = await self.store.load()
        await self.ha.start()
        self.actions = ActionExecutor(self.ha, self.discovery, self.record_event)
        self.ir = HomeAssistantRemoteTransport(self.ha, self.discovery, self.record_event)
        self.audio = AudioManager(self.ha, self.discovery, self.record_event)
        self.airplay = AirPlayEndpointManager(self.settings, self.ha, self.audio, self.record_event)
        self.audio.set_airplay_report_provider(self.airplay.report)
        await self._refresh_discovery_safe()
        await self._sync_engines()
        await self.airplay.start(self.config.audio)
        self.mqtt = MqttBridge(
            self.settings,
            self.ha,
            self.config.installation_id or "tecnohead",
            self.list_profiles,
            self.engine_states,
            self.handle_mqtt_mode,
            self.audio_payload,
            self.handle_mqtt_audio,
        )
        await self.mqtt.start()
        if self.settings.supervisor_token:
            self._event_task = asyncio.create_task(
                self.ha.state_event_stream(self.handle_state_event, self._event_stop),
                name="tecnohead-ha-events",
            )
        await self.record_event(
            event="app_started",
            message="TecnoHead Multimídia iniciado",
            result="ready_without_hardware_assumption",
        )

    async def stop(self) -> None:
        self._event_stop.set()
        if self._event_task:
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
        for engine in self.engines.values():
            engine._cancel_lights()
            if engine._task and not engine._task.done():
                engine._task.cancel()
        if self.mqtt:
            await self.mqtt.stop()
        if self.airplay:
            await self.airplay.stop()
        await self.ha.stop()

    async def _refresh_discovery_safe(self) -> None:
        try:
            await self.discovery.refresh()
        except HomeAssistantError as exc:
            await self.record_event(
                level="warning",
                event="ha_discovery_unavailable",
                message=str(exc),
                result="offline",
            )

    async def _sync_engines(self) -> None:
        if not self.actions or not self.ir:
            return
        async with self._lock:
            enabled_profiles = {profile.area_id: profile for profile in self.config.areas if profile.enabled}
            for area_id in list(self.engines):
                if area_id not in enabled_profiles:
                    self.engines[area_id]._cancel_lights()
                    del self.engines[area_id]
            for area_id, profile in enabled_profiles.items():
                if area_id in self.engines:
                    self.engines[area_id].update_profile(profile)
                else:
                    self.engines[area_id] = AreaEngine(
                        profile,
                        self.actions,
                        self.ir,
                        self.discovery,
                        self.record_event,
                        self.notify_area_state,
                    )

    async def list_profiles(self) -> list[AreaProfile]:
        return [profile.model_copy(deep=True) for profile in self.config.areas]

    async def get_profile(self, area_id: str) -> AreaProfile:
        profile = next((item for item in self.config.areas if item.area_id == area_id), None)
        if profile:
            return profile.model_copy(deep=True)
        suggested_remote = self.discovery.suggest_remote(area_id)
        return AreaProfile(area_id=area_id, ir=restore_ir_profile(suggested_remote))

    async def discover(self, *, refresh: bool = False) -> list[AreaDescriptor]:
        profiles = {profile.area_id: profile for profile in self.config.areas}
        return await self.discovery.areas(profiles, refresh=refresh)

    async def save_profile(self, area_id: str, update: AreaProfileUpdate) -> AreaProfile:
        if not self.discovery._snapshot:
            await self.discovery.refresh()
        profile = AreaProfile(area_id=area_id, **update.model_dump())
        await self._validate_profile_entities(profile)
        await self.store.upsert_area(profile)
        self.config = await self.store.snapshot()
        await self._sync_engines()
        if self.mqtt:
            await self.mqtt.sync_discovery()
        await self.record_event(
            area_id=area_id,
            event="profile_saved",
            message="Perfil da área salvo após validação de área e domínio",
            result="completed",
        )
        return profile

    async def audio_payload(self) -> dict[str, Any]:
        if not self.audio:
            raise AudioActionError("módulo de áudio não está disponível")
        return await self.audio.discovery_payload(self.config.audio)

    async def save_audio(self, update: MultiroomUpdate) -> MultiroomConfig:
        if not self.audio:
            raise AudioActionError("módulo de áudio não está disponível")
        zone_ids = [zone.zone_id for zone in update.zones]
        if len(zone_ids) != len(set(zone_ids)):
            raise ValueError("zonas de áudio duplicadas")
        if update.group_master_zone_id and update.group_master_zone_id not in zone_ids:
            raise ValueError("líder do grupo não está cadastrado")
        if any(zone_id not in zone_ids for zone_id in update.members):
            raise ValueError("membro do grupo não está cadastrado")
        await self.discovery.refresh()
        for zone in update.zones:
            if not zone.enabled:
                continue
            if not zone.area_id or not zone.media_player_entity_id:
                raise ValueError(f"zona {zone.zone_id} habilitada sem área/media_player")
            await self.discovery.validate_entity(zone.area_id, zone.media_player_entity_id, {"media_player"}, required=True)
            descriptor = self.audio._entity_descriptor(zone.area_id, zone.media_player_entity_id)
            if not self.audio._is_audio_candidate(descriptor):
                raise ValueError(f"zona {zone.zone_id}: media_player não anunciou volume, grupo ou integração LinkPlay")
        audio = MultiroomConfig.model_validate(update.model_dump(mode="json"))
        await self.store.update_audio(audio)
        self.config = await self.store.snapshot()
        if self.airplay:
            await self.airplay.apply_config(self.config.audio)
        if self.mqtt:
            await self.mqtt.sync_discovery()
        await self.record_event(
            event="audio_profile_saved",
            message="zonas de áudio salvas com validação estrita de área e domínio",
            result="completed",
        )
        return audio

    async def audio_set_volume(self, zone_id: str, request: AudioVolumeRequest) -> dict[str, Any]:
        assert self.audio is not None
        return await self.audio.set_volume(self.config.audio, zone_id, request)

    async def audio_set_mute(self, zone_id: str, request: AudioMuteRequest) -> dict[str, Any]:
        assert self.audio is not None
        return await self.audio.set_mute(self.config.audio, zone_id, request)

    async def audio_select_source(self, zone_id: str, request: AudioSourceRequest) -> dict[str, Any]:
        assert self.audio is not None
        return await self.audio.select_source(self.config.audio, zone_id, request)

    async def audio_playback(self, zone_id: str, request: AudioPlaybackRequest) -> dict[str, Any]:
        assert self.audio is not None
        return await self.audio.playback(self.config.audio, zone_id, request)

    async def audio_join(self, request: AudioGroupRequest) -> dict[str, Any]:
        assert self.audio is not None
        result = await self.audio.join(self.config.audio, request)
        audio = self.config.audio.model_copy(deep=True)
        audio.group_strategy = AudioGroupStrategy.LINKPLAY
        audio.group_master_zone_id = request.master_zone_id
        audio.members = list(dict.fromkeys([request.master_zone_id, *request.member_zone_ids]))
        await self.store.update_audio(audio)
        self.config = await self.store.snapshot()
        return result

    async def audio_share_pool_to_kitchen(self, request: AudioCommandRequest) -> dict[str, Any]:
        result = await self.audio_join(
            AudioGroupRequest(master_zone_id="pool", member_zone_ids=["kitchen"], confirmed=request.confirmed)
        )
        audio = self.config.audio.model_copy(deep=True)
        audio.share_pool_tv_to_kitchen = True
        await self.store.update_audio(audio)
        self.config = await self.store.snapshot()
        return result

    async def audio_unjoin(self, zone_id: str, request: AudioCommandRequest) -> dict[str, Any]:
        assert self.audio is not None
        result = await self.audio.unjoin(self.config.audio, zone_id, request)
        audio = self.config.audio.model_copy(deep=True)
        audio.group_strategy = AudioGroupStrategy.NONE
        audio.group_master_zone_id = None
        audio.members = []
        audio.share_pool_tv_to_kitchen = False
        await self.store.update_audio(audio)
        self.config = await self.store.snapshot()
        return result

    async def _validate_profile_entities(self, profile: AreaProfile) -> None:
        checks = (
            (profile.tv_entity_id, {"media_player"}, False),
            (profile.receiver_entity_id, {"media_player"}, False),
            (profile.screen_entity_id, {"switch", "cover"}, False),
            (profile.apple_tv_entity_id, {"media_player"}, False),
            (profile.climate_entity_id, {"climate"}, False),
        )
        for entity_id, domains, required in checks:
            await self.discovery.validate_entity(profile.area_id, entity_id, domains, required=required)
        for entity_id in profile.lighting_switch_entity_ids:
            await self.discovery.validate_entity(profile.area_id, entity_id, {"switch"}, required=True)
        if profile.ir and profile.ir.remote_entity_id:
            await self.discovery.validate_remote(profile.area_id, profile.ir.remote_entity_id)

    async def restore_presets(self, area_id: str, confirmed: bool) -> AreaProfile:
        if not confirmed:
            raise PermissionError("restauração de presets requer confirmação explícita")
        current = await self.get_profile(area_id)
        current.ir = restore_ir_profile(current.ir.remote_entity_id if current.ir else self.discovery.suggest_remote(area_id))
        await self.store.upsert_area(current)
        self.config = await self.store.snapshot()
        await self._sync_engines()
        await self.record_event(
            area_id=area_id,
            event="ir_presets_restored",
            message="Presets genéricos ON/OFF restaurados; integração HA não foi modificada",
            result="completed",
        )
        return current

    async def test_ir(self, area_id: str, direction: str, confirmed: bool) -> dict[str, Any]:
        if not confirmed:
            raise PermissionError("teste IR requer confirmação explícita")
        profile = await self.get_profile(area_id)
        if not profile.ir:
            raise IRSequenceError("perfil IR não configurado")
        assert self.ir is not None
        try:
            result = await (self.ir.send_on(profile) if direction == "on" else self.ir.send_off(profile))
            profile.ir.last_test_at = datetime.now(UTC).isoformat()
            profile.ir.last_test_result = "accepted_by_home_assistant_physical_unconfirmed"
            await self.store.upsert_area(profile)
            self.config = await self.store.snapshot()
            return result
        except (IRSequenceError, IRSequenceUncertain):
            profile.ir.last_test_at = datetime.now(UTC).isoformat()
            profile.ir.last_test_result = "failed_or_uncertain"
            await self.store.upsert_area(profile)
            self.config = await self.store.snapshot()
            raise

    async def check_ir_entity(self, area_id: str) -> dict[str, Any]:
        """Validate the configured HA remote without transmitting IR."""
        profile = await self.get_profile(area_id)
        remote_id = profile.ir.remote_entity_id if profile.ir else None
        result = await self.discovery.validate_remote(area_id, remote_id)
        state = result.get("state", {})
        attributes = state.get("attributes", {}) if isinstance(state, dict) else {}
        return {
            "ok": True,
            "entity_id": remote_id,
            "domain": "remote",
            "area_id": area_id,
            "state": state.get("state", "unknown"),
            "friendly_name": attributes.get("friendly_name"),
            "supported_features": attributes.get("supported_features"),
            "physical_transmission": "não executada",
        }

    async def request_mode(self, area_id: str, mode: Mode, *, reason: str = "explicit") -> dict[str, Any]:
        profile = await self.get_profile(area_id)
        if not profile.enabled:
            raise ValueError("a área precisa estar habilitada antes de executar cenas")
        await self._sync_engines()
        engine = self.engines.get(area_id)
        if not engine:
            raise ValueError("motor da área não está disponível")
        return await engine.request_mode(mode, reason=reason)

    async def wait_area(self, area_id: str) -> None:
        engine = self.engines.get(area_id)
        if engine:
            await engine.wait_idle()

    async def handle_mqtt_mode(self, area_id: str, mode: Mode, confirmed: bool) -> None:
        try:
            await self.request_mode(area_id, mode, reason="mqtt")
        except Exception as exc:
            await self.record_event(
                area_id=area_id,
                level="error",
                event="mqtt_command_failed",
                message=str(exc),
                result="failed",
            )

    async def handle_mqtt_audio(self, zone_id: str, key: str, payload: str) -> None:
        try:
            if key == "volume":
                await self.audio_set_volume(zone_id, AudioVolumeRequest(volume_percent=int(float(payload)), confirmed=True))
            elif key == "mute":
                await self.audio_set_mute(zone_id, AudioMuteRequest(is_volume_muted=payload.casefold() in {"on", "1", "true"}, confirmed=True))
            elif key == "source":
                await self.audio_select_source(zone_id, AudioSourceRequest(source=payload, confirmed=True))
            elif zone_id == "group" and key == "share_pool_to_kitchen":
                if payload.casefold() in {"on", "1", "true"}:
                    await self.audio_share_pool_to_kitchen(AudioCommandRequest(confirmed=True))
                else:
                    await self.audio_unjoin("pool", AudioCommandRequest(confirmed=True))
            elif zone_id == "group" and key == "unjoin_pool" and payload.casefold() in {"on", "1", "true"}:
                await self.audio_unjoin("pool", AudioCommandRequest(confirmed=True))
            else:
                return
            if self.mqtt:
                await self.mqtt.publish_audio_discovery()
        except Exception as exc:
            await self.record_event(event="mqtt_audio_command_failed", message=str(exc), level="error", result="failed")

    async def handle_state_event(self, event: dict[str, Any]) -> None:
        data = event.get("data", {})
        entity_id = data.get("entity_id")
        if not entity_id:
            return
        if self.airplay:
            await self.airplay.handle_state_event(event)
        area_id = self.discovery.effective_area_for_entity(entity_id)
        if not area_id:
            return
        engine = self.engines.get(area_id)
        if engine:
            await engine.handle_state_event(event)
            await engine.handle_climate_state_event(event)

    async def notify_area_state(self, area_id: str) -> None:
        if self.mqtt:
            await self.mqtt.publish_area_state(area_id)

    async def engine_states(self) -> list[dict[str, Any]]:
        return [engine.status() for engine in self.engines.values()]

    async def status(self) -> dict[str, Any]:
        audio_status = self.audio.status_payload(self.config.audio) if self.audio else {"zones": [], "airplay": {"state": "not_started"}}
        return {
            "app_version": __version__,
            "uptime_seconds": round(time.monotonic() - self.started_at, 1),
            "home_assistant": {
                "available": self.discovery.last_error is None and self.discovery._snapshot is not None,
                "last_discovery": self.discovery.last_refresh,
                "last_error": self.discovery.last_error,
            },
            "mqtt": self.mqtt.status() if self.mqtt else {"connected": False, "last_error": "not_started"},
            "audio": audio_status,
            "areas": await self.engine_states(),
            "events": [event.model_dump(mode="json") for event in list(self.events)[-50:]],
        }

    async def diagnostics(self) -> dict[str, Any]:
        status = await self.status()
        profiles = []
        for profile in self.config.areas:
            data = profile.model_dump(mode="json")
            if data.get("ir"):
                data["ir"]["on"]["value"] = "[redacted]"
                data["ir"]["off"]["value"] = "[redacted]"
            profiles.append(data)
        audio = await self.audio_payload() if self.audio else {"config": {}, "zones": [], "areas": [], "airplay": {"state": "not_started"}}
        return {"status": status, "profiles": profiles, "areas": [item.model_dump(mode="json") for item in await self.discover()], "audio": audio}

    async def record_event(
        self,
        *,
        event: str,
        message: str,
        area_id: str | None = None,
        level: str = "info",
        entity_id: str | None = None,
        command_kind: str | None = None,
        result: str | None = None,
        physical_confirmation: str = "not_observable",
    ) -> None:
        safe_message = message.replace("\n", " ")[:500]
        self.events.append(
            DiagnosticEvent(
                timestamp=datetime.now(UTC).isoformat(),
                area_id=area_id,
                level=level,
                event=event,
                message=safe_message,
                entity_id=entity_id,
                command_kind=command_kind,
                result=result,
                physical_confirmation=physical_confirmation,
            )
        )
        log = LOGGER.error if level == "error" else LOGGER.warning if level == "warning" else LOGGER.info
        log("%s: %s", event, safe_message)
