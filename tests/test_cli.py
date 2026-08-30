from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def project_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "title": "Paper Moon",
        "tracks": [
            {
                "id": "jane.jacket",
                "label": "Jane's jacket",
                "category": "wardrobe",
                "initial": "clean_buttoned",
            }
        ],
        "scenes": [
            {
                "id": "S01",
                "title": "Before",
                "story_order": 1,
                "shoot": {"day": 3, "order": 1},
                "tracks": ["jane.jacket"],
                "transitions": [
                    {
                        "track": "jane.jacket",
                        "from": "clean_buttoned",
                        "to": "wet_open",
                    }
                ],
            },
            {
                "id": "S02",
                "title": "After",
                "story_order": 2,
                "shoot": {"day": 1, "order": 1},
                "tracks": ["jane.jacket"],
                "expects": {"jane.jacket": "wet_open"},
                "transitions": [],
            },
        ],
    }


def write_project(path: Path, raw: dict[str, object] | None = None) -> Path:
    path.write_text(json.dumps(raw or project_data()), encoding="utf-8")
    return path


def run_cli(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "stateslate", *arguments],
        check=False,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def test_version_reports_package_version() -> None:
    result = run_cli(["--version"])

    assert result.returncode == 0
    assert result.stdout.strip() == "stateslate 0.1.0"
    assert result.stderr == ""


def test_validate_checks_semantics_without_writing(tmp_path: Path) -> None:
    project = write_project(tmp_path / "project.json")

    result = run_cli(["validate", str(project)])

    assert result.returncode == 0
    assert "VALID" in result.stdout
    assert not list(tmp_path.glob(".*stateslate*"))


def test_compile_writes_all_artifacts_and_summary(tmp_path: Path) -> None:
    project = write_project(tmp_path / "project.json")
    output = tmp_path / "report"

    result = run_cli(["compile", str(project), "--out", str(output)])

    assert result.returncode == 0
    assert set(path.name for path in output.iterdir()) == {
        "continuity.json",
        "report.html",
        "reset-checklist.md",
        "shoot-plan.csv",
        "timeline.svg",
    }
    assert "2 scenes" in result.stdout
    assert "1 high risk" in result.stdout


def test_compile_risk_gate_returns_one_after_writing_evidence(tmp_path: Path) -> None:
    project = write_project(tmp_path / "project.json")
    output = tmp_path / "report"

    result = run_cli(["compile", str(project), "--out", str(output), "--fail-on", "high"])

    assert result.returncode == 1
    assert output.joinpath("continuity.json").is_file()
    assert "RISK GATE" in result.stderr


def test_invalid_transition_returns_two_without_output_or_traceback(tmp_path: Path) -> None:
    raw = project_data()
    scenes = raw["scenes"]
    assert isinstance(scenes, list)
    first = scenes[0]
    assert isinstance(first, dict)
    transitions = first["transitions"]
    assert isinstance(transitions, list)
    transition = transitions[0]
    assert isinstance(transition, dict)
    transition["from"] = "wrong"
    project = write_project(tmp_path / "invalid.json", raw)
    output = tmp_path / "report"

    result = run_cli(["compile", str(project), "--out", str(output)])

    assert result.returncode == 2
    assert "TRANSITION_MISMATCH" in result.stderr
    assert "Repair:" in result.stderr
    assert "Traceback" not in result.stderr
    assert not output.exists()


def test_existing_output_is_refused_and_preserved(tmp_path: Path) -> None:
    project = write_project(tmp_path / "project.json")
    output = tmp_path / "report"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("owner data", encoding="utf-8")

    result = run_cli(["compile", str(project), "--out", str(output)])

    assert result.returncode == 2
    assert "OUTPUT_EXISTS" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "owner data"
    assert set(output.iterdir()) == {sentinel}


def test_demo_compiles_embedded_project(tmp_path: Path) -> None:
    output = tmp_path / "demo"

    result = run_cli(["demo", "--out", str(output)])

    assert result.returncode == 0
    report = json.loads(output.joinpath("continuity.json").read_text(encoding="utf-8"))
    assert report["summary"]["scene_count"] >= 3
    assert report["summary"]["reset_count"] >= 1
    assert report["summary"]["high_risk_count"] >= 1
    assert report["summary"]["medium_risk_count"] >= 1


def test_invalid_risk_days_is_cli_error_without_output(tmp_path: Path) -> None:
    project = write_project(tmp_path / "project.json")
    output = tmp_path / "report"

    result = run_cli(["compile", str(project), "--out", str(output), "--risk-days", "0"])

    assert result.returncode == 2
    assert "positive integer" in result.stderr
    assert not output.exists()
