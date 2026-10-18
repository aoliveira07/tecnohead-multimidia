from __future__ import annotations

import base64
import re
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Mode(str, Enum):
    OFF = "off"
    CINEMA = "cinema"
    TV = "tv"


class AudioGroupStrategy(str, Enum):
    NONE = "none"
    LINKPLAY = "linkplay"
    AIRPLAY2_APPLE = "airplay2_apple"


class AudioPriority(str, Enum):
    NORMAL = "normal"
    HDMI_ARC = "hdmi_arc"


class Phase(str, Enum):
    IDLE = "idle"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    ERROR = "error"
    UNCERTAIN = "uncertain"


class CommandFormat(str, Enum):
    BROADLINK_B64 = "broadlink_b64"
    PRONTO_HEX = "pronto_hex"
    NAMED_COMMAND = "named_command"


class IRCommand(BaseModel):
    """One command owned by this App, independent of the HA remote registry."""

    model_config = ConfigDict(extra="forbid")

    format: CommandFormat = CommandFormat.BROADLINK_B64
    value: str = Field(min_length=1)
    device: str | None = Field(default=None, max_length=128)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str, info: Any) -> str:
        value = value.strip()
        if value.startswith("b64:"):
            raise ValueError("o preset deve ser salvo sem o prefixo b64:")
        return value

    @model_validator(mode="after")
    def validate_format(self) -> IRCommand:
        if self.format is CommandFormat.BROADLINK_B64:
            try:
                decoded = base64.b64decode(self.value, validate=True)
            except Exception as exc:  # pragma: no cover - exact exception varies by Python
                raise ValueError("Base64 BroadLink inválido") from exc
            if not decoded:
                raise ValueError("o código Base64 não pode ser vazio")
        elif self.format is CommandFormat.PRONTO_HEX:
            compact = re.sub(r"\s+", " ", self.value).strip()
            tokens = compact.split(" ")
            if not tokens or any(not re.fullmatch(r"[0-9A-Fa-f]+", token) for token in tokens):
                raise ValueError("Pronto Hex inválido")
            if not tokens[0].lower() == "0000":
                raise ValueError("Pronto Hex deve começar com 0000")
        elif not self.value:
            raise ValueError("comando nomeado não pode ser vazio")
        return self

    def to_ha_command(self) -> str:
        if self.format is CommandFormat.BROADLINK_B64:
            return f"b64:{self.value}"
        return self.value


class IRProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remote_entity_id: str | None = None
    on: IRCommand
    off: IRCommand
    on_sends: int = Field(default=1, ge=1, le=5)
    off_sends: int = Field(default=2, ge=1, le=5)
    on_interval_seconds: float = Field(default=0.4, ge=0, le=30)
    off_interval_seconds: float = Field(default=5.0, ge=0, le=60)
    last_test_at: str | None = None
    last_test_result: str | None = None


class ClimateProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    setpoint_c: float = Field(default=22.0, ge=16.0, le=30.0)
    high_threshold_c: float = Field(default=23.0, ge=16.0, le=35.0)
    high_duration_seconds: float = Field(default=120.0, ge=0, le=1800)
    low_fan_mode: str | None = None
    high_fan_mode: str | None = None
    vane_mode: str | None = None
    temperature_sensor_entity_id: str | None = None
    minimum_fan_change_seconds: float = Field(default=120.0, ge=0, le=3600)


class AreaProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area_id: str = Field(min_length=1, max_length=128)
    enabled: bool = False
    tv_entity_id: str | None = None
    receiver_entity_id: str | None = None
    screen_entity_id: str | None = None
    apple_tv_entity_id: str | None = None
    climate_entity_id: str | None = None
    lighting_switch_entity_ids: list[str] = Field(default_factory=list)
    receiver_cinema_source: str | None = None
    receiver_tv_source: str | None = "TV Audio"
    # Home Assistant media_player.volume_set uses a 0.0-1.0 level. Keep a
    # conservative default and let a client calibrate it after listening.
    volume_cinema: float = Field(default=0.25, ge=0.0, le=1.0)
    volume_tv: float = Field(default=0.20, ge=0.0, le=1.0)
    lights_delay_seconds: float = Field(default=30.0, ge=0.0, le=3600.0)
    tv_protection_during_cinema: bool = True
    tv_protection_action: str = "turn_off"
    default_mode: Mode = Mode.TV
    climate: ClimateProfile = Field(default_factory=ClimateProfile)
    ir: IRProfile | None = None


