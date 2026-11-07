"""Tests for the project-wide verification contract."""

from pathlib import Path

from src import main


def test_quality_gate_runs_lint_after_runtime_checks(monkeypatch):
    commands = []

    class Result:
        returncode = 0

    def fake_run(command):
        commands.append(command)
        return Result()

    monkeypatch.setattr(main.subprocess, "run", fake_run)

    main.run_checks()

    assert commands[-1] == [main.sys.executable, "-m", "flake8", "src", "ml", "validation", "bridge", "tests"]


def test_firmware_has_one_active_ttc_implementation():
    root = Path(__file__).parents[1]

    assert (root / "firmware" / "ml" / "ttc_engine.h").exists()
    assert not (root / "firmware" / "ttc_calculator.h").exists()
