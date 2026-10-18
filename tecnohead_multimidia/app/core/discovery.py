from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.core.ha_client import HomeAssistantClient, HomeAssistantError
from app.models import AreaDescriptor, AreaProfile, EntityDescriptor

LOGGER = logging.getLogger("tecnohead.discovery")


class AreaValidationError(ValueError):
    pass


class DiscoveryService:
    """Strict area-aware view of HA registries and current states."""

    def __init__(self, ha: HomeAssistantClient):
        self.ha = ha
        self._snapshot: dict[str, Any] | None = None
        self._lock = asyncio.Lock()
        self.last_refresh: float | None = None
        self.last_error: str | None = None

    @staticmethod
    def _effective_area(entity: dict[str, Any], devices: dict[str, dict[str, Any]]) -> str | None:
        if entity.get("area_id"):
            return entity["area_id"]
        device = devices.get(entity.get("device_id"))
        return device.get("area_id") if device else None

    @staticmethod
    def _roles(entity_id: str, state: dict[str, Any]) -> list[str]:
        domain = entity_id.split(".", 1)[0]
        attrs = state.get("attributes", {}) if isinstance(state, dict) else {}
        roles: list[str] = []
        if domain == "remote":
            roles.append("remote")
        if domain == "light":
            roles.append("light")
        if domain == "climate":
            roles.append("climate")
        if domain in {"switch", "cover"}:
            roles.append("screen_candidate")
        if domain == "media_player":
            roles.append("tv_candidate")
            if attrs.get("source_list") or "volume_level" in attrs:
                roles.append("receiver_candidate")
        return roles

    async def refresh(self) -> dict[str, Any]:
        async with self._lock:
            try:
                snapshot = await self.ha.get_registry_snapshot()
            except HomeAssistantError as exc:
                self.last_error = str(exc)
                raise
            self._snapshot = snapshot
            self.last_refresh = time.time()
            self.last_error = None
            return snapshot

    async def snapshot(self, *, refresh: bool = False) -> dict[str, Any]:
        if refresh or self._snapshot is None:
            return await self.refresh()
        return self._snapshot

    def _area_descriptors(self, profiles: dict[str, AreaProfile]) -> list[AreaDescriptor]:
        if self._snapshot is None:
            return []
        raw_areas = self._snapshot.get("areas", [])
        raw_devices = {
            item.get("id"): item
            for item in self._snapshot.get("devices", [])
            if item.get("id")
        }
        states = {
            item.get("entity_id"): item
            for item in self._snapshot.get("states", [])
            if item.get("entity_id")
        }
        raw_entities = self._snapshot.get("entities", [])
        result: list[AreaDescriptor] = []
        for area in raw_areas:
            area_id = area.get("id") or area.get("area_id")
            if not area_id:
                continue
            entities: list[EntityDescriptor] = []
            for registry in raw_entities:
                entity_id = registry.get("entity_id")
                if not entity_id or registry.get("disabled_by"):
                    continue
                effective_area = self._effective_area(registry, raw_devices)
                if effective_area != area_id:
                    continue
                state = states.get(entity_id, {})
                attributes = state.get("attributes", {}) if isinstance(state, dict) else {}
                entities.append(
                    EntityDescriptor(
                        entity_id=entity_id,
                        domain=entity_id.split(".", 1)[0],
                        state=str(state.get("state", "unknown")),
                        friendly_name=attributes.get("friendly_name"),
                        area_id=effective_area,
                        device_id=registry.get("device_id"),
                        integration=registry.get("platform") or registry.get("integration_domain"),
                        attributes=attributes,
                        roles=self._roles(entity_id, state),
                    )
                )
            profile = profiles.get(area_id)
            result.append(
                AreaDescriptor(
                    area_id=area_id,
                    name=area.get("name") or area_id,
                    aliases=area.get("aliases") or [],
                    entities=sorted(entities, key=lambda entity: entity.entity_id),
                    profile=profile,
                )
            )
        return sorted(result, key=lambda item: item.name.casefold())

    def area_descriptor(self, area_id: str) -> AreaDescriptor | None:
        """Return one already-discovered area without widening its scope."""

        return next((area for area in self._area_descriptors({}) if area.area_id == area_id), None)

    def media_players_for_area(self, area_id: str) -> list[EntityDescriptor]:
        area = self.area_descriptor(area_id)
        if not area:
            return []
        return [entity for entity in area.entities if entity.domain == "media_player"]

    async def areas(self, profiles: dict[str, AreaProfile], *, refresh: bool = False) -> list[AreaDescriptor]:
        await self.snapshot(refresh=refresh)
        return self._area_descriptors(profiles)

    def entities_for_area(self, area_id: str) -> list[EntityDescriptor]:
        return next((area.entities for area in self._area_descriptors({}) if area.area_id == area_id), [])

    def _registry_entity(self, entity_id: str) -> dict[str, Any] | None:
        if self._snapshot is None:
            return None
        return next(
            (item for item in self._snapshot.get("entities", []) if item.get("entity_id") == entity_id),
            None,
        )

    def effective_area_for_entity(self, entity_id: str) -> str | None:
        if self._snapshot is None:
            return None
        entity = self._registry_entity(entity_id)
        if not entity:
            return None
        devices = {
            item.get("id"): item
            for item in self._snapshot.get("devices", [])
            if item.get("id")
        }
        return self._effective_area(entity, devices)

    async def validate_entity(
        self,
        area_id: str,
        entity_id: str | None,
        domains: set[str],
        *,
        required: bool = False,
    ) -> dict[str, Any] | None:
        if not entity_id:
            if required:
                raise AreaValidationError("entidade obrigatória não configurada")
            return None
        await self.refresh()
        registry = self._registry_entity(entity_id)
        effective_area = self.effective_area_for_entity(entity_id)
        domain = entity_id.split(".", 1)[0]
        if not registry or effective_area != area_id or domain not in domains:
            raise AreaValidationError(
                f"Equipamento fora da área {area_id} ou domínio inválido: {entity_id}"
            )
        state = next(
            (item for item in self._snapshot.get("states", []) if item.get("entity_id") == entity_id),
            {},
        )
        return {"registry": registry, "state": state, "area_id": effective_area}

    async def validate_remote(self, area_id: str, remote_entity_id: str | None) -> dict[str, Any]:
        result = await self.validate_entity(area_id, remote_entity_id, {"remote"}, required=True)
        assert result is not None
        state = result.get("state", {})
        if state.get("state") in {"unavailable", "unknown"}:
            raise AreaValidationError(f"Emissor IR indisponível: {remote_entity_id}")
        return result

    async def entity_state(self, entity_id: str | None) -> dict[str, Any] | None:
        if not entity_id:
            return None
        if self._snapshot is not None:
            state = next(
                (item for item in self._snapshot.get("states", []) if item.get("entity_id") == entity_id),
                None,
            )
            if state is not None:
                return state
        return await self.ha.get_state(entity_id)

    def suggest_remote(self, area_id: str) -> str | None:
        for area in self._area_descriptors({}):
            if area.area_id != area_id:
                continue
            remote_ids = {entity.entity_id for entity in area.entities if "remote" in entity.roles}
            if "remote.ir_cinema" in remote_ids:
                return "remote.ir_cinema"
            return sorted(remote_ids)[0] if remote_ids else None
        return None

    def sources_for(self, area_id: str, entity_id: str | None) -> list[str]:
        for area in self._area_descriptors({}):
            if area.area_id != area_id:
                continue
            for entity in area.entities:
                if entity.entity_id == entity_id:
                    sources = entity.attributes.get("source_list", [])
                    return [str(source) for source in sources] if isinstance(sources, list) else []
        return []
