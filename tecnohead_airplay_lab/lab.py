"""One isolated AirPlay 2 receiver; log counts, never user media or peers."""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import os
import plistlib
import re
import secrets
import signal
import socket
from collections import Counter
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

DATA = Path("/data")
RUNTIME = Path("/tmp/tecnohead-airplay-lab")
PROFILES = {
    "B0": (False, False),
    "M1": (False, True),
    "M2": (True, False),
    "M3": (True, True),
}
MAX_ITEM = 2 * 1024 * 1024
MAX_DECLARED_ITEM = 64 * 1024 * 1024
HEADER = re.compile(
    rb"<item><type>(?P<type>[0-9a-fA-F]{8})</type>"
    rb"<code>(?P<code>[0-9a-fA-F]{8})</code>"
    rb"<length>(?P<length>\d+)</length>"
)
FOOTER = b"</data></item>\n"
RC_MARKERS = (
    "TECNOHEAD_RC_SETUP_OK",
    "TECNOHEAD_RC_EVENT_CONNECTED",
    "TECNOHEAD_RC_UPDATE_INFO_ACK",
    "TECNOHEAD_RC_MEDIAREMOTE_ACK_NOW_PLAYING",
    "TECNOHEAD_RC_MEDIAREMOTE_ACK_COMMANDS",
)


def report(event: str, **fields: object) -> None:
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


def load_profile(path: Path = DATA / "options.json") -> str:
    options = json.loads(path.read_text(encoding="utf-8"))
    profile = options.get("profile")
    if profile not in PROFILES:
        raise ValueError("invalid laboratory profile")
    return profile


def stable_lab_id(path: Path = DATA / "lab_device_id") -> str:
    """A separate, locally administered 48-bit ID; never a commercial MAC."""

    if path.exists():
        identity = path.read_text(encoding="ascii").strip()
    else:
        identity = "02" + secrets.token_hex(5).upper()
        with path.open("x", encoding="ascii") as handle:
            handle.write(identity + "\n")
        path.chmod(0o600)
    if not re.fullmatch(r"02[0-9A-Fa-f]{10}", identity):
        raise ValueError("invalid laboratory identity in persistent data")
    return identity.upper()


def lan_address() -> str:
    """Read the selected LAN interface without transmitting a UDP packet."""

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("10.255.255.255", 9))
        address = sock.getsockname()[0]
    if address.startswith("127.") or address == "0.0.0.0":
        raise RuntimeError("no LAN address")
    return address


def shairport_config(profile: str, identity: str, address: str, pipe: Path) -> str:
    classic, _ = PROFILES[profile]
    if not re.fullmatch(r"02[0-9A-F]{10}", identity):
        raise ValueError("invalid identity")
    if not re.fullmatch(r"[0-9.]+", address):
        raise ValueError("invalid address")
    # No commercial model, unknown feature bit, MFi claim, or pairing bypass.
    return f'''general = {{
  name = "TecnoHead AirPlay Lab";
  service_type = "airplay2";
  dbus_service_bus = "session";
  mpris_service_bus = "session";
  mdns_backend = "avahi";
  output_backend = "stdout";
  port = 7100;
  address = "{address}";
  regtype = "_airplay._tcp";
  airplay_device_id = 0x{identity}L;
  nqptp_shared_memory_interface_name = "/tecnohead-airplay-lab";
  ignore_volume_control = "yes";
  interpolation = "basic";
  mixdown = "stereo";
}};
stdout = {{
  output_rate = 48000;
  output_format = "S32_LE";
  output_channels = 2;
}};
metadata = {{
  enabled = "yes";
  include_cover_art = "{"yes" if classic else "no"}";
  {('cover_art_cache_directory = "";' if classic else '')}
  pipe_name = "{pipe}";
  pipe_timeout = 1000;
}};
sessioncontrol = {{ active_state_timeout = 8.0; }};
diagnostics = {{
  log_verbosity = 1;
  {('get_plist_metadata = "no";' if profile == "M2" else '')}
}};
'''


def bus_config(socket_path: Path) -> str:
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
    <allow send_destination="*"/>
    <allow receive_sender="*"/>
    <allow receive_type="method_call"/>
    <allow receive_type="method_return"/>
    <allow receive_type="error"/>
    <allow receive_type="signal"/>
  </policy>
</busconfig>
'''


AVAHI_CONFIG = '''[server]
host-name=tecnohead-airplay-lab
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


