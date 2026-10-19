from pathlib import Path


def test_entrypoints_do_not_log_capability_tokens_in_stream_urls():
    root = Path(__file__).resolve().parents[1]
    shell_entrypoint = (root / "run.sh").read_text(encoding="utf-8")
    python_entrypoint = (root / "app" / "main.py").read_text(encoding="utf-8")

    assert "--no-access-log" in shell_entrypoint
    assert "access_log=False" in python_entrypoint
