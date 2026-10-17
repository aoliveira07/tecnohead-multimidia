from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

try:  # websockets changed its import path in v14
    from websockets.asyncio.client import connect as websocket_connect
except ImportError:  # pragma: no cover - exercised only with older websockets
    from websockets import connect as websocket_connect

from app.settings import Settings

LOGGER = logging.getLogger("tecnohead.ha")


class HomeAssistantError(RuntimeError):
    """Base error for HA transport failures."""


class HomeAssistantUnavailable(HomeAssistantError):
    pass


class HomeAssistantServiceError(HomeAssistantError):
    pass


class HomeAssistantClient:
    """Official Core API proxy client; never talks to a device directly."""

    def __init__(self, settings: Settings, session: aiohttp.ClientSession | None = None):
        self.settings = settings
        self._session = session
        self._owns_session = session is None
        self._message_id = 0

    async def start(self) -> None:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.settings.ha_request_timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def stop(self) -> None:
        if self._session is not None and self._owns_session:
            await self._session.close()
        self._session = None if self._owns_session else self._session

    def _headers(self) -> dict[str, str]:
        if not self.settings.supervisor_token:
            raise HomeAssistantUnavailable("SUPERVISOR_TOKEN não está disponível no App")
        return {
            "Authorization": f"Bearer {self.settings.supervisor_token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        if self._session is None:
            await self.start()
        assert self._session is not None
        try:
            async with self._session.request(method, url, headers=self._headers(), **kwargs) as response:
                raw = await response.text()
        except (TimeoutError, aiohttp.ClientError) as exc:
            raise HomeAssistantUnavailable("Home Assistant indisponível") from exc
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        if response.status >= 400:
            detail = payload.get("message", payload) if isinstance(payload, dict) else payload
            raise HomeAssistantServiceError(f"Home Assistant respondeu HTTP {response.status}: {detail}")
        return payload

    async def get_states(self) -> list[dict[str, Any]]:
        payload = await self._request("GET", f"{self.settings.core_api_url}/states")
        return payload if isinstance(payload, list) else []

    async def get_state(self, entity_id: str) -> dict[str, Any] | None:
        try:
            payload = await self._request("GET", f"{self.settings.core_api_url}/states/{entity_id}")
        except HomeAssistantServiceError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise
        return payload if isinstance(payload, dict) else None

    async def get_config(self) -> dict[str, Any]:
        payload = await self._request("GET", f"{self.settings.core_api_url}/config")
        return payload if isinstance(payload, dict) else {}

    async def call_service(self, domain: str, service: str, *, entity_id: str, data: dict[str, Any] | None = None) -> Any:
        """Call one HA service exactly once.

        IR power calls deliberately do not retry and never use num_repeats. The
        body uses entity_id because that is the REST representation of the HA
        action target.
        """

        payload: dict[str, Any] = {"entity_id": entity_id}
        if data:
            payload.update(data)
        return await self._request(
            "POST",
            f"{self.settings.core_api_url}/services/{domain}/{service}",
            json=payload,
        )

    async def get_mqtt_service(self) -> dict[str, Any] | None:
        """Read the Supervisor-provided MQTT service without exposing credentials."""

        try:
            payload = await self._request("GET", f"{self.settings.supervisor_url}/services/mqtt")
        except HomeAssistantError:
            return None
        if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            payload = payload["data"]
        if isinstance(payload, dict) and payload.get("host") and payload.get("port"):
            return payload
        return None

    async def websocket_command(self, command: dict[str, Any]) -> Any:
        if not self.settings.supervisor_token:
            raise HomeAssistantUnavailable("SUPERVISOR_TOKEN não está disponível no App")
        try:
            async with websocket_connect(self.settings.core_ws_url, open_timeout=self.settings.ha_request_timeout) as ws:
                await ws.send(json.dumps({"type": "auth", "access_token": self.settings.supervisor_token}))
                auth = json.loads(await asyncio.wait_for(ws.recv(), timeout=self.settings.ha_request_timeout))
                if auth.get("type") != "auth_ok":
                    raise HomeAssistantUnavailable("autenticação WebSocket do Home Assistant falhou")
                self._message_id += 1
                request = {"id": self._message_id, **command}
                await ws.send(json.dumps(request))
                while True:
                    message = json.loads(await asyncio.wait_for(ws.recv(), timeout=self.settings.ha_request_timeout))
                    if message.get("id") == self._message_id:
                        if not message.get("success", False):
                            raise HomeAssistantServiceError(str(message.get("error", "comando WebSocket rejeitado")))
                        return message.get("result")
        except HomeAssistantError:
            raise
        except Exception as exc:
            raise HomeAssistantUnavailable("WebSocket do Home Assistant indisponível") from exc

    async def get_registry_snapshot(self) -> dict[str, Any]:
        areas = await self.websocket_command({"type": "config/area_registry/list"})
        entities = await self.websocket_command({"type": "config/entity_registry/list"})
        devices = await self.websocket_command({"type": "config/device_registry/list"})
        states = await self.get_states()
        return {
            "areas": areas if isinstance(areas, list) else [],
            "entities": entities if isinstance(entities, list) else [],
            "devices": devices if isinstance(devices, list) else [],
            "states": states,
        }

    async def state_event_stream(
        self,
        callback: Callable[[dict[str, Any]], Awaitable[None]],
        stop_event: asyncio.Event,
    ) -> None:
        """Subscribe to state_changed and reconnect without replaying commands."""

        delay = 1.0
        while not stop_event.is_set():
            try:
                await self._state_event_connection(callback, stop_event)
                delay = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOGGER.warning("stream de eventos HA indisponível: %s", exc)
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=delay)
                except TimeoutError:
                    pass
                delay = min(delay * 2, 60.0)

    async def _state_event_connection(
        self,
        callback: Callable[[dict[str, Any]], Awaitable[None]],
        stop_event: asyncio.Event,
    ) -> None:
        if not self.settings.supervisor_token:
            raise HomeAssistantUnavailable("SUPERVISOR_TOKEN não está disponível no App")
        async with websocket_connect(self.settings.core_ws_url, open_timeout=self.settings.ha_request_timeout) as ws:
            await ws.send(json.dumps({"type": "auth", "access_token": self.settings.supervisor_token}))
            auth = json.loads(await asyncio.wait_for(ws.recv(), timeout=self.settings.ha_request_timeout))
            if auth.get("type") != "auth_ok":
                raise HomeAssistantUnavailable("autenticação WebSocket do Home Assistant falhou")
            self._message_id += 1
            await ws.send(
                json.dumps(
                    {
                        "id": self._message_id,
                        "type": "subscribe_events",
                        "event_type": "state_changed",
                    }
                )
            )
            subscribed = json.loads(await asyncio.wait_for(ws.recv(), timeout=self.settings.ha_request_timeout))
            if not subscribed.get("success", False):
                raise HomeAssistantServiceError("assinatura de eventos rejeitada")
            while not stop_event.is_set():
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except TimeoutError:
                    continue
                payload = json.loads(message)
                if payload.get("type") == "event" and isinstance(payload.get("event"), dict):
                    await callback(payload["event"])