@dataclass
class Counters:
    pcm_bytes_discarded: int = 0
    metadata_items: int = 0
    classic_artwork_items: int = 0
    classic_track_items: int = 0
    sender_now_playing_updates: int = 0
    sender_now_playing_max_bytes: int = 0
    sender_supported_commands_updates: int = 0
    sender_supported_commands_max_bytes: int = 0
    sender_playback_updates: int = 0
    sender_field_presence: set[str] = field(default_factory=set)
    oversized_items: int = 0
    invalid_items: int = 0
    rc: Counter[str] = field(default_factory=Counter)

    def observe_metadata(self, type_code: str, code: str, payload: bytes) -> None:
        self.metadata_items += 1
        if code == "PICT":
            self.classic_artwork_items += 1
        elif code in {"minm", "asar", "asal"}:
            self.classic_track_items += 1
        if type_code != "ssnc" or code != "copl":
            return
        try:
            message = plistlib.loads(payload)
        except (ValueError, TypeError, OverflowError, plistlib.InvalidFileException):
            self.invalid_items += 1
            return
        if not isinstance(message, dict):
            self.invalid_items += 1
            return
        kind = message.get("type")
        if kind == "updateMRNowPlayingInfo":
            self.sender_now_playing_updates += 1
            self.sender_now_playing_max_bytes = max(self.sender_now_playing_max_bytes, len(payload))
            params = message.get("params")
            info = params.get("params", params) if isinstance(params, dict) else None
            if isinstance(info, dict):
                for field_name, suffix in (
                    ("title", "Title"), ("artist", "Artist"),
                    ("album", "Album"), ("artwork", "ArtworkData"),
                    ("duration", "Duration"), ("position", "ElapsedTime"),
                ):
                    if info.get(f"kMRMediaRemoteNowPlayingInfo{suffix}"):
                        self.sender_field_presence.add(field_name)
        elif kind == "updateMRSupportedCommands":
            self.sender_supported_commands_updates += 1
            self.sender_supported_commands_max_bytes = max(
                self.sender_supported_commands_max_bytes, len(payload)
            )
        elif kind == "updateMRPlaybackState":
            self.sender_playback_updates += 1

    def summary(self) -> dict[str, object]:
        return {
            "pcm_bytes_discarded": self.pcm_bytes_discarded,
            "metadata_items": self.metadata_items,
            "classic_artwork_items": self.classic_artwork_items,
            "classic_track_items": self.classic_track_items,
            "sender_now_playing_updates": self.sender_now_playing_updates,
            "sender_now_playing_max_bytes": self.sender_now_playing_max_bytes,
            "sender_supported_commands_updates": self.sender_supported_commands_updates,
            "sender_supported_commands_max_bytes": self.sender_supported_commands_max_bytes,
            "sender_playback_updates": self.sender_playback_updates,
            "sender_field_presence": sorted(self.sender_field_presence),
            "oversized_items": self.oversized_items,
            "invalid_items": self.invalid_items,
            "rc": dict(sorted(self.rc.items())),
        }


def fourcc(raw: bytes) -> str | None:
    try:
        result = bytes.fromhex(raw.decode("ascii")).decode("ascii")
    except (ValueError, UnicodeDecodeError):
        return None
    return result if len(result) == 4 else None


async def consume_metadata(stream: asyncio.StreamReader, counters: Counters) -> None:
    while header := await stream.readline():
        match = HEADER.search(header)
        if match is None:
            continue
        try:
            length = int(match.group("length"))
            if length > MAX_DECLARED_ITEM:
                counters.oversized_items += 1
                return
            marker = await stream.readline()
            if not marker.lstrip().startswith(b"<data"):
                counters.invalid_items += 1
                continue
            remaining = ((length + 2) // 3) * 4
            encoded = bytearray()
            while remaining:
                chunk = await stream.readexactly(min(remaining, 64 * 1024))
                if length <= MAX_ITEM:
                    encoded.extend(chunk)
                remaining -= len(chunk)
            if await stream.readexactly(len(FOOTER)) != FOOTER:
                counters.invalid_items += 1
                continue
            if length > MAX_ITEM:
                counters.oversized_items += 1
                continue
            payload = base64.b64decode(encoded, validate=True)
            if len(payload) != length:
                counters.invalid_items += 1
                continue
        except (asyncio.IncompleteReadError, ValueError, binascii.Error):
            counters.invalid_items += 1
            return
        type_code = fourcc(match.group("type"))
        item_code = fourcc(match.group("code"))
        if type_code and item_code:
            counters.observe_metadata(type_code, item_code, payload)


async def discard_pcm(stream: asyncio.StreamReader, counters: Counters) -> None:
    while chunk := await stream.read(64 * 1024):
        counters.pcm_bytes_discarded += len(chunk)


async def consume_shairport_log(stream: asyncio.StreamReader, counters: Counters) -> None:
    while raw := await stream.readline():
        # Raw log lines may contain peers and media; only emit fixed markers.
        line = raw.decode("utf-8", errors="replace").strip()
        for marker in RC_MARKERS:
            if line.endswith(marker):
                counters.rc[marker] += 1
                report("rc_marker", marker=marker, count=counters.rc[marker])
                break


async def discard_stream(stream: asyncio.StreamReader | None) -> None:
    if stream:
        while await stream.read(64 * 1024):
            pass


async def wait_for_socket(path: Path, process: asyncio.subprocess.Process) -> None:
    for _ in range(40):
        if process.returncode is not None:
            raise RuntimeError("private D-Bus exited")
        if path.exists():
            return
        await asyncio.sleep(0.1)
    raise RuntimeError("private D-Bus socket not created")


async def terminate(process: asyncio.subprocess.Process | None) -> None:
    if not process or process.returncode is not None:
        return
    with suppress(ProcessLookupError):
        process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=3)
    except TimeoutError:
        with suppress(ProcessLookupError):
            process.kill()
        await process.wait()


