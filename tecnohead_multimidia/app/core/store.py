from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path

from app.models import AppConfig, AreaProfile, IRProfile, MultiroomConfig, default_app_config

LOGGER = logging.getLogger("tecnohead.store")


class ConfigStore:
    """Atomic, private, app-owned configuration persisted under the HA App data map."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.path = data_dir / "config.json"
        self._lock = asyncio.Lock()
        self._config = default_app_config()

    async def load(self) -> AppConfig:
        async with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self._config = default_app_config()
                self._config.installation_id = uuid.uuid4().hex
                await self._write_locked()
                return self._config.model_copy(deep=True)
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._config = self._migrate(raw)
            except (OSError, ValueError, TypeError) as exc:
                LOGGER.error("config could not be loaded; using a safe empty config: %s", exc)
                self._config = default_app_config()
                self._config.installation_id = uuid.uuid4().hex
                await self._write_locked()
            return self._config.model_copy(deep=True)

    @staticmethod
    def _migrate(raw: object) -> AppConfig:
        if not isinstance(raw, dict):
            raise ValueError("configuration root must be an object")
        data = dict(raw)
        source_version = int(data.get("schema_version", 1) or 1)
        data.setdefault("installation_id", uuid.uuid4().hex)
        data.setdefault("areas", [])
        # v0/v1/v2 already used the same area shape. The v1.3 migration only
        # adds an empty, app-owned audio section; no HA registry data is moved.
        if source_version < 3:
            data.setdefault("audio", MultiroomConfig().model_dump(mode="json"))
        data["schema_version"] = 3
        return AppConfig.model_validate(data)

    async def _write_locked(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._config.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
        fd, temp_name = tempfile.mkstemp(prefix="config.", suffix=".tmp", dir=self.data_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    async def snapshot(self) -> AppConfig:
        async with self._lock:
            return self._config.model_copy(deep=True)

    async def save(self, config: AppConfig) -> AppConfig:
        async with self._lock:
            config.installation_id = config.installation_id or self._config.installation_id or uuid.uuid4().hex
            config.schema_version = 3
            self._config = config.model_copy(deep=True)
            await self._write_locked()
            return self._config.model_copy(deep=True)

    async def get_area(self, area_id: str) -> AreaProfile | None:
        config = await self.snapshot()
        return next((area for area in config.areas if area.area_id == area_id), None)

    async def upsert_area(self, profile: AreaProfile) -> AreaProfile:
        async with self._lock:
            for index, current in enumerate(self._config.areas):
                if current.area_id == profile.area_id:
                    self._config.areas[index] = profile.model_copy(deep=True)
                    break
            else:
                self._config.areas.append(profile.model_copy(deep=True))
            await self._write_locked()
            return profile.model_copy(deep=True)

    async def update_ir(self, area_id: str, profile: IRProfile) -> AreaProfile:
        async with self._lock:
            for index, current in enumerate(self._config.areas):
                if current.area_id == area_id:
                    current.ir = profile.model_copy(deep=True)
                    self._config.areas[index] = current
                    await self._write_locked()
                    return current.model_copy(deep=True)
        raise KeyError(area_id)

    async def update_audio(self, audio: MultiroomConfig) -> MultiroomConfig:
        async with self._lock:
            self._config.audio = audio.model_copy(deep=True)
            self._config.schema_version = 3
            await self._write_locked()
            return self._config.audio.model_copy(deep=True)
