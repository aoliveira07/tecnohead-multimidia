from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.discovery import AreaValidationError, DiscoveryService
from app.core.ha_client import HomeAssistantClient, HomeAssistantError
from app.models import AreaProfile, IRCommand

LOGGER = logging.getLogger("tecnohead.ir")


class IRSequenceUncertain(RuntimeError):
    """The App cannot safely know whether a multi-call IR sequence completed."""


class IRSequenceError(RuntimeError):
    pass


class HomeAssistantRemoteTransport:
    """Transport abstraction backed only by remote.send_command in HA."""

    def __init__(
        self,
        ha: HomeAssistantClient,
        discovery: DiscoveryService,
        event_recorder: Callable[..., Awaitable[None]] | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self.ha = ha
        self.discovery = discovery
        self.event_recorder = event_recorder
        self.sleep = sleep
        self.monotonic = monotonic

    async def _record(self, **kwargs: Any) -> None:
        if self.event_recorder:
            await self.event_recorder(**kwargs)

    @staticmethod
    def _data(command: IRCommand) -> dict[str, str]:
        data: dict[str, str] = {"command": command.to_ha_command()}
        if command.device:
            data["device"] = command.device
        return data

    async def _call_once(self, area: AreaProfile, command_kind: str, command: IRCommand) -> dict[str, Any]:
        remote_id = area.ir.remote_entity_id if area.ir else None
        if not remote_id:
            raise IRSequenceError("nenhum emissor IR foi selecionado para a área")
        try:
            await self.discovery.validate_remote(area.area_id, remote_id)
            started = self.monotonic()
            result = await self.ha.call_service(
                "remote",
                "send_command",
                entity_id=remote_id,
                data=self._data(command),
            )
            finished = self.monotonic()
        except (AreaValidationError, HomeAssistantError) as exc:
            await self._record(
                area_id=area.area_id,
                level="error",
                event="ir_call_failed",
                message=str(exc),
                entity_id=remote_id,
                command_kind=command_kind,
                result="failed",
            )
            raise IRSequenceError(str(exc)) from exc
        await self._record(
            area_id=area.area_id,
            event="ir_call_completed",
            message=f"remote.send_command concluído ({command_kind})",
            entity_id=remote_id,
            command_kind=command_kind,
            result="accepted_by_home_assistant",
        )
        return {
            "entity_id": remote_id,
            "started_monotonic": started,
            "returned_monotonic": finished,
            "ha_result": result,
        }

    async def send_on(self, area: AreaProfile) -> dict[str, Any]:
        if not area.ir:
            raise IRSequenceError("perfil IR não configurado")
        calls: list[dict[str, Any]] = []
        for index in range(area.ir.on_sends):
            if index:
                await self.sleep(area.ir.on_interval_seconds)
            calls.append(await self._call_once(area, "projector_on", area.ir.on))
        return {"direction": "on", "calls": calls, "physical_confirmation": "not_observable"}

    async def send_off(self, area: AreaProfile) -> dict[str, Any]:
        if not area.ir:
            raise IRSequenceError("perfil IR não configurado")
        calls: list[dict[str, Any]] = []
        gap_after_return: list[float] = []
        for index in range(area.ir.off_sends):
            if index:
                previous_return = calls[-1]["returned_monotonic"]
                try:
                    await self.sleep(area.ir.off_interval_seconds)
                except asyncio.CancelledError as exc:
                    await self._record(
                        area_id=area.area_id,
                        level="error",
                        event="ir_sequence_uncertain",
                        message="sequência OFF cancelada durante a espera; segunda chamada não foi enviada",
                        entity_id=area.ir.remote_entity_id,
                        command_kind="projector_off",
                        result="uncertain",
                    )
                    raise IRSequenceUncertain("sequência OFF cancelada durante a espera") from exc
                before_call = self.monotonic()
                gap_after_return.append(before_call - previous_return)
            calls.append(await self._call_once(area, "projector_off", area.ir.off))
        return {
            "direction": "off",
            "calls": calls,
            "gaps_after_return_seconds": gap_after_return,
            "physical_confirmation": "not_observable",
        }
