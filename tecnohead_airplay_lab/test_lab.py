"""Offline safety and framing checks for the standalone lab receiver."""

import asyncio
import base64
import importlib.util
import json
import plistlib
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("tecnohead_lab", Path(__file__).with_name("lab.py"))
assert SPEC and SPEC.loader
lab = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lab
SPEC.loader.exec_module(lab)


@pytest.mark.parametrize("profile", list(lab.PROFILES))
def test_profile_options(tmp_path: Path, profile: str) -> None:
    options = tmp_path / "options.json"
    options.write_text(json.dumps({"profile": profile}), encoding="utf-8")
    assert lab.load_profile(options) == profile


def test_unknown_profile_fails_closed(tmp_path: Path) -> None:
    options = tmp_path / "options.json"
    options.write_text('{"profile":"vendor-mask"}', encoding="utf-8")
    with pytest.raises(ValueError):
        lab.load_profile(options)


def test_stable_id_is_separate_and_persistent(tmp_path: Path) -> None:
    identity = tmp_path / "lab_device_id"
    first = lab.stable_lab_id(identity)
    assert first == lab.stable_lab_id(identity)
    assert len(first) == 12 and first.startswith("02")
    identity.write_text("bad", encoding="ascii")
    with pytest.raises(ValueError):
        lab.stable_lab_id(identity)


@pytest.mark.parametrize("profile", list(lab.PROFILES))
def test_config_does_not_claim_vendor_capabilities(profile: str) -> None:
    config = lab.shairport_config(profile, "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"))
    assert 'name = "TecnoHead AirPlay Lab";' in config
    assert "port = 7100;" in config
    assert 'output_backend = "stdout";' in config
    assert "airplay_device_id = 0x02AABBCCDDEEL;" in config
    assert 'include_cover_art = "yes";' in config if profile in {"M2", "M3"} else 'include_cover_art = "no";' in config
    assert ('get_plist_metadata = "no";' in config) == (profile == "M2")
    assert "apple_feature_comparison" not in config
    assert "WiiM" not in config and "HomePod" not in config and "MFi" not in config


def test_mediaremote_counters_retain_no_media() -> None:
    counters = lab.Counters()
    secret_title = "Private user track"
    plist = plistlib.dumps({
        "type": "updateMRNowPlayingInfo",
        "params": {"params": {"kMRMediaRemoteNowPlayingInfoTitle": secret_title}},
    })
    counters.observe_metadata("ssnc", "copl", plist)
    summary = counters.summary()
    assert summary["sender_now_playing_updates"] == 1
    assert summary["sender_now_playing_max_bytes"] == len(plist)
    assert summary["sender_supported_commands_max_bytes"] == 0
    assert summary["sender_field_presence"] == ["title"]
    assert secret_title not in json.dumps(summary)


@pytest.mark.asyncio
async def test_metadata_pipe_framing() -> None:
    title = "Private user track"
    payload = plistlib.dumps({
        "type": "updateMRNowPlayingInfo",
        "params": {"params": {"kMRMediaRemoteNowPlayingInfoTitle": title}},
    })
    header = (
        f"<item><type>{b'ssnc'.hex()}</type><code>{b'copl'.hex()}</code>"
        f"<length>{len(payload)}</length>\n<data encoding=\"base64\">\n"
    ).encode()
    stream = asyncio.StreamReader()
    stream.feed_data(header + base64.b64encode(payload) + lab.FOOTER)
    stream.feed_eof()
    counters = lab.Counters()
    await lab.consume_metadata(stream, counters)
    assert counters.sender_now_playing_updates == 1
    assert title not in json.dumps(counters.summary())


@pytest.mark.asyncio
async def test_rc_gate_logs_only_sanitized_markers(capsys: pytest.CaptureFixture[str]) -> None:
    secret = "private peer and track"
    stream = asyncio.StreamReader()
    stream.feed_data(
        f"{secret} TECNOHEAD_RC_RECORD_SEEN\n"
        f"{secret} TECNOHEAD_RC_GATE_MASK_31\n"
        f"{secret} TECNOHEAD_RC_LOOP_ALIVE_MASK_31\n"
        f"{secret} TECNOHEAD_RC_EVENT_CLEANUP\n"
        f"{secret} TECNOHEAD_RC_SNAPSHOT_CLEARED\n"
        f"{secret} TECNOHEAD_RC_GATE_MASK_999\n"
        f"{secret} TECNOHEAD_RC_LOOP_ALIVE_MASK_999\n".encode()
    )
    stream.feed_eof()
    counters = lab.Counters()
    await lab.consume_shairport_log(stream, counters)
    assert counters.rc["TECNOHEAD_RC_RECORD_SEEN"] == 1
    assert counters.rc["TECNOHEAD_RC_GATE_MASK_31"] == 1
    assert counters.rc["TECNOHEAD_RC_LOOP_ALIVE_MASK_31"] == 1
    assert counters.rc["TECNOHEAD_RC_EVENT_CLEANUP"] == 1
    assert counters.rc["TECNOHEAD_RC_SNAPSHOT_CLEARED"] == 1
    assert "TECNOHEAD_RC_GATE_MASK_999" not in counters.rc
    assert "TECNOHEAD_RC_LOOP_ALIVE_MASK_999" not in counters.rc
    assert secret not in capsys.readouterr().out
