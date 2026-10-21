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


@pytest.mark.parametrize("advertisement", lab.ADVERTISEMENTS)
def test_advertisement_options(tmp_path: Path, advertisement: str) -> None:
    options = tmp_path / "options.json"
    options.write_text(json.dumps({"profile": "M1", "advertisement": advertisement}), encoding="utf-8")
    assert lab.load_advertisement(options) == advertisement


def test_missing_advertisement_defaults_to_stock(tmp_path: Path) -> None:
    options = tmp_path / "options.json"
    options.write_text('{"profile":"B0"}', encoding="utf-8")
    assert lab.load_advertisement(options) == "stock"


def test_unknown_advertisement_fails_closed(tmp_path: Path) -> None:
    options = tmp_path / "options.json"
    options.write_text('{"profile":"B0","advertisement":"vendor-mask"}', encoding="utf-8")
    with pytest.raises(ValueError):
        lab.load_advertisement(options)


@pytest.mark.parametrize("mode", lab.NETWORK_MODES)
def test_network_mode_options(tmp_path: Path, mode: str) -> None:
    options = tmp_path / "options.json"
    options.write_text(json.dumps({"profile": "B0", "network_mode": mode}), encoding="utf-8")
    assert lab.load_network_mode(options) == mode


def test_network_mode_defaults_to_ipv4_and_rejects_unknown(tmp_path: Path) -> None:
    options = tmp_path / "options.json"
    options.write_text('{"profile":"B0"}', encoding="utf-8")
    assert lab.load_network_mode(options) == "ipv4_only"
    options.write_text('{"profile":"B0","network_mode":"any"}', encoding="utf-8")
    with pytest.raises(ValueError):
        lab.load_network_mode(options)


@pytest.mark.parametrize("variant", lab.TXT_VARIANTS)
def test_txt_variant_options(tmp_path: Path, variant: str) -> None:
    options = tmp_path / "options.json"
    options.write_text(json.dumps({"profile": "M1", "txt_variant": variant}), encoding="utf-8")
    assert lab.load_txt_variant(options) == variant


def test_txt_variant_defaults_to_stock_and_rejects_unknown(tmp_path: Path) -> None:
    options = tmp_path / "options.json"
    options.write_text('{"profile":"B0"}', encoding="utf-8")
    assert lab.load_txt_variant(options) == "stock"
    options.write_text('{"profile":"B0","txt_variant":"vendor_certificate"}', encoding="utf-8")
    with pytest.raises(ValueError):
        lab.load_txt_variant(options)


@pytest.mark.parametrize("variant", lab.INFO_VARIANTS)
def test_info_variant_options(tmp_path: Path, variant: str) -> None:
    options = tmp_path / "options.json"
    options.write_text(json.dumps({"info_variant": variant}), encoding="utf-8")
    assert lab.load_info_variant(options) == variant


def test_info_variant_defaults_to_stock_and_rejects_unknown(tmp_path: Path) -> None:
    options = tmp_path / "options.json"
    options.write_text('{"profile":"B0"}', encoding="utf-8")
    assert lab.load_info_variant(options) == "stock"
    options.write_text('{"info_variant":"supports_ui_true"}', encoding="utf-8")
    with pytest.raises(ValueError):
        lab.load_info_variant(options)


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
@pytest.mark.parametrize("advertisement", lab.ADVERTISEMENTS)
def test_config_does_not_claim_vendor_capabilities(profile: str, advertisement: str) -> None:
    config = lab.shairport_config(
        profile, "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"), advertisement
    )
    assert 'name = "TecnoHead AirPlay Lab";' in config
    assert "port = 7100;" in config
    assert 'output_backend = "stdout";' in config
    assert "airplay_device_id = 0x02AABBCCDDEEL;" in config
    assert 'include_cover_art = "yes";' in config if profile in {"M2", "M3"} else 'include_cover_art = "no";' in config
    assert ('get_plist_metadata = "no";' in config) == (profile == "M2")
    assert "apple_feature_comparison" not in config
    assert f'apple_lab_advertisement = "{advertisement}";' in config
    assert 'apple_lab_txt_variant = "stock";' in config
    assert 'apple_lab_info_variant = "stock";' in config
    assert "WiiM" not in config and "HomePod" not in config and "MFi" not in config


