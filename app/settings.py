from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_version: str = "1.2.1"
    app_host: str = "0.0.0.0"
    app_port: int = 8099
    data_dir: Path = Path("/data")
    supervisor_url: str = "http://supervisor"
    core_api_url: str = "http://supervisor/core/api"
    core_ws_url: str = "ws://supervisor/core/websocket"
    supervisor_token: str | None = None
    mqtt_discovery_prefix: str = "homeassistant"
    mqtt_topic_prefix: str = "tecnohead"
    ha_request_timeout: float = 12.0


def load_settings() -> Settings:
    return Settings(
        app_version=os.getenv("APP_VERSION", "1.2.1"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("INGRESS_PORT", os.getenv("APP_PORT", "8099"))),
        data_dir=Path(os.getenv("APP_DATA_DIR", "/data")),
        supervisor_url=os.getenv("SUPERVISOR_URL", "http://supervisor"),
        core_api_url=os.getenv("HA_CORE_API_URL", "http://supervisor/core/api").rstrip("/"),
        core_ws_url=os.getenv("HA_CORE_WS_URL", "ws://supervisor/core/websocket"),
        supervisor_token=os.getenv("SUPERVISOR_TOKEN"),
        mqtt_discovery_prefix=os.getenv("MQTT_DISCOVERY_PREFIX", "homeassistant").strip("/"),
        mqtt_topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "tecnohead").strip("/"),
        ha_request_timeout=float(os.getenv("HA_REQUEST_TIMEOUT", "12")),
    )
