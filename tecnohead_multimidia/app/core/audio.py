from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.discovery import AreaValidationError, DiscoveryService
from app.core.ha_client import HomeAssistantClient, HomeAssistantError
from app.models import (
    AudioCommandRequest,
    AudioGroupRequest,
    AudioMuteRequest,
    AudioPlaybackRequest,
    AudioPriority,
    AudioSourceRequest,
    AudioVolumeRequest,
    AudioZoneProfile,
    MultiroomConfig,
)

LOGGER = logging.getLogger("tecnohead.audio")

ZONE_LABELS = {"kitchen": "Cozinha", "pool": "Piscina"}


class AudioActionError(RuntimeError):
    pass


class AudioManager:
    """Area-scoped audio controls using Home Assistant media_player services.

    This class intentionally does not implement a proprietary LinkPlay socket
    client. LinkPlay capability is accepted only when HA exposes a real
    media_player and the command is sent through the HA service API.
    """

    def __init__(
        self,
        ha: HomeAssistantClient,
        discovery: DiscoveryService,
        event_recorder: Callable[..., Awaitable[None]] | None = None,
    ) -> None:
        self.ha = ha
        self.discovery = discovery
        self.event_recorder = event_recorder

    async def _record(self, **kwargs: Any) -> None:
        if self.event_recorder:
            await self.event_recorder(**kwargs)

    @staticmethod
    def _safe_attr(attrs: dict[str, Any], key: str, default: Any = None) -> Any:
        value = attrs.get(key, default)
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, list):
            return [str(item) for item in value]
        return default

    @staticmethod
    def _is_tv_or_arc_source(source: str | None) -> bool:
        if not source:
            return False
        value = source.casefold()
        return any(token in value for token in ("arc", "tv", "hdmi"))

    @staticmethod
    def _zone_config(config: MultiroomConfig, zone_id: str) -> AudioZoneProfile:
        zone = next((item for item in config.zones if item.zone_id == zone_id), None)
        if not zone:
            raise AudioActionError(f"zona de áudio não configurada: {zone_id}")
        return zone

    def _entity_descriptor(self, area_id: str | None, entity_id: str | None) -> dict[str, Any] | None:
        if not area_id or not entity_id:
            return None
        area = self.discovery.area_descriptor(area_id)
        if not area:
            return None
        entity = next((item for item in area.entities if item.entity_id == entity_id), None)
        if not entity:
            return None
        attrs = entity.attributes
        source_list = attrs.get("source_list")
        if not isinstance(source_list, list):
            source_list = []
        group_members = attrs.get("group_members")
        if not isinstance(group_members, list):
            group_members = []
        volume_level = attrs.get("volume_level")
        try:
            volume_level = float(volume_level) if volume_level is not None else None
        except (TypeError, ValueError):
            volume_level = None
        supported_features = attrs.get("supported_features")
        try:
            supported_features = int(supported_features) if supported_features is not None else 0
        except (TypeError, ValueError):
            supported_features = 0
        return {
            "entity_id": entity.entity_id,
            "friendly_name": entity.friendly_name,
            "area_id": entity.area_id,
            "integration": entity.integration,
            "state": entity.state,
            "available": entity.state not in {"unavailable", "unknown"},
            "device_class": self._safe_attr(attrs, "device_class"),
            "supported_features": supported_features,
            "source": self._safe_attr(attrs, "source"),
            "media_title": self._safe_attr(attrs, "media_title"),
            "media_artist": self._safe_attr(attrs, "media_artist"),
            "media_album_name": self._safe_attr(attrs, "media_album_name"),
            "source_list": [str(item) for item in source_list],
            "volume_level": volume_level,
            "is_volume_muted": self._safe_attr(attrs, "is_volume_muted"),
            "group_members": [str(item) for item in group_members],
            "supports": {
                "volume": volume_level is not None,
                "mute": "is_volume_muted" in attrs or bool(supported_features & 8),
                "source": bool(source_list),
                "group": bool(group_members) or bool(supported_features & 524288),
                "playback": bool(supported_features & (1 | 16384 | 32768 | 4096)),
            },
        }

    def _zone_status(self, zone: AudioZoneProfile) -> dict[str, Any]:
        base = {
            "zone_id": zone.zone_id,
            "label": ZONE_LABELS.get(zone.zone_id, zone.zone_id),
            "enabled": zone.enabled,
            "area_id": zone.area_id,
            "entity_id": zone.media_player_entity_id,
            "priority": zone.priority.value,
            "max_volume_percent": zone.max_volume_percent,
            "airplay": {
                "enabled": zone.airplay.enabled,
                "service_name": zone.airplay.service_name or f"TecnoHead {ZONE_LABELS.get(zone.zone_id, zone.zone_id)}",
                "stable_id": zone.airplay.stable_id,
                "listen_port": zone.airplay.listen_port,
                "pairing_state": zone.airplay.pairing_state,
            },
        }
        entity = self._entity_descriptor(zone.area_id, zone.media_player_entity_id)
        if not zone.enabled or not zone.area_id or not zone.media_player_entity_id:
            return {**base, "status": "unconfigured", "diagnostic": "zona sem área ou media_player configurado", "entity": entity}
        if not entity:
            return {
                **base,
                "status": "area_mismatch",
                "diagnostic": "media_player não pertence à área selecionada",
                "entity": None,
            }
        diagnostic = "pronto"
        status = "ready"
        if not entity["available"]:
            status = "unavailable"
            diagnostic = "media_player indisponível ou sem estado confirmado"
        elif not entity["supports"]["volume"]:
            status = "degraded"
            diagnostic = "volume_level não foi anunciado pelo media_player"
        return {**base, "status": status, "diagnostic": diagnostic, "entity": entity}

    async def discovery_payload(self, config: MultiroomConfig) -> dict[str, Any]:
        await self.discovery.refresh()
        areas = await self.discovery.areas({})
        area_options = []
        for area in areas:
            area_options.append(
                {
                    "area_id": area.area_id,
                    "name": area.name,
                    "media_players": [
                        self._entity_descriptor(area.area_id, entity.entity_id)
                        for entity in area.entities
                        if entity.domain == "media_player"
                    ],
                }
            )
        statuses = [self._zone_status(zone) for zone in config.zones]
        for zone_id in ("kitchen", "pool"):
            if not any(item["zone_id"] == zone_id for item in statuses):
                statuses.append(
                    {
                        "zone_id": zone_id,
                        "label": ZONE_LABELS[zone_id],
                        "enabled": False,
                        "area_id": None,
                        "entity_id": None,
                        "priority": AudioPriority.HDMI_ARC.value if zone_id == "pool" else AudioPriority.NORMAL.value,
                        "max_volume_percent": 30,
                        "airplay": {"enabled": False, "service_name": f"TecnoHead {ZONE_LABELS[zone_id]}", "stable_id": None, "listen_port": None, "pairing_state": "not_configured"},
                        "status": "unconfigured",
                        "diagnostic": "zona ainda não cadastrada",
                        "entity": None,
                    }
                )
        return {
            "config": config.model_dump(mode="json"),
            "areas": area_options,
            "zones": statuses,
            "airplay": self.airplay_report(config, statuses),
        }

    def status_payload(self, config: MultiroomConfig) -> dict[str, Any]:
        statuses = [self._zone_status(zone) for zone in config.zones]
        for zone_id in ("kitchen", "pool"):
            if not any(item["zone_id"] == zone_id for item in statuses):
                statuses.append({"zone_id": zone_id, "label": ZONE_LABELS[zone_id], "enabled": False, "status": "unconfigured", "diagnostic": "zona ainda não cadastrada"})
        return {"zones": statuses, "airplay": self.airplay_report(config, statuses), "group_strategy": config.group_strategy.value}

    @staticmethod
    def airplay_report(config: MultiroomConfig, statuses: list[dict[str, Any]]) -> dict[str, Any]:
        configured = [item for item in statuses if item.get("enabled") and item.get("entity_id")]
        linkplay_ready = all(
            (item.get("entity") or {}).get("integration") in {"linkplay", "link_play"}
            for item in configured
        ) if configured else False
        if not configured:
            reason = "configure primeiro os media_players físicos das zonas"
            state = "not_configured"
        elif not linkplay_ready:
            reason = "a integração LinkPlay não foi observada nas entidades HA configuradas; a ponte PCM não é segura sem um destino físico comprovado"
            state = "blocked"
        else:
            reason = "receptor LinkPlay observado; ponte Shairport/NQPTP ainda depende de compilação e teste físico"
            state = "not_homologated"
        return {
            "state": state,
            "reason": reason,
            "shairport_sync": "not_started",
            "airplay2_handshake": "not_tested",
            "nqptp": "not_started",
            "mdns": "not_started",
            "physical_audio": "not_tested",
            "group_strategy": config.group_strategy.value,
        }

    async def _checked_zone(self, config: MultiroomConfig, zone_id: str) -> tuple[AudioZoneProfile, dict[str, Any], dict[str, Any]]:
        zone = self._zone_config(config, zone_id)
        if not zone.enabled or not zone.area_id or not zone.media_player_entity_id:
            raise AudioActionError(f"zona {zone_id} não está habilitada/configurada")
        try:
            checked = await self.discovery.validate_entity(zone.area_id, zone.media_player_entity_id, {"media_player"}, required=True)
        except (AreaValidationError, HomeAssistantError) as exc:
            raise AudioActionError(str(exc)) from exc
        assert checked is not None
        state = checked.get("state", {})
        if state.get("state") in {"unknown", "unavailable"}:
            raise AudioActionError(f"media_player indisponível: {zone.media_player_entity_id}")
        entity = self._entity_descriptor(zone.area_id, zone.media_player_entity_id) or {}
        return zone, entity, state

    async def set_volume(self, config: MultiroomConfig, zone_id: str, request: AudioVolumeRequest) -> dict[str, Any]:
        if not request.confirmed:
            raise PermissionError("alteração de volume requer confirmação explícita")
        zone, entity, _ = await self._checked_zone(config, zone_id)
        if not entity.get("supports", {}).get("volume"):
            raise AudioActionError("a entidade não anunciou volume_level; não há slider absoluto seguro")
        if request.volume_percent > zone.max_volume_percent:
            raise AudioActionError(f"volume acima do limite seguro configurado ({zone.max_volume_percent}%)")
        await self.ha.call_service(
            "media_player",
            "volume_set",
            entity_id=zone.media_player_entity_id or "",
            data={"volume_level": request.volume_percent / 100.0},
        )
        await self._record(
            area_id=zone.area_id,
            event="audio_volume_set",
            message=f"volume de {zone.zone_id} solicitado",
            entity_id=zone.media_player_entity_id,
            command_kind="media_player.volume_set",
            result="accepted_by_home_assistant",
            physical_confirmation="not_observable",
        )
        return {"ok": True, "zone_id": zone_id, "requested_percent": request.volume_percent}

    async def set_mute(self, config: MultiroomConfig, zone_id: str, request: AudioMuteRequest) -> dict[str, Any]:
        if not request.confirmed:
            raise PermissionError("mudo requer confirmação explícita")
        zone, entity, _ = await self._checked_zone(config, zone_id)
        if not entity.get("supports", {}).get("mute"):
            raise AudioActionError("a entidade não anunciou suporte de mudo")
        await self.ha.call_service(
            "media_player",
            "volume_mute",
            entity_id=zone.media_player_entity_id or "",
            data={"is_volume_muted": request.is_volume_muted},
        )
        await self._record(
            area_id=zone.area_id,
            event="audio_mute_set",
            message=f"mudo de {zone.zone_id} solicitado",
            entity_id=zone.media_player_entity_id,
            command_kind="media_player.volume_mute",
            result="accepted_by_home_assistant",
            physical_confirmation="not_observable",
        )
        return {"ok": True, "zone_id": zone_id, "is_volume_muted": request.is_volume_muted}

    async def select_source(self, config: MultiroomConfig, zone_id: str, request: AudioSourceRequest) -> dict[str, Any]:
        if not request.confirmed:
            raise PermissionError("troca de fonte requer confirmação explícita")
        zone, entity, _ = await self._checked_zone(config, zone_id)
        sources = entity.get("source_list", [])
        selected = next((item for item in sources if item.casefold() == request.source.casefold()), None)
        if not selected:
            raise AudioActionError("fonte não foi anunciada pela entidade HA")
        current = entity.get("source")
        if zone.priority is AudioPriority.HDMI_ARC and self._is_tv_or_arc_source(current) and not self._is_tv_or_arc_source(selected):
            await self._record(
                area_id=zone.area_id,
                level="warning",
                event="audio_arc_override_requested",
                message="troca explícita pode substituir a prioridade HDMI ARC",
                entity_id=zone.media_player_entity_id,
                command_kind="media_player.select_source",
                result="awaiting_explicit_policy",
            )
        await self.ha.call_service(
            "media_player",
            "select_source",
            entity_id=zone.media_player_entity_id or "",
            data={"source": selected},
        )
        await self._record(
            area_id=zone.area_id,
            event="audio_source_selected",
            message=f"fonte {selected} solicitada para {zone.zone_id}",
            entity_id=zone.media_player_entity_id,
            command_kind="media_player.select_source",
            result="accepted_by_home_assistant",
            physical_confirmation="not_observable",
        )
        return {"ok": True, "zone_id": zone_id, "source": selected}

    async def playback(self, config: MultiroomConfig, zone_id: str, request: AudioPlaybackRequest) -> dict[str, Any]:
        if not request.confirmed:
            raise PermissionError("reprodução requer confirmação explícita")
        zone, entity, _ = await self._checked_zone(config, zone_id)
        if not entity.get("supports", {}).get("playback"):
            raise AudioActionError("a entidade não anunciou suporte de reprodução")
        await self.ha.call_service("media_player", f"media_{request.action}", entity_id=zone.media_player_entity_id or "", data={})
        await self._record(
            area_id=zone.area_id,
            event="audio_playback_requested",
            message=f"ação {request.action} solicitada para {zone.zone_id}",
            entity_id=zone.media_player_entity_id,
            command_kind=f"media_player.media_{request.action}",
            result="accepted_by_home_assistant",
            physical_confirmation="not_observable",
        )
        return {"ok": True, "zone_id": zone_id, "action": request.action}

    async def join(self, config: MultiroomConfig, request: AudioGroupRequest) -> dict[str, Any]:
        if not request.confirmed:
            raise PermissionError("agrupamento de áudio requer confirmação explícita")
        master, master_entity, _ = await self._checked_zone(config, request.master_zone_id)
        if not master_entity.get("supports", {}).get("group"):
            raise AudioActionError("a entidade líder não anunciou suporte de grupo multiroom")
        if request.master_zone_id in request.member_zone_ids:
            raise AudioActionError("a zona líder não pode ser membro dela mesma")
        members: list[str] = []
        for zone_id in request.member_zone_ids:
            zone, _, _ = await self._checked_zone(config, zone_id)
            if zone.media_player_entity_id:
                members.append(zone.media_player_entity_id)
        await self.ha.call_service("media_player", "join", entity_id=master.media_player_entity_id or "", data={"group_members": members})
        await self._record(
            area_id=master.area_id,
            event="audio_linkplay_join_requested",
            message="agrupamento enviado pela API media_player.join; confirmação física pendente",
            entity_id=master.media_player_entity_id,
            command_kind="media_player.join",
            result="accepted_by_home_assistant",
        )
        return {"ok": True, "master_zone_id": request.master_zone_id, "member_zone_ids": request.member_zone_ids}

    async def unjoin(self, config: MultiroomConfig, zone_id: str, request: AudioCommandRequest) -> dict[str, Any]:
        if not request.confirmed:
            raise PermissionError("separação de áudio requer confirmação explícita")
        zone, _, _ = await self._checked_zone(config, zone_id)
        await self.ha.call_service("media_player", "unjoin", entity_id=zone.media_player_entity_id or "", data={})
        await self._record(
            area_id=zone.area_id,
            event="audio_linkplay_unjoin_requested",
            message="separação enviada pela API media_player.unjoin; ARC não foi reconfigurado",
            entity_id=zone.media_player_entity_id,
            command_kind="media_player.unjoin",
            result="accepted_by_home_assistant",
        )
        return {"ok": True, "zone_id": zone_id}

