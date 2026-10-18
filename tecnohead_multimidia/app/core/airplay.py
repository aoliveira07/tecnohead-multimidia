from __future__ import annotations

import asyncio
import base64
import binascii
import contextlib
import json
import logging
import os
import re
import secrets
import socket
import time
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.audio import AudioActionError
from app.core.ha_client import HomeAssistantError
from app.models import AudioZoneProfile, MultiroomConfig

LOGGER = logging.getLogger("tecnohead.airplay")

DEFAULT_RAOP_PORTS = {"kitchen": 7000, "pool": 7001}
PCM_RATE = 48000
PCM_CHANNELS = 2
PCM_SAMPLE_FORMAT = "s32le"
STREAM_IDLE_SECONDS = 8.0
MDNS_PROBE_TIMEOUT = 3.0
METADATA_STREAM_LIMIT = 4 * 1024 * 1024
VOLUME_HOOK_PATH = "/usr/local/bin/tecnohead-airplay-volume-hook"
IPV4_RE = re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")

EventRecorder = Callable[..., Awaitable[None]]
_METADATA_HEADER_RE = re.compile(
    rb"<item><type>(?P<type>[0-9a-fA-F]{8})</type>"
    rb"<code>(?P<code>[0-9a-fA-F]{8})</code>"
    rb"<length>(?P<length>\d+)</length>"
)


def _metadata_fourcc(value: bytes) -> str | None:
    try:
        decoded = bytes.fromhex(value.decode("ascii"))
        return decoded.decode("ascii") if len(decoded) == 4 else None
    except (UnicodeDecodeError, ValueError):
        return None


def airplay_volume_to_percent(value: str | bytes) -> int | None:
    """Convert Shairport's AirPlay dB value to the linear iOS slider.

    Shairport reports the source volume as 0 dB (100%) down to -30 dB (0%),
    with -144 dB reserved for mute. The PCM path is kept at full gain and
    this value is forwarded to the physical LinkPlay media_player instead.
    """

    if isinstance(value, bytes):
        value = value.decode("ascii", errors="ignore")
    try:
        db = float(value.strip())
    except (TypeError, ValueError):
        return None
    if db <= -143.0:
        return 0
    percent = round(((db + 30.0) / 30.0) * 100.0)
    return max(0, min(100, percent))


def _redact_process_line(line: str) -> str:
    """Keep diagnostics useful without copying client network addresses."""

    return IPV4_RE.sub("[redacted-ip]", line.strip())[:500]