class AirPlayEndpointProfile(BaseModel):
    """Persisted identity only; a stream is never resumed after a restart."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    service_name: str | None = None
    stable_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    listen_port: int | None = Field(default=None, ge=1024, le=65535)
    output_backend: str = "pcm_bridge"
    pairing_state: str = "not_configured"


class AudioZoneProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zone_id: str = Field(min_length=1, max_length=64)
    area_id: str | None = None
    enabled: bool = False
    media_player_entity_id: str | None = None
    max_volume_percent: int = Field(default=30, ge=0, le=100)
    allow_absolute_volume: bool = False
    priority: AudioPriority = AudioPriority.NORMAL
    # Kept for backwards-compatible config files. ARC is observed and left to
    # the physical amplifier; it no longer gates an explicit AirPlay request.
    airplay_may_override_arc: bool = True
    airplay: AirPlayEndpointProfile = Field(default_factory=AirPlayEndpointProfile)


class MultiroomConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    zones: list[AudioZoneProfile] = Field(default_factory=list)
    group_strategy: AudioGroupStrategy = AudioGroupStrategy.NONE
    group_master_zone_id: str | None = None
    members: list[str] = Field(default_factory=list)
    share_pool_tv_to_kitchen: bool = False


class AudioZoneUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zone_id: str = Field(min_length=1, max_length=64)
    area_id: str | None = None
    enabled: bool = False
    media_player_entity_id: str | None = None
    max_volume_percent: int = Field(default=30, ge=0, le=100)
    allow_absolute_volume: bool = False
    priority: AudioPriority = AudioPriority.NORMAL
    # Legacy field retained so v1.4.x configs can be saved without a reset.
    # The audio engine no longer blocks AirPlay based on this value.
    airplay_may_override_arc: bool = True
    airplay: AirPlayEndpointProfile = Field(default_factory=AirPlayEndpointProfile)


class MultiroomUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    zones: list[AudioZoneUpdate] = Field(default_factory=list)
    group_strategy: AudioGroupStrategy = AudioGroupStrategy.NONE
    group_master_zone_id: str | None = None
    members: list[str] = Field(default_factory=list)
    share_pool_tv_to_kitchen: bool = False


class AudioCommandRequest(BaseModel):
    confirmed: bool = False


class AudioVolumeRequest(BaseModel):
    volume_percent: int = Field(ge=0, le=100)
    confirmed: bool = False


class AudioMuteRequest(BaseModel):
    is_volume_muted: bool
    confirmed: bool = False


class AudioSourceRequest(BaseModel):
    source: str = Field(min_length=1, max_length=128)
    confirmed: bool = False


class AudioPlaybackRequest(BaseModel):
    action: str = Field(pattern="^(play|pause|stop)$")
    confirmed: bool = False


class AudioGroupRequest(BaseModel):
    master_zone_id: str = Field(min_length=1, max_length=64)
    member_zone_ids: list[str] = Field(min_length=1, max_length=8)
    confirmed: bool = False


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 3
    installation_id: str | None = None
    areas: list[AreaProfile] = Field(default_factory=list)
    audio: MultiroomConfig = Field(default_factory=MultiroomConfig)


class ModeRequest(BaseModel):
    mode: Mode
    confirmed: bool = False


class IRTestRequest(BaseModel):
    direction: str = Field(pattern="^(on|off)$")
    confirmed: bool = False


class AreaProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    tv_entity_id: str | None = None
    receiver_entity_id: str | None = None
    screen_entity_id: str | None = None
    apple_tv_entity_id: str | None = None
    climate_entity_id: str | None = None
    lighting_switch_entity_ids: list[str] = Field(default_factory=list)
    receiver_cinema_source: str | None = None
    receiver_tv_source: str | None = "TV Audio"
    volume_cinema: float = Field(default=0.25, ge=0.0, le=1.0)
    volume_tv: float = Field(default=0.20, ge=0.0, le=1.0)
    lights_delay_seconds: float = Field(default=30.0, ge=0.0, le=3600.0)
    tv_protection_during_cinema: bool = True
    tv_protection_action: str = "turn_off"
    default_mode: Mode = Mode.TV
    climate: ClimateProfile = Field(default_factory=ClimateProfile)
    ir: IRProfile | None = None


class RestorePresetRequest(BaseModel):
    confirmed: bool = False


class EntityDescriptor(BaseModel):
    entity_id: str
    domain: str
    state: str
    friendly_name: str | None = None
    area_id: str | None = None
    device_id: str | None = None
    integration: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    roles: list[str] = Field(default_factory=list)


class AreaDescriptor(BaseModel):
    area_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    entities: list[EntityDescriptor] = Field(default_factory=list)
    profile: AreaProfile | None = None


class DiagnosticEvent(BaseModel):
    timestamp: str
    area_id: str | None = None
    level: str = "info"
    event: str
    message: str
    entity_id: str | None = None
    command_kind: str | None = None
    result: str | None = None
    physical_confirmation: str = "not_observable"


def default_app_config() -> AppConfig:
    return AppConfig()
