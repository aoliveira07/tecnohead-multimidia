from __future__ import annotations

from app.settings import load_settings


def test_mediaremote_probe_defaults_off_when_options_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("APPLE_MEDIAREMOTE_EXPERIMENTAL", raising=False)
    assert load_settings().apple_mediaremote_experimental is False
    assert load_settings().apple_legacy_metadata_zone == "off"
    assert load_settings().apple_feature_comparison_zone == "off"
    assert load_settings().apple_mediaremote_forward_zone == "off"


def test_mediaremote_probe_reads_haos_option(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("APPLE_MEDIAREMOTE_EXPERIMENTAL", raising=False)
    (tmp_path / "options.json").write_text('{"apple_mediaremote_experimental": true}', encoding="utf-8")
    assert load_settings().apple_mediaremote_experimental is True


def test_mediaremote_probe_requires_boolean_true_and_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("APPLE_MEDIAREMOTE_EXPERIMENTAL", raising=False)
    options = tmp_path / "options.json"
    for content in ('{"apple_mediaremote_experimental": "true"}', "{bad json", "[]"):
        options.write_text(content, encoding="utf-8")
        assert load_settings().apple_mediaremote_experimental is False


def test_mediaremote_probe_environment_override_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    (tmp_path / "options.json").write_text('{"apple_mediaremote_experimental": true}', encoding="utf-8")
    monkeypatch.setenv("APPLE_MEDIAREMOTE_EXPERIMENTAL", "false")
    assert load_settings().apple_mediaremote_experimental is False


def test_legacy_metadata_option_allows_only_one_known_zone(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    options = tmp_path / "options.json"
    for value in ("kitchen", "pool"):
        options.write_text('{"apple_legacy_metadata_zone": "' + value + '"}', encoding="utf-8")
        assert load_settings().apple_legacy_metadata_zone == value
    for content in (
        '{"apple_legacy_metadata_zone": "both"}',
        '{"apple_legacy_metadata_zone": ["kitchen", "pool"]}',
        '{"apple_legacy_metadata_zone": true}',
        "{bad json",
    ):
        options.write_text(content, encoding="utf-8")
        assert load_settings().apple_legacy_metadata_zone == "off"


def test_feature_comparison_is_opt_in_for_kitchen_only(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    options = tmp_path / "options.json"
    options.write_text('{"apple_feature_comparison_zone": "kitchen"}', encoding="utf-8")
    assert load_settings().apple_feature_comparison_zone == "kitchen"
    for content in (
        '{"apple_feature_comparison_zone": "pool"}',
        '{"apple_feature_comparison_zone": "both"}',
        '{"apple_feature_comparison_zone": true}',
        "{bad json",
    ):
        options.write_text(content, encoding="utf-8")
        assert load_settings().apple_feature_comparison_zone == "off"


def test_mediaremote_forward_is_opt_in_for_kitchen_only(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    options = tmp_path / "options.json"
    options.write_text('{"apple_mediaremote_forward_zone": "kitchen"}', encoding="utf-8")
    assert load_settings().apple_mediaremote_forward_zone == "kitchen"
    for content in (
        '{"apple_mediaremote_forward_zone": "pool"}',
        '{"apple_mediaremote_forward_zone": "both"}',
        '{"apple_mediaremote_forward_zone": true}',
        "{bad json",
    ):
        options.write_text(content, encoding="utf-8")
        assert load_settings().apple_mediaremote_forward_zone == "off"
