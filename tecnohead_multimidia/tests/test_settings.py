from __future__ import annotations

from app.settings import load_settings


def test_mediaremote_probe_defaults_off_when_options_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("APPLE_MEDIAREMOTE_EXPERIMENTAL", raising=False)
    assert load_settings().apple_mediaremote_experimental is False


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