def test_invalid_config_advertisement_fails_closed() -> None:
    with pytest.raises(ValueError):
        lab.shairport_config("M1", "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"), "vendor")


@pytest.mark.parametrize("variant", lab.TXT_VARIANTS)
def test_txt_variant_changes_only_diagnostic_option(variant: str) -> None:
    args = ("M1", "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"))
    baseline = lab.shairport_config(*args)
    changed = lab.shairport_config(*args, txt_variant=variant)
    assert changed == baseline.replace(
        'apple_lab_txt_variant = "stock";', f'apple_lab_txt_variant = "{variant}";'
    )
    assert "WiiM" not in changed and "HomePod" not in changed and "MFi" not in changed


def test_invalid_config_txt_variant_fails_closed() -> None:
    with pytest.raises(ValueError):
        lab.shairport_config(
            "M1", "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"),
            txt_variant="vendor_certificate",
        )


def test_info_variant_changes_only_diagnostic_option() -> None:
    args = ("M1", "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"))
    baseline = lab.shairport_config(*args)
    changed = lab.shairport_config(*args, info_variant="omit_audio_only_ui")
    assert changed == baseline.replace(
        'apple_lab_info_variant = "stock";',
        'apple_lab_info_variant = "omit_audio_only_ui";',
    )
    assert "WiiM" not in changed and "HomePod" not in changed and "MFi" not in changed


def test_invalid_config_info_variant_fails_closed() -> None:
    with pytest.raises(ValueError):
        lab.shairport_config(
            "M1", "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"),
            info_variant="supports_ui_true",
        )


def test_info_patch_omits_only_negative_ui_hint() -> None:
    patch = (Path(__file__).with_name("patches") / "shairport-lab-info-variant.patch").read_text()
    assert 'plist_dict_remove_item(capabilities, "supportsUIForAudioOnlyContent")' in patch
    assert 'plist_dict_remove_item(response_plist, "playbackCapabilities")' in patch
    assert 'config_lookup_string(config.cfg, "diagnostics.apple_lab_info_variant"' in patch
    assert "plist_new_bool" not in patch
    assert "airplay_features" not in patch


def test_info_variant_can_remove_entire_capabilities_dictionary() -> None:
    args = ("M1", "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"))
    baseline = lab.shairport_config(*args)
    changed = lab.shairport_config(*args, info_variant="omit_playback_capabilities")
    assert changed == baseline.replace(
        'apple_lab_info_variant = "stock";',
        'apple_lab_info_variant = "omit_playback_capabilities";',
    )
    assert "WiiM" not in changed and "HomePod" not in changed and "MFi" not in changed


def test_dual_stack_changes_only_network_binding() -> None:
    args = ("B0", "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"), "stock")
    ipv4 = lab.shairport_config(*args)
    dual = lab.shairport_config(*args, network_mode="dual_stack")
    assert 'address = "192.0.2.5";' in ipv4
    assert "address =" not in dual
    assert dual == ipv4.replace('  address = "192.0.2.5";\n', "")
    assert "use-ipv6=no" in lab.avahi_config()
    assert "publish-aaaa-on-ipv4=no" in lab.avahi_config()
    assert "use-ipv6=yes" in lab.avahi_config("dual_stack")
    assert "publish-aaaa-on-ipv4=yes" in lab.avahi_config("dual_stack")


def test_invalid_network_mode_fails_closed() -> None:
    with pytest.raises(ValueError):
        lab.shairport_config(
            "B0", "02AABBCCDDEE", "192.0.2.5", Path("/tmp/metadata"),
            "stock", "anything",
        )
    with pytest.raises(ValueError):
        lab.avahi_config("anything")


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
        f"{secret} TECNOHEAD_RC_RTSP_PEER_CLOSED\n"
        f"{secret} TECNOHEAD_RC_RTSP_THREAD_CLEANUP\n"
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
    assert counters.rc["TECNOHEAD_RC_RTSP_PEER_CLOSED"] == 1
    assert counters.rc["TECNOHEAD_RC_RTSP_THREAD_CLEANUP"] == 1
    assert counters.rc["TECNOHEAD_RC_SNAPSHOT_CLEARED"] == 1
    assert "TECNOHEAD_RC_GATE_MASK_999" not in counters.rc
    assert "TECNOHEAD_RC_LOOP_ALIVE_MASK_999" not in counters.rc
    assert secret not in capsys.readouterr().out
