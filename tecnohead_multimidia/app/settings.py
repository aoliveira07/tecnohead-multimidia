from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


def _load_supervisor_token() -> str | None:
    """Read the Supervisor token from the normal env or S6 container env.

    S6 normally imports this value through ``with-contenv``. The fallback is
    limited to the two standard S6 environment directories so local runs
    remain unauthenticated rather than guessing credentials. The token is
    never logged or persisted by the application.
    """

    token = os.getenv("SUPERVISOR_TOKEN")
    if token:
        return token
    for path in (
        Path("/var/run/s6/container_environment/SUPERVISOR_TOKEN"),
        Path("/run/s6/container_environment/SUPERVISOR_TOKEN"),
    ):
        try:
            token = path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            continue
        if token:
            return token
    return None


def _load_mediaremote_probe_option(data_dir: Path) -> bool:
    """Read the HAOS-validated opt-in without exposing other app options."""

    env_value = os.getenv("APPLE_MEDIAREMOTE_EXPERIMENTAL")
    if env_value is not None:
        return env_value.strip().lower() in {"1", "true", "yes"}
    try:
        options = json.loads((data_dir / "options.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return False
    return isinstance(options, dict) and options.get("apple_mediaremote_experimental") is True


@dataclass(frozen=True)
class Settings:
    app_version: str = "1.4.16"
    app_host: str = "0.0.0.0"
    app_port: int = 18199
    data_dir: Path = Path("/data")
    supervisor_url: str = "http://supervisor"
    core_api_url: str = "http://supervisor/core/api"
    core_ws_url: str = "ws://supervisor/core/websocket"
    supervisor_token: str | None = None
    mqtt_discovery_prefix: str = "homeassistant"
    mqtt_topic_prefix: str = "tecnohead"
    ha_request_timeout: float = 12.0
    apple_mediaremote_experimental: bool = False


def load_settings() -> Settings:
    data_dir = Path(os.getenv("APP_DATA_DIR", "/data"))
    return Settings(
        app_version=os.getenv("APP_VERSION", "1.4.17-rc.2"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("INGRESS_PORT", os.getenv("APP_PORT", "18199"))),
        data_dir=data_dir,
        supervisor_url=os.getenv("SUPERVISOR_URL", "http://supervisor"),
        core_api_url=os.getenv("HA_CORE_API_URL", "http://supervisor/core/api").rstrip("/"),
        core_ws_url=os.getenv("HA_CORE_WS_URL", "ws://supervisor/core/websocket"),
        supervisor_token=_load_supervisor_token(),
        mqtt_discovery_prefix=os.getenv("MQTT_DISCOVERY_PREFIX", "homeassistant").strip("/"),
        mqtt_topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "tecnohead").strip("/"),
        ha_request_timeout=float(os.getenv("HA_REQUEST_TIMEOUT", "12")),
        apple_mediaremote_experimental=_load_mediaremote_probe_option(data_dir),
    )
