from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.discovery import AreaValidationError, DiscoveryService
from app.core.ha_client import HomeAssistantClient, HomeAssistantError
from app.models import AreaProfile

LOGGER = logging.getLogger("tecnohead.actions")


class ActionError(RuntimeError):
    pass


class ActionExecutor:
    """Validated, area-scoped HA service calls for non-IR equipment."""

    def __init__(
        self,
        ha: HomeAssistantClient,
        discovery: DiscoveryService,
        event_recorder: Callable[..., Awaitable[None]] | None = None,
    ):
        self.ha = ha
        self.discovery = discovery
        self.event_recorder = event_recorder
        self._last_fan_change: dict[str, float] = {}
        self._fan_mode_state: dict[str, str] = {}
        self._above_high_since: dict[str, float] = {}

    async def _record(self, **kwargs: Any) -> None:
        if self.event_recorder:
            await self.event_recorder(**kwargs)

    async def call(
        self,
        area: AreaProfile,
        entity_id: str | None,
        domains: set[str],
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
        *,
        required: bool = False,
    ) -> Any:
        if not entity_id:
            if required:
                raise ActionError(f"entidade obrigatória não configurada para {service}")
            return None
        try:
            checked = await self.discovery.validate_entity(area.area_id, entity_id, domains, required=True)
            assert checked is not None
            state = checked.get("state", {})
            if state.get("state") in {"unavailable", "unknown"}:
                raise ActionError(f"entidade indisponível: {entity_id}")
            result = await self.ha.call_service(domain, service, entity_id=entity_id, data=data or {})
        except (AreaValidationError, HomeAssistantError) as exc:
            await self._record(
                area_id=area.area_id,
                level="error",
                event="ha_action_failed",
                message=str(exc),
                entity_id=entity_id,
                command_kind=f"{domain}.{service}",
                result="failed",
            )
            raise ActionError(str(exc)) from exc
        await self._record(
            area_id=area.area_id,
            event="ha_action_completed",
            message=f"{domain}.{service} concluído",
            entity_id=entity_id,
            command_kind=f"{domain}.{service}",
            result="accepted_by_home_assistant",
            physical_confirmation="state_observed_when_available",
        )
        return result

    async def apply_receiver(self, area: AreaProfile, source: str | None, volume: float) -> list[str]:
        if not area.receiver_entity_id:
            return ["receiver não configurado"]
        warnings: list[str] = []
        await self.call(area, area.receiver_entity_id, {"media_player"}, "media_player", "turn_on")
        if source:
            await self.call(
                area,
                area.receiver_entity_id,
                {"media_player"},
                "media_player",
                "select_source",
                {"source": source},
            )
        else:
            warnings.append("fonte do receiver não configurada")
        await self.call(
            area,
            area.receiver_entity_id,
            {"media_player"},
            "media_player",
            "volume_set",
            {"volume_level": max(0.0, min(float(volume), 1.0))},
        )
        return warnings

    async def apply_climate(self, area: AreaProfile) -> list[str]:
        profile = area.climate
        if not profile.enabled or not area.climate_entity_id:
            return []
        warnings: list[str] = []
        checked = await self.discovery.validate_entity(area.area_id, area.climate_entity_id, {"climate"}, required=True)
        assert checked is not None
        state = checked.get("state", {})
        attributes = state.get("attributes", {}) if isinstance(state, dict) else {}
        state_value = state.get("state")
        if state_value in {"unavailable", "unknown"}:
            raise ActionError(f"climate indisponível: {area.climate_entity_id}")
        hvac_modes = [str(item) for item in attributes.get("hvac_modes", [])]
        cool = next((mode for mode in hvac_modes if mode.casefold() == "cool"), None)
        if cool:
            await self.call(
                area,
                area.climate_entity_id,
                {"climate"},
                "climate",
                "set_hvac_mode",
                {"hvac_mode": cool},
            )
        else:
            warnings.append("climate não anunciou hvac_mode cool")
        await self.call(
            area,
            area.climate_entity_id,
            {"climate"},
            "climate",
            "set_temperature",
            {"temperature": profile.setpoint_c},
        )

        current_temperature = attributes.get("current_temperature")
        if current_temperature is None and profile.temperature_sensor_entity_id:
            sensor = await self.discovery.validate_entity(
                area.area_id,
                profile.temperature_sensor_entity_id,
                {"sensor"},
                required=False,
            )
            if sensor:
                sensor_state = sensor.get("state", {}).get("state")
                try:
                    current_temperature = float(sensor_state)
                except (TypeError, ValueError):
                    current_temperature = None
        try:
            current_temperature = float(current_temperature)
        except (TypeError, ValueError):
            current_temperature = None

        fan_modes = [str(item) for item in attributes.get("fan_modes", [])]
        if current_temperature is None:
            warnings.append("temperatura atual indisponível; ventilação dinâmica não foi comutada")
        else:
            if current_temperature >= profile.high_threshold_c:
                since = self._above_high_since.setdefault(area.climate_entity_id, time.monotonic())
                wants_high = (
                    area.climate_entity_id not in self._fan_mode_state
                    or time.monotonic() - since >= profile.high_duration_seconds
                )
            else:
                self._above_high_since.pop(area.climate_entity_id, None)
                wants_high = False
            requested = profile.high_fan_mode if wants_high else profile.low_fan_mode
            if not requested:
                candidates = (
                    ("high", "turbo", "strong", "maximum", "max", "powerful")
                    if wants_high
                    else ("low", "silent", "quiet", "minimum", "min")
                )
                requested = next(
                    (mode for mode in fan_modes if mode.casefold() in candidates),
                    None,
                )
            if requested and any(mode.casefold() == requested.casefold() for mode in fan_modes):
                now = time.monotonic()
                last_change = self._last_fan_change.get(area.climate_entity_id, 0.0)
                current_fan = self._fan_mode_state.get(area.climate_entity_id)
                if (
                    current_fan
                    and current_fan.casefold() == requested.casefold()
                ):
                    pass
                elif now - last_change >= profile.minimum_fan_change_seconds:
                    await self.call(
                        area,
                        area.climate_entity_id,
                        {"climate"},
                        "climate",
                        "set_fan_mode",
                        {"fan_mode": requested},
                    )
                    self._last_fan_change[area.climate_entity_id] = now
                    self._fan_mode_state[area.climate_entity_id] = requested
            elif requested:
                warnings.append(f"fan_mode não suportado pelo dispositivo: {requested}")
            else:
                warnings.append("fan_mode alto/baixo não foi anunciado pelo dispositivo")

        swing_modes = [str(item) for item in attributes.get("swing_modes", [])]
        vane_mode = profile.vane_mode
        if not vane_mode:
            vane_mode = next(
                (
                    mode
                    for mode in swing_modes
                    if any(token in mode.casefold() for token in ("up", "top", "upper", "ceiling", "cima"))
                ),
                None,
            )
        if vane_mode and any(mode.casefold() == vane_mode.casefold() for mode in swing_modes):
            await self.call(
                area,
                area.climate_entity_id,
                {"climate"},
                "climate",
                "set_swing_mode",
                {"swing_mode": vane_mode},
            )
        else:
            warnings.append("posição fixa superior da aleta não foi anunciada; etapa não confirmada")
        return warnings

    async def lights_in_area(self, area_id: str) -> tuple[list[str], list[str]]:
        await self.discovery.refresh()
        entities = self.discovery.entities_for_area(area_id)
        light_entities = [entity.entity_id for entity in entities if entity.domain == "light"]
        configured_switches = [
            entity.entity_id
            for entity in entities
            if entity.domain == "switch" and entity.entity_id in set(self._configured_switches(area_id))
        ]
        return light_entities, configured_switches

    def _configured_switches(self, area_id: str) -> list[str]:
        # The caller supplies the current area profile through a small cache in
        # Runtime; this fallback is intentionally empty for strict safety.
        return []

    async def turn_off_lights(self, area: AreaProfile) -> list[str]:
        await self.discovery.refresh()
        entities = self.discovery.entities_for_area(area.area_id)
        light_ids = [entity.entity_id for entity in entities if entity.domain == "light"]
        area_switches = {
            entity.entity_id
            for entity in entities
            if entity.domain == "switch" and entity.entity_id in set(area.lighting_switch_entity_ids)
        }
        failures: list[str] = []
        for entity_id in [*light_ids, *sorted(area_switches)]:
            domain = entity_id.split(".", 1)[0]
            try:
                await self.call(area, entity_id, {domain}, domain, "turn_off")
            except ActionError as exc:
                failures.append(f"{entity_id}: {exc}")
        return failures
