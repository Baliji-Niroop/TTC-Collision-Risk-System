"""Tests for replay output handling."""

from pathlib import Path

from src.replay_runner import _atomic_write


def test_atomic_write_retries_transient_permission_error(tmp_path, monkeypatch):
    destination = tmp_path / "live_data.txt"
    original_replace = Path.replace
    calls = 0

    def replace_once_after_lock(path, target):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError("temporary file lock")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", replace_once_after_lock)

    _atomic_write(destination, "packet")

    assert calls == 2
    assert destination.read_text(encoding="utf-8") == "packet"
    assert not destination.with_suffix(".tmp").exists()