def _quote_config(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _resolve_lan_address() -> str | None:
    """Resolve the host-network address without sending application data."""

    override = os.getenv("AIRPLAY_STREAM_HOST", "").strip()
    if override:
        return override
    candidates = ("8.8.8.8", "10.255.255.255")
    for target in candidates:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect((target, 9))
            address = sock.getsockname()[0]
            if address and not address.startswith("127."):
                return address
        except OSError:
            continue
        finally:
            sock.close()
    return None


class AudioStreamBroker:
    """Small fan-out buffer for the live MP3 stream consumed by LinkPlay."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[bytes | None]] = set()
        self._recent: deque[bytes] = deque(maxlen=32)
        self.bytes_sent = 0
        self.client_count = 0
        self.last_chunk_at: float | None = None

    async def publish(self, chunk: bytes) -> None:
        if not chunk:
            return
        self._recent.append(chunk)
        self.bytes_sent += len(chunk)
        self.last_chunk_at = time.monotonic()
        for queue in tuple(self._subscribers):
            if queue.full():
                with contextlib.suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(chunk)

    async def subscribe(self) -> AsyncIterator[bytes]:
        queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=32)
        for chunk in self._recent:
            queue.put_nowait(chunk)
        self._subscribers.add(queue)
        self.client_count = len(self._subscribers)
        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    return
                yield chunk
        finally:
            self._subscribers.discard(queue)
            self.client_count = len(self._subscribers)

    def reset(self) -> None:
        self._recent.clear()
        self.bytes_sent = 0
        self.last_chunk_at = None

    async def close(self) -> None:
        for queue in tuple(self._subscribers):
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(None)
        self._subscribers.clear()
        self.client_count = 0


@dataclass
class _Endpoint:
    zone: AudioZoneProfile
    port: int
    token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    broker: AudioStreamBroker = field(default_factory=AudioStreamBroker)
    process: asyncio.subprocess.Process | None = None
    ffmpeg: asyncio.subprocess.Process | None = None
    metadata_reader: asyncio.subprocess.Process | None = None
    metadata_pipe_path: Path | None = None
    volume_socket: socket.socket | None = None
    volume_socket_path: Path | None = None
    pcm_task: asyncio.Task[None] | None = None
    mp3_task: asyncio.Task[None] | None = None
    metadata_task: asyncio.Task[None] | None = None
    volume_task: asyncio.Task[None] | None = None
    process_log_task: asyncio.Task[None] | None = None
    ffmpeg_log_task: asyncio.Task[None] | None = None
    idle_task: asyncio.Task[None] | None = None
    activation_task: asyncio.Task[None] | None = None
    state: str = "starting"
    diagnostic: str = "inicializando"
    last_pcm_at: float | None = None
    last_mp3_at: float | None = None
    session_started_at: float | None = None
    output_started: bool = False
    linkplay_started: bool = False
    last_error: str | None = None
    last_airplay_volume_percent: int | None = None
    last_airplay_volume_at: float | None = None
    last_airplay_volume_source: str | None = None
    process_log_tail: deque[str] = field(default_factory=lambda: deque(maxlen=24))


class AirPlayEndpointManager:
    """Owns AirPlay 2 receiver processes and bridges PCM to a LinkPlay URL.

    Shairport Sync and NQPTP are the only AirPlay transport components. The
    physical amplifier is still controlled through Home Assistant's
    ``media_player`` service API; this manager never opens a proprietary
    LinkPlay socket.
    """

    def __init__(
        self,
        settings: Any,
        ha: Any,
        audio: Any,
        event_recorder: EventRecorder,
    ) -> None:
        self.settings = settings
        self.ha = ha
        self.audio = audio
        self.event_recorder = event_recorder
        self._config = MultiroomConfig()
        self._endpoints: dict[str, _Endpoint] = {}
        self._nqptp: asyncio.subprocess.Process | None = None
        self._nqptp_log_task: asyncio.Task[None] | None = None
        self._dbus_process: asyncio.subprocess.Process | None = None
        self._avahi_process: asyncio.subprocess.Process | None = None
        self._mdns_log_tasks: list[asyncio.Task[None]] = []
        self._mdns_log_tail: deque[str] = deque(maxlen=24)
        self._mdns_mode = "not_started"
        self._mdns_diagnostic = "mDNS ainda não verificado"
        self._mdns_env: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._dependency_error: str | None = None
        self._shairport_version = "not_started"
        self._nqptp_version = "not_started"
        self._ffmpeg_version = "not_started"
        self._lan_address = _resolve_lan_address()

    @property
    def stream_port(self) -> int:
        # The Ingress server itself serves the protected stream route. With
        # host_network enabled this is reachable by a LinkPlay device on the
        # LAN without opening a second unauthenticated web server.
        return int(self.settings.app_port)

    def _stream_url(self, endpoint: _Endpoint) -> str | None:
        if not self._lan_address:
            return None
        return f"http://{self._lan_address}:{self.stream_port}/api/audio/airplay/{endpoint.zone.zone_id}/stream?token={endpoint.token}"

    async def start(self, config: MultiroomConfig) -> None:
        await self.apply_config(config)

    async def apply_config(self, config: MultiroomConfig) -> None:
        async with self._lock:
            self._config = config.model_copy(deep=True)
            wanted = {
                zone.zone_id: zone
                for zone in config.zones
                if zone.enabled and zone.airplay.enabled and zone.area_id and zone.media_player_entity_id
            }
            if wanted and not await self._ensure_dependencies():
                for endpoint in self._endpoints.values():
                    endpoint.state = "blocked"
                    endpoint.diagnostic = self._dependency_error or "dependências AirPlay não disponíveis"
                return
            if wanted:
                try:
                    await self._ensure_nqptp()
                except (OSError, RuntimeError, TimeoutError) as exc:
                    self._dependency_error = str(exc)
                    await self.event_recorder(
                        event="airplay_nqptp_unavailable",
                        level="error",
                        message=self._dependency_error,
                        result="blocked",
                    )
                    for endpoint in self._endpoints.values():
                        endpoint.state = "blocked"
                        endpoint.diagnostic = self._dependency_error
                    return
                try:
                    await self._ensure_mdns()
                except (OSError, RuntimeError, TimeoutError) as exc:
                    self._dependency_error = str(exc)
                    await self.event_recorder(
                        event="airplay_mdns_unavailable",
                        level="error",
                        message=self._dependency_error,
                        result="blocked",
                    )
                    for endpoint in self._endpoints.values():
                        endpoint.state = "blocked"
                        endpoint.diagnostic = self._dependency_error
                    return
            for zone_id in list(self._endpoints):
                current = self._endpoints[zone_id]
                desired = wanted.get(zone_id)
                if desired is None or self._endpoint_changed(current.zone, desired):
                    await self._stop_endpoint(zone_id)
            occupied: set[int] = set()
            for endpoint in self._endpoints.values():
                occupied.add(endpoint.port)
            for zone_id, zone in wanted.items():
                if zone_id in self._endpoints:
                    self._endpoints[zone_id].zone = zone
                    continue
                port = self._select_port(zone, occupied)
                occupied.add(port)
                await self._start_endpoint(zone, port)

    @staticmethod
    def _endpoint_changed(old: AudioZoneProfile, new: AudioZoneProfile) -> bool:
        return (
            old.area_id != new.area_id
            or old.media_player_entity_id != new.media_player_entity_id
            or old.airplay.service_name != new.airplay.service_name
            or old.airplay.stable_id != new.airplay.stable_id
            or old.airplay.listen_port != new.airplay.listen_port
        )

    @staticmethod
    def _port_available(port: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False
        finally:
            sock.close()

    def _select_port(self, zone: AudioZoneProfile, occupied: set[int]) -> int:
        preferred = zone.airplay.listen_port or DEFAULT_RAOP_PORTS.get(zone.zone_id, 7000)
        for port in range(preferred, preferred + 100):
            if port not in occupied and self._port_available(port):
                return port
        raise RuntimeError(f"não foi encontrada porta AirPlay livre para a zona {zone.zone_id}")

    async def _run_version(self, executable: str, *args: str) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                executable,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"executável ausente: {executable}") from exc
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10)
        text = (stdout or b"").decode("utf-8", errors="replace").strip()
        if process.returncode not in (0, None):
            raise RuntimeError(f"{executable} retornou código {process.returncode}")
        return _redact_process_line(text.splitlines()[0] if text else "versão não informada")

    async def _ensure_dependencies(self) -> bool:
        if self._dependency_error is not None:
            return False
        try:
            self._shairport_version = await self._run_version("shairport-sync", "-V")
            self._nqptp_version = await self._run_version("nqptp", "-V")
            self._ffmpeg_version = await self._run_version("ffmpeg", "-version")
            version_text = self._shairport_version.casefold().replace(" ", "")
            if "airplay2" not in version_text and "airplay-2" not in version_text:
                raise RuntimeError("Shairport Sync foi compilado sem suporte AirPlay 2")
            if not Path("/run/dbus/system_bus_socket").exists():
                raise RuntimeError("barramento D-Bus do host não está disponível para o mDNS/Avahi")
        except (OSError, RuntimeError, TimeoutError) as exc:
            self._dependency_error = str(exc)
            await self.event_recorder(
                event="airplay_dependencies_unavailable",
                level="error",
                message=self._dependency_error,
                result="blocked",
            )
            return False
        return True

    async def _ensure_nqptp(self) -> None:
        if self._nqptp and self._nqptp.returncode is None:
            return
        if self._nqptp:
            with contextlib.suppress(ProcessLookupError):
                self._nqptp.terminate()
        self._nqptp = await asyncio.create_subprocess_exec(
            "nqptp",
            "-v",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        self._nqptp_log_task = asyncio.create_task(self._consume_nqptp_log(), name="tecnohead-nqptp-log")
        await asyncio.sleep(0.25)
        if self._nqptp.returncode is not None:
            raise RuntimeError("NQPTP não conseguiu reservar UDP 319/320")
        await self.event_recorder(
            event="airplay_nqptp_started",
            message="NQPTP compartilhado iniciado para os receptores AirPlay 2",
            command_kind="nqptp",
            result="started",
        )

    async def _probe_host_avahi(self) -> str:
        """Return host, private, or blocked without starting another mDNS stack."""

        bus_socket = Path("/run/dbus/system_bus_socket")
        if not bus_socket.exists():
            return "private"
        try:
            process = await asyncio.create_subprocess_exec(
                "dbus-send",
                "--system",
                "--print-reply",
                "--dest=org.freedesktop.Avahi",
                "/",
                "org.freedesktop.Avahi.Server.GetVersionString",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            output, _ = await asyncio.wait_for(process.communicate(), timeout=MDNS_PROBE_TIMEOUT)
        except (OSError, asyncio.TimeoutError) as exc:
            self._mdns_diagnostic = f"não foi possível consultar o Avahi do host: {_redact_process_line(str(exc))}"
            return "blocked"
        text = _redact_process_line((output or b"").decode("utf-8", errors="replace"))
        if process.returncode == 0:
            self._mdns_diagnostic = "Avahi do host acessível pelo D-Bus"
            return "host"
        lowered = text.casefold()
        if any(marker in lowered for marker in ("serviceunknown", "namehasnoowner", "failed to connect", "could not connect")):
            self._mdns_diagnostic = "Avahi não está publicado no D-Bus do host; usando responder compartilhado interno"
            return "private"
        self._mdns_diagnostic = f"Avahi do host existe, mas o App não obteve acesso: {text or 'erro não informado'}"
        return "blocked"

    @staticmethod
    def _private_avahi_config() -> str:
        return '''[server]
host-name=tecnohead-multimedia
domain-name=local
use-ipv4=yes
use-ipv6=no
enable-dbus=yes
allow-point-to-point=no

[publish]
disable-publishing=no
disable-user-service-publishing=no
publish-addresses=yes
publish-hinfo=no
publish-workstation=no
publish-domain=no
publish-aaaa-on-ipv4=no
'''

    @staticmethod
    def _private_dbus_config(socket_path: Path) -> str:
        return f'''<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
  "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <type>system</type>
  <listen>unix:path={socket_path}</listen>
  <policy context="default">
    <allow user="root"/>
    <allow own="org.freedesktop.Avahi"/>
    <allow own="org.gnome.ShairportSync"/>
    <allow own_prefix="org.mpris.MediaPlayer2.ShairportSync"/>
  <!-- This bus is private to the App. Allow the normal request/reply and
       signal traffic used by Avahi and Shairport Sync; restricting replies
       here makes Avahi silently reject its own D-Bus method returns. -->
  <allow send_destination="*"/>
  <allow receive_sender="*"/>
  <allow receive_type="method_call"/>
  <allow receive_type="method_return"/>
  <allow receive_type="error"/>
  <allow receive_type="signal"/>
  </policy>
</busconfig>
'''

    async def _wait_for_path(self, path: Path, process: asyncio.subprocess.Process) -> None:
        for _ in range(30):
            if process.returncode is not None:
                details = "; ".join(self._mdns_log_tail)
                raise RuntimeError(f"D-Bus interno encerrou durante a inicialização: {details or process.returncode}")
            if path.exists():
                return
            await asyncio.sleep(0.1)
        raise RuntimeError("D-Bus interno não criou o socket do responder mDNS")

    async def _start_private_mdns(self) -> None:
        directory = self.settings.data_dir / "airplay" / "mdns"
        directory.mkdir(parents=True, exist_ok=True)
        socket_path = directory / "system_bus_socket"
        with contextlib.suppress(FileNotFoundError):
            socket_path.unlink()
        dbus_config = directory / "dbus.conf"
        dbus_config.write_text(self._private_dbus_config(socket_path), encoding="utf-8")
        avahi_config = directory / "avahi-daemon.conf"
        avahi_config.write_text(self._private_avahi_config(), encoding="utf-8")

        self._dbus_process = await asyncio.create_subprocess_exec(
            "dbus-daemon",
            f"--config-file={dbus_config}",
            "--nofork",
            "--nopidfile",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        self._mdns_log_tasks.append(asyncio.create_task(self._consume_mdns_log(self._dbus_process, "dbus")))
        private_env = {"DBUS_SYSTEM_BUS_ADDRESS": f"unix:path={socket_path}"}
        try:
            await self._wait_for_path(socket_path, self._dbus_process)
            self._avahi_process = await asyncio.create_subprocess_exec(
                "avahi-daemon",
                "--no-chroot",
                "--no-drop-root",
                "--no-rlimits",
                "--debug",
                f"--file={avahi_config}",
                env={**os.environ, **private_env},
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            self._mdns_log_tasks.append(asyncio.create_task(self._consume_mdns_log(self._avahi_process, "avahi")))
            await asyncio.sleep(0.5)
            if self._avahi_process.returncode is not None:
                details = "; ".join(self._mdns_log_tail)
                raise RuntimeError(f"Avahi interno encerrou durante a inicialização: {details or self._avahi_process.returncode}")
        except Exception:
            await self._terminate_process(self._avahi_process)
            await self._terminate_process(self._dbus_process)
            self._avahi_process = None
            self._dbus_process = None
            self._mdns_env = {}
            raise
        self._mdns_env = private_env
        self._mdns_mode = "private_avahi"
        self._mdns_diagnostic = "responder D-Bus/Avahi compartilhado iniciado dentro do App"

    async def _ensure_mdns(self) -> None:
        if self._mdns_mode == "host_avahi":
            return
        if self._mdns_mode == "private_avahi" and self._avahi_process and self._avahi_process.returncode is None:
            return
        mode = await self._probe_host_avahi()
        if mode == "host":
            self._mdns_mode = "host_avahi"
            self._mdns_env = {}
            return
        if mode == "blocked":
            raise RuntimeError(self._mdns_diagnostic)
        await self._start_private_mdns()

    async def _start_endpoint(self, zone: AudioZoneProfile, port: int) -> None:
        endpoint = _Endpoint(zone=zone, port=port)
        endpoint.state = "starting"
        endpoint.diagnostic = "iniciando receptor AirPlay 2"
        directory = self.settings.data_dir / "airplay"
        directory.mkdir(parents=True, exist_ok=True)
        config_path = directory / f"{zone.zone_id}.conf"
        endpoint.metadata_pipe_path = self._metadata_pipe_path(zone)
        endpoint.volume_socket_path = self._volume_socket_path(zone)
        try:
            self._prepare_metadata_pipe(endpoint.metadata_pipe_path)
            endpoint.volume_socket = self._prepare_volume_socket(endpoint.volume_socket_path)
        except OSError as exc:
            endpoint.state = "blocked"
            endpoint.last_error = _redact_process_line(str(exc))
            endpoint.diagnostic = f"não foi possível preparar a ponte de volume AirPlay: {endpoint.last_error}"
            await self.event_recorder(
                event="airplay_volume_bridge_failed",
                area_id=zone.area_id,
                entity_id=zone.media_player_entity_id,
                message=endpoint.diagnostic,
                level="error",
                result="blocked",
            )
            self._remove_metadata_pipe(endpoint.metadata_pipe_path)
            self._close_volume_socket(endpoint.volume_socket, endpoint.volume_socket_path)
            endpoint.volume_socket = None
            return
        config_path.write_text(
            self._config_text(zone, port, endpoint.metadata_pipe_path, endpoint.volume_socket_path),
            encoding="utf-8",
        )
        try:
            # Keep a reader open before Shairport Sync starts. This prevents
            # the metadata FIFO from blocking its first pvol message while
            # still keeping one isolated pipe per AirPlay identity.
            endpoint.metadata_reader = await asyncio.create_subprocess_exec(
                "cat",
                str(endpoint.metadata_pipe_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                # Shairport can emit a large metadata item (for example a
                # plist or artwork) before the next pvol update. The default
                # asyncio StreamReader limit is 64 KiB; when that item has no
                # separator within the limit, the metadata task dies and all
                # later AirPlay volume changes are lost. Keep the FIFO local
                # and bounded while allowing the largest normal item through.
                limit=METADATA_STREAM_LIMIT,
            )
            endpoint.ffmpeg = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "warning",
                "-f",
                PCM_SAMPLE_FORMAT,
                "-ar",
                str(PCM_RATE),
                "-ac",
                str(PCM_CHANNELS),
                "-i",
                "pipe:0",
                "-f",
                "mp3",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                "-ar",
                str(PCM_RATE),
                "-ac",
                str(PCM_CHANNELS),
                "-flush_packets",
                "1",
                "pipe:1",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            endpoint.process = await asyncio.create_subprocess_exec(
                "shairport-sync",
                "-c",
                str(config_path),
                env={**os.environ, **self._mdns_env},
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except (OSError, ValueError) as exc:
            endpoint.state = "blocked"
            endpoint.last_error = str(exc)
            endpoint.diagnostic = f"não foi possível iniciar processo AirPlay: {exc}"
            await self.event_recorder(
                event="airplay_endpoint_failed",
                area_id=zone.area_id,
                entity_id=zone.media_player_entity_id,
                message=endpoint.diagnostic,
                level="error",
                result="blocked",
            )
            await self._terminate_process(endpoint.ffmpeg)
            await self._terminate_process(endpoint.metadata_reader)
            self._remove_metadata_pipe(endpoint.metadata_pipe_path)
            self._close_volume_socket(endpoint.volume_socket, endpoint.volume_socket_path)
            endpoint.volume_socket = None
            return
        endpoint.state = "advertising"
        endpoint.diagnostic = "AirPlay 2 anunciado; aguardando seleção Apple"
        endpoint.pcm_task = asyncio.create_task(self._consume_pcm(endpoint), name=f"airplay-pcm-{zone.zone_id}")
        endpoint.mp3_task = asyncio.create_task(self._consume_mp3(endpoint), name=f"airplay-mp3-{zone.zone_id}")
        endpoint.metadata_task = asyncio.create_task(
            self._consume_metadata(endpoint),
            name=f"airplay-metadata-{zone.zone_id}",
        )
        endpoint.volume_task = asyncio.create_task(
            self._consume_volume_hook(endpoint),
            name=f"airplay-volume-hook-{zone.zone_id}",
        )
        endpoint.process_log_task = asyncio.create_task(self._consume_process_log(endpoint), name=f"airplay-log-{zone.zone_id}")
        endpoint.ffmpeg_log_task = asyncio.create_task(self._consume_ffmpeg_log(endpoint), name=f"airplay-ffmpeg-log-{zone.zone_id}")
        endpoint.idle_task = asyncio.create_task(self._watch_idle(endpoint), name=f"airplay-idle-{zone.zone_id}")
        self._endpoints[zone.zone_id] = endpoint
        await self.event_recorder(
            event="airplay_endpoint_started",
            area_id=zone.area_id,
            entity_id=zone.media_player_entity_id,
            message=f"receptor AirPlay 2 TecnoHead {zone.zone_id} anunciado na porta {port}",
            command_kind="shairport-sync",
            result="advertising",
        )

    @staticmethod
    def _safe_zone_name(zone_id: str) -> str:
        return re.sub(r"[^a-z0-9_-]", "-", zone_id.casefold()) or "zone"

    def _metadata_pipe_path(self, zone: AudioZoneProfile) -> Path:
        return self.settings.data_dir / "airplay" / f"{self._safe_zone_name(zone.zone_id)}-metadata"

    def _volume_socket_path(self, zone: AudioZoneProfile) -> Path:
        return self.settings.data_dir / "airplay" / f"{self._safe_zone_name(zone.zone_id)}-volume.sock"

    @staticmethod
    def _prepare_metadata_pipe(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        if not hasattr(os, "mkfifo"):
            raise OSError("o sistema operacional não oferece FIFO para metadados AirPlay")
        os.mkfifo(path, 0o600)

    @staticmethod
    def _remove_metadata_pipe(path: Path | None) -> None:
        if path:
            with contextlib.suppress(FileNotFoundError, OSError):
                path.unlink()

    @staticmethod
    def _prepare_volume_socket(path: Path) -> socket.socket:
        if not hasattr(socket, "AF_UNIX"):
            raise OSError("o sistema operacional não oferece sockets Unix para o gancho de volume AirPlay")
        path.parent.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        volume_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            volume_socket.bind(str(path))
            os.chmod(path, 0o600)
            volume_socket.setblocking(False)
            return volume_socket
        except OSError:
            volume_socket.close()
            with contextlib.suppress(FileNotFoundError):
                path.unlink()
            raise

    @staticmethod
    def _close_volume_socket(volume_socket: socket.socket | None, path: Path | None) -> None:
        if volume_socket:
            with contextlib.suppress(OSError):
                volume_socket.close()
        if path:
            with contextlib.suppress(FileNotFoundError, OSError):
                path.unlink()

    def _config_text(
        self,
        zone: AudioZoneProfile,
        port: int,
        metadata_pipe: Path | None = None,
        volume_socket: Path | None = None,
    ) -> str:
        service_name = zone.airplay.service_name or f"TecnoHead {zone.zone_id.title()}"
        stable = re.sub(r"[^0-9a-f]", "", zone.airplay.stable_id.casefold())
        device_id = (stable[:12] or secrets.token_hex(6)).ljust(12, "0")
        shm_name = f"/tecnohead-{re.sub(r'[^a-z0-9-]', '-', zone.zone_id.casefold())}"[:63]
        metadata_pipe = metadata_pipe or self._metadata_pipe_path(zone)
        volume_socket = volume_socket or self._volume_socket_path(zone)
        # On a host with more than one interface, letting Avahi associate the
        # service with its default hostname can make the RTSP target resolve to
        # the wrong interface. The address is resolved at runtime and is never
        # persisted in the repository or exposed in diagnostics.
        address_line = f"  address = {_quote_config(self._lan_address)};\n" if self._lan_address else ""
        return f'''// Generated by TecnoHead Multimídia. Do not edit inside the container.
general = {{
  name = {_quote_config(service_name)};
  service_type = "airplay2";
  mdns_backend = "avahi";
  output_backend = "stdout";
  port = {port};
{address_line}  regtype = "_airplay._tcp";
  airplay_device_id = 0x{device_id}L;
  nqptp_shared_memory_interface_name = {_quote_config(shm_name)};
  # Keep PCM at full gain. The pvol metadata below is forwarded to the
  # physical LinkPlay media_player, so the iPhone changes the player volume
  # instead of applying a second software attenuation in this bridge.
  ignore_volume_control = "yes";
  # Shairport Sync appends the AirPlay dB value to this command. The hook
  # sends only that value over a private Unix datagram socket so the App can
  # update the physical LinkPlay player without relying only on metadata.
  run_this_when_volume_is_set = {_quote_config(f"{VOLUME_HOOK_PATH} {volume_socket} ")};
  interpolation = "basic";
  mixdown = "stereo";
}};
stdout = {{
  output_rate = {PCM_RATE};
  output_format = "S32_LE";
  output_channels = {PCM_CHANNELS};
}};
metadata = {{
  enabled = "yes";
  include_cover_art = "no";
  pipe_name = {_quote_config(str(metadata_pipe))};
  pipe_timeout = 1000;
}};
sessioncontrol = {{
  active_state_timeout = {STREAM_IDLE_SECONDS};
}};
diagnostics = {{
  log_verbosity = 1;
}};
'''

    async def _consume_pcm(self, endpoint: _Endpoint) -> None:
        assert endpoint.process and endpoint.process.stdout and endpoint.ffmpeg and endpoint.ffmpeg.stdin
        try:
            while True:
                chunk = await endpoint.process.stdout.read(65536)
                if not chunk:
                    break
                endpoint.last_pcm_at = time.monotonic()
                try:
                    endpoint.ffmpeg.stdin.write(chunk)
                    await endpoint.ffmpeg.stdin.drain()
                except (BrokenPipeError, ConnectionResetError):
                    break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            endpoint.last_error = _redact_process_line(str(exc))
        finally:
            if endpoint.ffmpeg and endpoint.ffmpeg.stdin:
                with contextlib.suppress(BrokenPipeError, ConnectionResetError, OSError):
                    endpoint.ffmpeg.stdin.close()
            if endpoint.process and endpoint.process.returncode is None:
                endpoint.state = "error"
                endpoint.diagnostic = "Shairport Sync encerrou o fluxo de áudio"

    async def _consume_mp3(self, endpoint: _Endpoint) -> None:
        assert endpoint.ffmpeg and endpoint.ffmpeg.stdout
        try:
            while True:
                chunk = await endpoint.ffmpeg.stdout.read(32768)
                if not chunk:
                    break
                endpoint.last_mp3_at = time.monotonic()
                await endpoint.broker.publish(chunk)
                if not endpoint.output_started:
                    endpoint.output_started = True
                    endpoint.session_started_at = time.monotonic()
                    endpoint.activation_task = asyncio.create_task(self._activate_linkplay(endpoint), name=f"airplay-activate-{endpoint.zone.zone_id}")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            endpoint.last_error = _redact_process_line(str(exc))

    @staticmethod
    async def _read_metadata_item(
        stream: asyncio.StreamReader,
        header: bytes,
    ) -> tuple[str, str, bytes] | None:
        match = _METADATA_HEADER_RE.search(header)
        if not match:
            return None
        type_code = _metadata_fourcc(match.group("type"))
        item_code = _metadata_fourcc(match.group("code"))
        if not type_code or not item_code:
            return None
        try:
            length = int(match.group("length"))
        except ValueError:
            return None
        if length <= 0:
            return type_code, item_code, b""

        marker = await stream.readline()
        if not marker or not marker.lstrip().startswith(b"<data"):
            return None
        encoded_parts: list[bytes] = []
        while True:
            line = await stream.readline()
            if not line:
                return None
            if line.lstrip().startswith(b"</data>"):
                break
            encoded_parts.append(line.strip())
        payload = b""
        if encoded_parts:
            with contextlib.suppress(ValueError, binascii.Error):
                payload = base64.b64decode(b"".join(encoded_parts), validate=False)
        return type_code, item_code, payload[:length]

    async def _consume_metadata(self, endpoint: _Endpoint) -> None:
        if not endpoint.metadata_reader or not endpoint.metadata_reader.stdout:
            return
        try:
            while True:
                header = await endpoint.metadata_reader.stdout.readline()
                if not header:
                    return
                item = await self._read_metadata_item(endpoint.metadata_reader.stdout, header)
                if not item:
                    continue
                type_code, item_code, payload = item
                if type_code != "ssnc" or item_code != "pvol":
                    continue
                fields = payload.decode("ascii", errors="ignore").split(",")
                if not fields:
                    continue
                volume_percent = airplay_volume_to_percent(fields[0])
                if volume_percent is None:
                    continue
                await self._forward_airplay_volume(endpoint, volume_percent)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            endpoint.last_error = _redact_process_line(str(exc))
            await self.event_recorder(
                event="airplay_volume_bridge_failed",
                area_id=endpoint.zone.area_id,
                entity_id=endpoint.zone.media_player_entity_id,
                message="a leitura do volume AirPlay foi interrompida",
                level="warning",
                result="degraded",
            )

    async def _consume_volume_hook(self, endpoint: _Endpoint) -> None:
        if not endpoint.volume_socket:
            return
        loop = asyncio.get_running_loop()
        try:
            while True:
                payload = await loop.sock_recv(endpoint.volume_socket, 128)
                if not payload:
                    continue
                volume_percent = airplay_volume_to_percent(payload)
                if volume_percent is None:
                    continue
                endpoint.last_airplay_volume_source = "shairport_volume_hook"
                await self._forward_airplay_volume(endpoint, volume_percent)
        except asyncio.CancelledError:
            raise
        except (OSError, RuntimeError) as exc:
            endpoint.last_error = _redact_process_line(str(exc))
            await self.event_recorder(
                event="airplay_volume_hook_failed",
                area_id=endpoint.zone.area_id,
                entity_id=endpoint.zone.media_player_entity_id,
                message="a ponte nativa de volume AirPlay foi interrompida",
                level="warning",
                result="degraded",
            )

    async def _forward_airplay_volume(self, endpoint: _Endpoint, volume_percent: int) -> None:
        if endpoint.last_airplay_volume_percent == volume_percent:
            return
        endpoint.last_airplay_volume_percent = volume_percent
        endpoint.last_airplay_volume_at = time.monotonic()
        try:
            result = await self.audio.set_airplay_volume(
                self._config,
                endpoint.zone.zone_id,
                volume_percent,
            )
            applied = int(result.get("applied_percent", volume_percent))
            await self.event_recorder(
                event="airplay_volume_forwarded",
                area_id=endpoint.zone.area_id,
                entity_id=endpoint.zone.media_player_entity_id,
                message="volume AirPlay encaminhado ao media_player LinkPlay pela API do Home Assistant",
                command_kind="media_player.volume_set",
                result=f"accepted_by_home_assistant:{applied}%",
                physical_confirmation="not_observable",
            )
        except (HomeAssistantError, RuntimeError, ValueError, AudioActionError) as exc:
            endpoint.last_error = _redact_process_line(str(exc))
            await self.event_recorder(
                event="airplay_volume_forward_failed",
                area_id=endpoint.zone.area_id,
                entity_id=endpoint.zone.media_player_entity_id,
                message="o Home Assistant não aceitou o volume físico solicitado pelo AirPlay",
                level="warning",
                command_kind="media_player.volume_set",
                result="degraded",
            )

    async def _activate_linkplay(self, endpoint: _Endpoint) -> None:
        url = self._stream_url(endpoint)
        if not url:
            endpoint.state = "blocked"
            endpoint.diagnostic = "não foi possível resolver um endereço LAN para a ponte de áudio"
            return
        try:
            await self.audio.start_airplay_output(self._config, endpoint.zone.zone_id, url)
            endpoint.linkplay_started = True
            endpoint.state = "streaming"
            endpoint.diagnostic = "PCM recebido; reprodução HTTP solicitada ao LinkPlay via Home Assistant"
            await self.event_recorder(
                event="airplay_linkplay_play_requested",
                area_id=endpoint.zone.area_id,
                entity_id=endpoint.zone.media_player_entity_id,
                message="URL de áudio AirPlay encaminhada ao media_player pela API do Home Assistant",
                command_kind="media_player.play_media",
                result="accepted_by_home_assistant",
                physical_confirmation="not_observable",
            )
        except (HomeAssistantError, RuntimeError, ValueError) as exc:
            endpoint.state = "blocked"
            endpoint.last_error = _redact_process_line(str(exc))
            endpoint.diagnostic = endpoint.last_error
            await self.event_recorder(
                event="airplay_linkplay_play_blocked",
                area_id=endpoint.zone.area_id,
                entity_id=endpoint.zone.media_player_entity_id,
                message=endpoint.last_error,
                level="warning",
                command_kind="media_player.play_media",
                result="blocked",
            )

    async def _watch_idle(self, endpoint: _Endpoint) -> None:
        try:
            while endpoint.process and endpoint.process.returncode is None:
                await asyncio.sleep(1)
                if endpoint.output_started and endpoint.last_mp3_at and time.monotonic() - endpoint.last_mp3_at > STREAM_IDLE_SECONDS:
                    await self._deactivate_linkplay(endpoint)
            if endpoint.process and endpoint.process.returncode is not None:
                returncode = endpoint.process.returncode
                if endpoint.state not in {"error", "blocked"}:
                    endpoint.state = "blocked"
                    endpoint.diagnostic = f"Shairport Sync encerrou durante a publicação (código {returncode}); consulte o diagnóstico do endpoint"
                endpoint.last_error = endpoint.diagnostic
        except asyncio.CancelledError:
            raise

    async def _deactivate_linkplay(self, endpoint: _Endpoint) -> None:
        if not endpoint.output_started:
            return
        endpoint.output_started = False
        if endpoint.linkplay_started:
            with contextlib.suppress(Exception):
                await self.audio.stop_airplay_output(self._config, endpoint.zone.zone_id)
        endpoint.linkplay_started = False
        endpoint.broker.reset()
        endpoint.state = "advertising"
        endpoint.diagnostic = "sessão AirPlay encerrada; aguardando nova seleção Apple"
        await self.event_recorder(
            event="airplay_session_stopped",
            area_id=endpoint.zone.area_id,
            entity_id=endpoint.zone.media_player_entity_id,
            message="fluxo AirPlay sem áudio; saída LinkPlay liberada sem retomar fonte automaticamente",
            command_kind="airplay-session",
            result="stopped",
        )

    async def _consume_process_log(self, endpoint: _Endpoint) -> None:
        if not endpoint.process or not endpoint.process.stderr:
            return
        try:
            async for raw in endpoint.process.stderr:
                line = _redact_process_line(raw.decode("utf-8", errors="replace"))
                if line:
                    endpoint.process_log_tail.append(line)
                    endpoint.diagnostic = line
        except asyncio.CancelledError:
            raise

    async def _consume_ffmpeg_log(self, endpoint: _Endpoint) -> None:
        if not endpoint.ffmpeg or not endpoint.ffmpeg.stderr:
            return
        try:
            async for raw in endpoint.ffmpeg.stderr:
                line = _redact_process_line(raw.decode("utf-8", errors="replace"))
                if line:
                    endpoint.last_error = line
        except asyncio.CancelledError:
            raise

    async def _consume_nqptp_log(self) -> None:
        if not self._nqptp or not self._nqptp.stdout:
            return
        try:
            async for raw in self._nqptp.stdout:
                line = _redact_process_line(raw.decode("utf-8", errors="replace"))
                if line and "error" in line.casefold():
                    self._dependency_error = line
        except asyncio.CancelledError:
            raise

    async def _consume_mdns_log(self, process: asyncio.subprocess.Process, label: str) -> None:
        if not process.stdout:
            return
        try:
            async for raw in process.stdout:
                line = _redact_process_line(raw.decode("utf-8", errors="replace"))
                if line:
                    self._mdns_log_tail.append(f"{label}: {line}")
        except asyncio.CancelledError:
            raise

    async def _stop_endpoint(self, zone_id: str) -> None:
        endpoint = self._endpoints.pop(zone_id, None)
        if not endpoint:
            return
        for task in (
            endpoint.activation_task,
            endpoint.idle_task,
            endpoint.pcm_task,
            endpoint.mp3_task,
            endpoint.metadata_task,
            endpoint.volume_task,
            endpoint.process_log_task,
            endpoint.ffmpeg_log_task,
        ):
            if task and not task.done():
                task.cancel()
        for task in (
            endpoint.activation_task,
            endpoint.idle_task,
            endpoint.pcm_task,
            endpoint.mp3_task,
            endpoint.metadata_task,
            endpoint.volume_task,
            endpoint.process_log_task,
            endpoint.ffmpeg_log_task,
        ):
            if task:
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task
        await self._terminate_process(endpoint.process)
        await self._terminate_process(endpoint.ffmpeg)
        await self._terminate_process(endpoint.metadata_reader)
        await endpoint.broker.close()
        self._remove_metadata_pipe(endpoint.metadata_pipe_path)
        self._close_volume_socket(endpoint.volume_socket, endpoint.volume_socket_path)
        endpoint.volume_socket = None

    @staticmethod
    async def _terminate_process(process: asyncio.subprocess.Process | None) -> None:
        if not process or process.returncode is not None:
            return
        with contextlib.suppress(ProcessLookupError):
            process.terminate()
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(process.wait(), timeout=3)
        if process.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                process.kill()

    async def stop(self) -> None:
        async with self._lock:
            for zone_id in list(self._endpoints):
                await self._stop_endpoint(zone_id)
            if self._nqptp:
                await self._terminate_process(self._nqptp)
            if self._nqptp_log_task and not self._nqptp_log_task.done():
                self._nqptp_log_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._nqptp_log_task
            self._nqptp = None
            for task in self._mdns_log_tasks:
                if not task.done():
                    task.cancel()
            for task in self._mdns_log_tasks:
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task
            self._mdns_log_tasks.clear()
            await self._terminate_process(self._avahi_process)
            await self._terminate_process(self._dbus_process)
            self._avahi_process = None
            self._dbus_process = None
            self._mdns_env = {}
            self._mdns_mode = "not_started"

    def stream(self, zone_id: str, token: str) -> AsyncIterator[bytes]:
        endpoint = self._endpoints.get(zone_id)
        if not endpoint or not secrets.compare_digest(endpoint.token, token):
            raise KeyError(zone_id)
        return endpoint.broker.subscribe()

    def report(self) -> dict[str, Any]:
        if self._dependency_error:
            overall_state = "blocked"
            reason = self._dependency_error
        elif not self._endpoints:
            overall_state = "not_configured"
            reason = "ative a identidade AirPlay 2 nas zonas habilitadas"
        elif any(item.state == "streaming" for item in self._endpoints.values()):
            overall_state = "streaming"
            reason = "há uma sessão AirPlay encaminhada ao LinkPlay; o som ainda precisa de confirmação física"
        elif any(item.state == "advertising" for item in self._endpoints.values()):
            overall_state = "ready"
            reason = "destinos AirPlay 2 anunciados; selecione um no iPhone para iniciar a prova física"
        else:
            overall_state = "starting"
            reason = "processos AirPlay 2 em inicialização"
        return {
            "state": overall_state,
            "reason": reason,
            "shairport_sync": self._shairport_version,
            "airplay2_handshake": "not_tested",
            "nqptp": self._nqptp_version if self._nqptp else "not_started",
            "mdns": self._mdns_mode,
            "mdns_diagnostic": self._mdns_diagnostic,
            "mdns_process_alive": bool(self._avahi_process and self._avahi_process.returncode is None)
            if self._mdns_mode == "private_avahi"
            else None,
            "mdns_log_tail": list(self._mdns_log_tail),
            "physical_audio": "not_tested",
            "stream_host_resolved": bool(self._lan_address),
            "stream_port": self.stream_port,
            "endpoints": {
                zone_id: {
                    "service_name": endpoint.zone.airplay.service_name or f"TecnoHead {zone_id.title()}",
                    "listen_port": endpoint.port,
                    "state": endpoint.state,
                    "diagnostic": endpoint.diagnostic,
                    "clients": endpoint.broker.client_count,
                    "bytes_sent": endpoint.broker.bytes_sent,
                    "volume_bridge": "active",
                    "last_airplay_volume_percent": endpoint.last_airplay_volume_percent,
                    "last_airplay_volume_at": datetime.fromtimestamp(endpoint.last_airplay_volume_at, UTC).isoformat() if endpoint.last_airplay_volume_at else None,
                    "last_airplay_volume_source": endpoint.last_airplay_volume_source,
                    "volume_hook_active": bool(endpoint.volume_socket),
                    "process_alive": bool(endpoint.process and endpoint.process.returncode is None),
                    "process_returncode": endpoint.process.returncode if endpoint.process else None,
                    "process_log_tail": list(endpoint.process_log_tail),
                    "last_error": endpoint.last_error,
                    "session_started_at": datetime.fromtimestamp(endpoint.session_started_at, UTC).isoformat() if endpoint.session_started_at else None,
                }
                for zone_id, endpoint in self._endpoints.items()
            },
        }
