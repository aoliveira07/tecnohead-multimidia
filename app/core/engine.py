from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.actions import ActionError, ActionExecutor
from app.core.discovery import DiscoveryService
from app.core.ir_transport import HomeAssistantRemoteTransport, IRSequenceError, IRSequenceUncertain
from app.models import AreaProfile, Mode, Phase

LOGGER = logging.getLogger("tecnohead.engine")


class AreaEngine:
    """Single-area state machine with a lock and no YAML automation dependency."""

    def __init__(
        self,
        profile: AreaProfile,
        actions: ActionExecutor,
        ir: HomeAssistantRemoteTransport,
        discovery: DiscoveryService,
        event_recorder: Callable[..., Awaitable[None]],
        state_changed: Callable[[str], Awaitable[None]] | None = None,
    ):
        self.profile = profile
        self.actions = actions
        self.ir = ir
        self.discovery = discovery
        self.event_recorder = event_recorder
        self.state_changed = state_changed
        self.mode = Mode.OFF
        self.requested_mode = Mode.OFF
        self.phase = Phase.IDLE
        self.projector_intent = "unknown"
        self.diagnostic = "Pronto"
        self.last_transition_at: float | None = None
        self.last_lights_schedule_at: float | None = None
        self.last_lights_off_at: float | None = None
        self._task: asyncio.Task[None] | None = None
        self._lights_task: asyncio.Task[None] | None = None
        self._pending_mode: Mode | None = None
        self._generation = 0
        self._lock = asyncio.Lock()
        self._expected_tv_state: str | None = None
        self._expected_tv_until = 0.0
        self._external_tv_task: asyncio.Task[None] | None = None
        self._climate_task: asyncio.Task[None] | None = None
        self._request_monotonic = time.monotonic()

    def update_profile(self, profile: AreaProfile) -> None:
        self.profile = profile

    async def _record(self, **kwargs: Any) -> None:
        await self.event_recorder(area_id=self.profile.area_id, **kwargs)
        if self.state_changed:
            await self.state_changed(self.profile.area_id)

    def _status_diagnostic(self) -> str:
        return self.diagnostic

    def status(self) -> dict[str, Any]:
        return {
            "area_id": self.profile.area_id,
            "mode": self.mode.value,
            "requested_mode": self.requested_mode.value,
            "phase": self.phase.value,
            "projector_intent": self.projector_intent,
            "diagnostic": self._status_diagnostic(),
            "last_transition_at": self.last_transition_at,
            "last_lights_schedule_at": self.last_lights_schedule_at,
            "last_lights_off_at": self.last_lights_off_at,
            "tv_input_blocked": self.requested_mode is Mode.CINEMA or self.phase in {Phase.STARTING, Phase.ACTIVE} and self.mode is Mode.CINEMA,
        }

    async def request_mode(self, mode: Mode, *, reason: str = "explicit") -> dict[str, Any]:
        async with self._lock:
            if not self.profile.enabled:
                self.diagnostic = "Área desabilitada no TecnoHead Multimídia"
                self.phase = Phase.ERROR
                await self._record(level="warning", event="area_disabled", message=self.diagnostic, result="not_started")
                return self.status()
            if (
                (not self._task or self._task.done())
                and self.mode is mode
                and self.phase in {Phase.IDLE, Phase.ACTIVE, Phase.UNCERTAIN}
            ):
                return self.status()
            if self._task and not self._task.done():
                if self.phase is Phase.STOPPING:
                    self._pending_mode = mode
                    self.requested_mode = mode
                    self.diagnostic = "Próxima cena aguardará a confirmação OFF em andamento"
                    await self._record(
                        event="transition_queued",
                        message=f"modo {mode.value} enfileirado durante STOPPING",
                        result="queued",
                    )
                    return self.status()
                if self.requested_mode is mode:
                    return self.status()
                self._task.cancel()
            self._generation += 1
            generation = self._generation
            self.requested_mode = mode
            self.last_transition_at = time.time()
            self._request_monotonic = time.monotonic()
            self._cancel_lights()
            self._task = asyncio.create_task(
                self._transition(mode, generation, reason),
                name=f"tecnohead-{self.profile.area_id}-{mode.value}",
            )
            return self.status()

    def _cancel_lights(self) -> None:
        if self._lights_task and not self._lights_task.done():
            self._lights_task.cancel()
        self._lights_task = None

    async def wait_idle(self) -> None:
        task = self._task
        if task:
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _transition(self, mode: Mode, generation: int, reason: str) -> None:
        self.phase = Phase.STOPPING if mode is Mode.OFF else Phase.STARTING
        self.diagnostic = f"Iniciando cena {mode.value} ({reason})"
        await self._record(event="transition_started", message=self.diagnostic, result="started")
        warnings: list[str] = []
        try:
            if mode is Mode.CINEMA:
                warnings.extend(await self._cinema(generation))
            elif mode is Mode.TV:
                warnings.extend(await self._tv(generation))
            else:
                warnings.extend(await self._off(generation))
            if warnings:
                self.diagnostic = "Concluído com degradações: " + "; ".join(warnings[:5])
                self.phase = Phase.ERROR
                await self._record(event="transition_degraded", message=self.diagnostic, result="degraded")
            else:
                self.mode = mode
                self.requested_mode = mode
                self.phase = Phase.ACTIVE if mode is not Mode.OFF else Phase.IDLE
                self.diagnostic = "Cena concluída; confirmação física de IR não é observável" if mode is not Mode.OFF else "Multimídia desligada; estado físico do projetor não é observável"
                await self._record(event="transition_completed", message=self.diagnostic, result="completed")
        except IRSequenceUncertain as exc:
            self.phase = Phase.UNCERTAIN
            self.diagnostic = str(exc)
            await self._record(level="error", event="transition_uncertain", message=self.diagnostic, result="uncertain")
        except (IRSequenceError, ActionError, asyncio.CancelledError) as exc:
            if isinstance(exc, asyncio.CancelledError):
                raise
            self.phase = Phase.ERROR
            self.diagnostic = str(exc)
            await self._record(level="error", event="transition_failed", message=self.diagnostic, result="failed")
        finally:
            if mode is not Mode.OFF and self.phase in {Phase.ACTIVE, Phase.ERROR}:
                self._schedule_lights(generation, self._request_monotonic)
            if self._pending_mode is not None and self._pending_mode is not mode:
                next_mode = self._pending_mode
                self._pending_mode = None
                self._generation += 1
                next_generation = self._generation
                self.requested_mode = next_mode
                self._task = asyncio.create_task(
                    self._transition(next_mode, next_generation, "queued_after_stopping"),
                    name=f"tecnohead-{self.profile.area_id}-{next_mode.value}",
                )

    async def _cinema(self, generation: int) -> list[str]:
        warnings: list[str] = []
        tv_state = await self.discovery.entity_state(self.profile.tv_entity_id)
        if self.profile.tv_entity_id and tv_state and tv_state.get("state") in {"on", "playing", "idle", "paused"}:
            self._mark_internal_tv("off")
            await self.actions.call(self.profile, self.profile.tv_entity_id, {"media_player"}, "media_player", "turn_off")
        elif self.profile.tv_entity_id and not tv_state:
            warnings.append("estado da TV indisponível")
        await self._screen(True)
        if not self.profile.ir:
            raise IRSequenceError("perfil IR do projetor não está configurado")
        await self.ir.send_on(self.profile)
        self.projector_intent = "on_commanded_unknown_physical"
        warnings.extend(await self.actions.apply_receiver(self.profile, self.profile.receiver_cinema_source, self.profile.volume_cinema))
        if self.profile.apple_tv_entity_id:
            await self.actions.call(self.profile, self.profile.apple_tv_entity_id, {"media_player"}, "media_player", "turn_on")
        warnings.extend(await self.actions.apply_climate(self.profile))
        self.diagnostic = "Cinema ativo; projetor recebeu ON, sem feedback físico"
        return warnings

    async def _tv(self, generation: int) -> list[str]:
        warnings: list[str] = []
        if self.mode is Mode.CINEMA or self.projector_intent.startswith("on_commanded"):
            if not self.profile.ir:
                raise IRSequenceError("não é seguro desligar o projetor sem perfil IR")
            await self.ir.send_off(self.profile)
            self.projector_intent = "off_commanded_unknown_physical"
        await self._screen(False)
        if self.profile.tv_entity_id:
            self._mark_internal_tv("on")
            await self.actions.call(self.profile, self.profile.tv_entity_id, {"media_player"}, "media_player", "turn_on")
        else:
            warnings.append("TV não configurada")
        warnings.extend(await self.actions.apply_receiver(self.profile, self.profile.receiver_tv_source, self.profile.volume_tv))
        warnings.extend(await self.actions.apply_climate(self.profile))
        return warnings

    async def _off(self, generation: int) -> list[str]:
        warnings: list[str] = []
        self._cancel_lights()
        if self.mode is Mode.CINEMA or self.projector_intent.startswith("on_commanded"):
            if not self.profile.ir:
                raise IRSequenceError("não é seguro desligar o projetor sem perfil IR")
            await self.ir.send_off(self.profile)
            self.projector_intent = "off_commanded_unknown_physical"
        await self._screen(False)
        if self.profile.tv_entity_id:
            self._mark_internal_tv("off")
            await self.actions.call(self.profile, self.profile.tv_entity_id, {"media_player"}, "media_player", "turn_off")
        if self.profile.receiver_entity_id:
            await self.actions.call(self.profile, self.profile.receiver_entity_id, {"media_player"}, "media_player", "turn_off")
        if self.profile.apple_tv_entity_id:
            await self.actions.call(self.profile, self.profile.apple_tv_entity_id, {"media_player"}, "media_player", "turn_off")
        return warnings

    async def _screen(self, open_screen: bool) -> None:
        entity_id = self.profile.screen_entity_id
        if not entity_id:
            raise ActionError("telão não configurado")
        domain = entity_id.split(".", 1)[0]
        if domain == "cover":
            service = "open_cover" if open_screen else "close_cover"
        else:
            service = "turn_on" if open_screen else "turn_off"
        await self.actions.call(self.profile, entity_id, {"switch", "cover"}, domain, service, required=True)

    def _schedule_lights(self, generation: int, requested_at: float | None = None) -> None:
        self._cancel_lights()
        requested_at = requested_at if requested_at is not None else time.monotonic()
        self.last_lights_schedule_at = time.time() - max(0.0, time.monotonic() - requested_at)
        self._lights_task = asyncio.create_task(
            self._lights_after_delay(generation, requested_at),
            name=f"tecnohead-lights-{self.profile.area_id}",
        )

    async def _lights_after_delay(self, generation: int, requested_at: float) -> None:
        try:
            remaining = self.profile.lights_delay_seconds - (time.monotonic() - requested_at)
            if remaining > 0:
                await asyncio.sleep(remaining)
            if generation != self._generation or self.requested_mode is Mode.OFF or self.mode is Mode.OFF:
                return
            failures = await self.actions.turn_off_lights(self.profile)
            self.last_lights_off_at = time.time()
            if failures:
                self.diagnostic = "Luzes parcialmente não desligadas: " + "; ".join(failures[:4])
                await self._record(level="warning", event="lights_degraded", message=self.diagnostic, result="degraded")
            else:
                await self._record(event="lights_turned_off", message="Luzes da área desligadas após o atraso configurado", result="completed")
        except asyncio.CancelledError:
            return
        except Exception as exc:
            await self._record(level="error", event="lights_failed", message=str(exc), result="failed")

    def _mark_internal_tv(self, expected: str) -> None:
        self._expected_tv_state = expected
        self._expected_tv_until = time.monotonic() + 8.0

    async def handle_state_event(self, event: dict[str, Any]) -> None:
        data = event.get("data", event)
        entity_id = data.get("entity_id")
        if entity_id != self.profile.tv_entity_id:
            return
        new_state = data.get("new_state") or {}
        old_state = data.get("old_state") or {}
        new_value = new_state.get("state")
        old_value = old_state.get("state")
        if new_value == old_value:
            return
        if self._expected_tv_state == new_value and time.monotonic() < self._expected_tv_until:
            self._expected_tv_state = None
            return
        if new_value in {"on", "playing", "idle", "paused"} and old_value not in {"on", "playing", "idle", "paused"}:
            if self.requested_mode is Mode.CINEMA or self.phase in {Phase.STARTING, Phase.ACTIVE} and self.mode is Mode.CINEMA:
                if self.profile.tv_protection_during_cinema and self.profile.tv_protection_action == "turn_off":
                    self._external_tv_task = asyncio.create_task(self._protect_tv(), name=f"protect-tv-{self.profile.area_id}")
                return
            self._external_tv_task = asyncio.create_task(
                self._handle_external_tv_on(),
                name=f"external-tv-on-{self.profile.area_id}",
            )
        elif new_value not in {"on", "playing", "idle", "paused"} and old_value in {"on", "playing", "idle", "paused"}:
            if self.requested_mode is not Mode.CINEMA and self.mode is not Mode.CINEMA:
                self._cancel_lights()
                self.requested_mode = Mode.OFF
                self.mode = Mode.OFF
                self.phase = Phase.IDLE
                await self._record(event="external_tv_off", message="TV desligada fisicamente; modo lógico OFF", result="completed")

    async def _protect_tv(self) -> None:
        try:
            self._mark_internal_tv("off")
            await self.actions.call(self.profile, self.profile.tv_entity_id, {"media_player"}, "media_player", "turn_off")
            await self._record(event="external_tv_protected", message="TV desligada durante Cinema; demais equipamentos preservados", result="completed")
        except Exception as exc:
            await self._record(level="error", event="external_tv_protection_failed", message=str(exc), result="failed")

    async def _handle_external_tv_on(self) -> None:
        try:
            self.requested_mode = Mode.TV
            self.mode = Mode.TV
            self.phase = Phase.STARTING
            self._request_monotonic = time.monotonic()
            self.diagnostic = "TV ligada fisicamente; aplicando somente receiver e ambiente"
            await self._record(event="external_tv_on", message=self.diagnostic, result="started")
            warnings = []
            warnings.extend(await self.actions.apply_receiver(self.profile, self.profile.receiver_tv_source, self.profile.volume_tv))
            warnings.extend(await self.actions.apply_climate(self.profile))
            self.phase = Phase.ERROR if warnings else Phase.ACTIVE
            self.diagnostic = "; ".join(warnings) if warnings else "TV física preservada, receiver em TV Audio"
            self._generation += 1
            self._schedule_lights(self._generation, self._request_monotonic)
            await self._record(event="external_tv_on_completed", message=self.diagnostic, result="completed" if not warnings else "degraded")
        except Exception as exc:
            self.phase = Phase.ERROR
            self.diagnostic = str(exc)
            await self._record(level="error", event="external_tv_on_failed", message=self.diagnostic, result="failed")

    async def handle_climate_state_event(self, event: dict[str, Any]) -> None:
        if self.requested_mode is Mode.OFF or self.phase not in {Phase.ACTIVE, Phase.ERROR}:
            return
        data = event.get("data", {})
        entity_id = data.get("entity_id")
        watched = {self.profile.climate_entity_id, self.profile.climate.temperature_sensor_entity_id}
        if entity_id not in watched:
            return
        old_state = data.get("old_state") or {}
        new_state = data.get("new_state") or {}
        old_temp = (old_state.get("attributes") or {}).get("current_temperature")
        new_temp = (new_state.get("attributes") or {}).get("current_temperature")
        if entity_id == self.profile.climate.temperature_sensor_entity_id:
            old_temp = old_state.get("state")
            new_temp = new_state.get("state")
        if old_temp == new_temp:
            return
        if self._climate_task and not self._climate_task.done():
            return
        self._climate_task = asyncio.create_task(self._reapply_climate(), name=f"climate-{self.profile.area_id}")

    async def _reapply_climate(self) -> None:
        try:
            warnings = await self.actions.apply_climate(self.profile)
            if warnings:
                await self._record(level="warning", event="climate_degraded", message="; ".join(warnings[:4]), result="degraded")
            else:
                await self._record(event="climate_rebalanced", message="Perfil de climatização reavaliado pela temperatura", result="completed")
        except Exception as exc:
            await self._record(level="error", event="climate_rebalance_failed", message=str(exc), result="failed")
