from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from stateslate.compiler import Compilation, compile_project
from stateslate.parser import load_project
from stateslate.render import render_artifacts


def compilation(tmp_path: Path) -> Compilation:
    raw = {
        "schema_version": 1,
        "title": "Paper <Moon>",
        "tracks": [
            {
                "id": "jane.jacket",
                "label": "=Jane's | jacket",
                "category": "wardrobe",
                "initial": "clean_buttoned",
            },
            {
                "id": "letter.seal",
                "label": "Letter <seal>",
                "category": "props",
                "initial": "sealed",
            },
        ],
        "scenes": [
            {
                "id": "S01",
                "title": "The <letter> arrives",
                "story_order": 1,
                "shoot": {"day": 3, "order": 1},
                "tracks": ["jane.jacket", "letter.seal"],
                "transitions": [
                    {
                        "track": "letter.seal",
                        "from": "sealed",
                        "to": "+opened",
                        "note": "Open <on camera>",
                    }
                ],
            },
            {
                "id": "S02",
                "title": "After the storm",
                "story_order": 2,
                "shoot": {"day": 1, "order": 1},
                "tracks": ["jane.jacket", "letter.seal"],
                "expects": {"letter.seal": "+opened"},
                "transitions": [
                    {
                        "track": "jane.jacket",
                        "from": "clean_buttoned",
                        "to": "wet_open",
                    }
                ],
            },
        ],
    }
    path = tmp_path / "project.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return compile_project(load_project(path), risk_days=3)


def test_render_artifacts_returns_the_complete_deterministic_set(tmp_path: Path) -> None:
    compiled = compilation(tmp_path)

    first = render_artifacts(compiled)
    second = render_artifacts(compiled)

    assert first == second
    assert set(first) == {
        "continuity.json",
        "report.html",
        "reset-checklist.md",
        "shoot-plan.csv",
        "timeline.svg",
    }
    assert all(text.endswith("\n") for text in first.values())
    assert all(line == line.rstrip() for text in first.values() for line in text.splitlines())


def test_json_report_preserves_values_and_one_compiled_truth(tmp_path: Path) -> None:
    artifacts = render_artifacts(compilation(tmp_path))
    report = json.loads(artifacts["continuity.json"])

    assert report["schema_version"] == 1
    assert report["generator"] == {"name": "stateslate", "version": "0.1.0"}
    assert report["project"]["title"] == "Paper <Moon>"
    assert report["summary"] == {
        "high_risk_count": 2,
        "medium_risk_count": 0,
        "prepare_count": 2,
        "reset_count": 2,
        "scene_count": 2,
        "track_count": 2,
    }
    assert report["story_scenes"][0]["exit_states"]["letter.seal"] == "+opened"
    assert report["shoot_scenes"][0]["id"] == "S02"
    assert len(report["risks"]) == 2


def test_csv_neutralizes_formula_cells_without_changing_json(tmp_path: Path) -> None:
    artifacts = render_artifacts(compilation(tmp_path))
    rows = list(csv.DictReader(io.StringIO(artifacts["shoot-plan.csv"])))

    letter_row = next(
        row for row in rows if row["scene_id"] == "S02" and row["track_id"] == "letter.seal"
    )
    assert letter_row["setup_state"] == "'+opened"
    assert letter_row["track_label"] == "Letter <seal>"
    jacket_row = next(row for row in rows if row["track_id"] == "jane.jacket")
    assert jacket_row["track_label"] == "'=Jane's | jacket"
    report = json.loads(artifacts["continuity.json"])
    assert report["tracks"][0]["label"] == "=Jane's | jacket"


def test_html_and_svg_escape_project_text_and_contain_no_script(tmp_path: Path) -> None:
    artifacts = render_artifacts(compilation(tmp_path))
    html = artifacts["report.html"]
    svg = artifacts["timeline.svg"]

    assert "Paper &lt;Moon&gt;" in html
    assert "The &lt;letter&gt; arrives" in html
    assert "Paper <Moon>" not in html
    assert "<script" not in html.lower()
    assert "Paper &lt;Moon&gt;" in svg
    assert "The &lt;letter&gt; arrives" in svg
    assert '<svg xmlns="http://www.w3.org/2000/svg" role="img"' in svg
    assert "<title>" in svg and "<desc>" in svg


def test_markdown_contains_shoot_order_resets_and_escapes_table_pipes(tmp_path: Path) -> None:
    markdown = render_artifacts(compilation(tmp_path))["reset-checklist.md"]

    assert "Day 1 / 1 — S02" in markdown
    assert "Day 3 / 1 — S01" in markdown
    assert "Reset `letter.seal`: `+opened` → `sealed`" in markdown
    assert "=Jane's \\| jacket" in markdown
    assert "FUTURE_REFERENCE" in markdown
