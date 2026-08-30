from __future__ import annotations

import json
from pathlib import Path

from stateslate.compiler import Compilation, compile_project
from stateslate.parser import load_project


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
            },
            {
                "id": "letter.seal",
                "label": "Letter seal",
                "category": "props",
                "initial": "sealed",
            },
        ],
        "scenes": [
            {
                "id": "S01",
                "title": "The letter arrives",
                "story_order": 10,
                "shoot": {"day": 3, "order": 2},
                "tracks": ["jane.jacket", "letter.seal"],
                "transitions": [{"track": "letter.seal", "from": "sealed", "to": "opened"}],
            },
            {
                "id": "S02",
                "title": "After the storm",
                "story_order": 20,
                "shoot": {"day": 1, "order": 1},
                "tracks": ["jane.jacket", "letter.seal"],
                "transitions": [
                    {
                        "track": "jane.jacket",
                        "from": "clean_buttoned",
                        "to": "wet_open",
                    }
                ],
            },
            {
                "id": "S03",
                "title": "Morning after",
                "story_order": 30,
                "shoot": {"day": 5, "order": 1},
                "tracks": ["jane.jacket"],
                "expects": {"jane.jacket": "wet_open"},
                "transitions": [],
            },
        ],
    }


def compile_data(tmp_path: Path, raw: dict[str, object], risk_days: int = 3) -> Compilation:
    path = tmp_path / "project.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return compile_project(load_project(path), risk_days=risk_days)


def test_compile_project_projects_story_states_into_shoot_order(tmp_path: Path) -> None:
    compilation = compile_data(tmp_path, project_data())

    assert [scene.id for scene in compilation.shoot_scenes] == ["S02", "S01", "S03"]
    assert dict(compilation.shoot_scenes[0].setup_states) == {
        "jane.jacket": "clean_buttoned",
        "letter.seal": "opened",
    }
    assert dict(compilation.shoot_scenes[1].setup_states) == {
        "jane.jacket": "clean_buttoned",
        "letter.seal": "sealed",
    }


def test_compile_project_emits_prepare_then_exact_reset_actions(tmp_path: Path) -> None:
    compilation = compile_data(tmp_path, project_data())

    first_actions = compilation.shoot_scenes[0].actions
    assert [
        (action.kind, action.track, action.from_state, action.to_state) for action in first_actions
    ] == [
        ("prepare", "jane.jacket", None, "clean_buttoned"),
        ("prepare", "letter.seal", None, "opened"),
    ]
    second_actions = compilation.shoot_scenes[1].actions
    assert [
        (action.kind, action.track, action.from_state, action.to_state) for action in second_actions
    ] == [
        ("reset", "jane.jacket", "wet_open", "clean_buttoned"),
        ("reset", "letter.seal", "opened", "sealed"),
    ]
    assert all(action.source_scene == "S02" for action in second_actions)


def test_compile_project_marks_story_reference_scheduled_in_future_as_high_risk(
    tmp_path: Path,
) -> None:
    compilation = compile_data(tmp_path, project_data())

    first_references = compilation.shoot_scenes[0].references
    assert [
        (reference.track, reference.status, reference.source_scene)
        for reference in first_references
    ] == [
        ("jane.jacket", "future", "S01"),
        ("letter.seal", "future", "S01"),
    ]
    assert {risk.code for risk in compilation.risks if risk.scene == "S02"} == {"FUTURE_REFERENCE"}
    assert all(risk.severity == "high" for risk in compilation.risks if risk.scene == "S02")


def test_compile_project_marks_available_reference_after_threshold_as_medium(
    tmp_path: Path,
) -> None:
    compilation = compile_data(tmp_path, project_data(), risk_days=3)

    third_reference = compilation.shoot_scenes[2].references[0]
    assert third_reference.status == "available"
    assert third_reference.source_scene == "S02"
    assert third_reference.day_gap == 4
    risk = next(risk for risk in compilation.risks if risk.scene == "S03")
    assert (risk.code, risk.severity, risk.day_gap) == ("LONG_REFERENCE_GAP", "medium", 4)


def test_compile_project_does_not_emit_medium_risk_below_threshold(tmp_path: Path) -> None:
    compilation = compile_data(tmp_path, project_data(), risk_days=5)

    assert not any(risk.scene == "S03" for risk in compilation.risks)


def test_compile_project_summary_counts_actions_and_risks(tmp_path: Path) -> None:
    compilation = compile_data(tmp_path, project_data())

    assert compilation.summary.scene_count == 3
    assert compilation.summary.track_count == 2
    assert compilation.summary.prepare_count == 2
    assert compilation.summary.reset_count == 3
    assert compilation.summary.high_risk_count == 2
    assert compilation.summary.medium_risk_count == 1