async def run() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    profile = load_profile()
    identity = stable_lab_id()
    address = lan_address()
    classic, relay = PROFILES[profile]
    bus_socket = RUNTIME / "bus.sock"
    pipe = RUNTIME / "metadata.pipe"
    for path in (bus_socket, pipe):
        with suppress(FileNotFoundError):
            path.unlink()
    os.mkfifo(pipe, 0o600)
    (RUNTIME / "bus.conf").write_text(bus_config(bus_socket), encoding="utf-8")
    (RUNTIME / "avahi.conf").write_text(AVAHI_CONFIG, encoding="utf-8")
    (RUNTIME / "shairport.conf").write_text(
        shairport_config(profile, identity, address, pipe), encoding="utf-8"
    )
    env = {
        **os.environ,
        "DBUS_SYSTEM_BUS_ADDRESS": f"unix:path={bus_socket}",
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={bus_socket}",
        "TECNOHEAD_RC_NOW_PLAYING": "1" if relay else "0",
    }
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    processes: list[asyncio.subprocess.Process] = []
    tasks: list[asyncio.Task[None]] = []
    counters = Counters()
    report("lab_starting", profile=profile, classic_metadata=classic, rc_relay=relay, audio_output="discarded")
    try:
        bus = await asyncio.create_subprocess_exec(
            "dbus-daemon", f"--config-file={RUNTIME / 'bus.conf'}", "--nofork", "--nopidfile",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        processes.append(bus)
        tasks.append(asyncio.create_task(discard_stream(bus.stdout)))
        await wait_for_socket(bus_socket, bus)
        avahi = await asyncio.create_subprocess_exec(
            "avahi-daemon", "--no-chroot", "--no-drop-root", "--no-rlimits", "--debug",
            f"--file={RUNTIME / 'avahi.conf'}", env=env,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        processes.append(avahi)
        tasks.append(asyncio.create_task(discard_stream(avahi.stdout)))
        await asyncio.sleep(0.5)
        if avahi.returncode is not None:
            raise RuntimeError("private mDNS failed")
        nqptp = await asyncio.create_subprocess_exec(
            "nqptp", "-v", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        processes.append(nqptp)
        tasks.append(asyncio.create_task(discard_stream(nqptp.stdout)))
        await asyncio.sleep(0.3)
        if nqptp.returncode is not None:
            raise RuntimeError("NQPTP failed")
        # Keep the FIFO open before Shairport writes its first item.
        reader = await asyncio.create_subprocess_exec(
            "cat", str(pipe), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            limit=4 * 1024 * 1024,
        )
        processes.append(reader)
        tasks.append(asyncio.create_task(consume_metadata(reader.stdout, counters)))
        receiver = await asyncio.create_subprocess_exec(
            "shairport-sync", "-c", str(RUNTIME / "shairport.conf"), env=env,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            limit=4 * 1024 * 1024,
        )
        processes.append(receiver)
        tasks.append(asyncio.create_task(discard_pcm(receiver.stdout, counters)))
        tasks.append(asyncio.create_task(consume_shairport_log(receiver.stderr, counters)))
        await asyncio.sleep(0.6)
        if receiver.returncode is not None:
            raise RuntimeError("Shairport exited during startup")
        report("lab_ready", profile=profile, name="TecnoHead AirPlay Lab", port=7100)
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=15)
            except TimeoutError:
                pass
            report("lab_counts", **counters.summary())
            if stop.is_set():
                break
            if any(process.returncode is not None for process in (bus, avahi, nqptp, reader, receiver)):
                raise RuntimeError("a laboratory dependency exited")
    finally:
        for process in reversed(processes):
            await terminate(process)
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError, Exception):
                await task
        report("lab_stopped", profile=profile, **counters.summary())


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        # The exception itself may contain a path/address; never print it.
        report("lab_failed", reason=type(error).__name__)
        raise SystemExit(1) from None
