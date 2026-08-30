from __future__ import annotations

import json
from pathlib import Path

import pytest

from stateslate.compiler import propagate_story
from stateslate.errors import StateSlateError
from stateslate.models import Project
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
                "id": "S02",
                "title": "After the storm",
                "story_order": 20,
                "shoot": {"day": 1, "order": 1},
                "tracks": ["jane.jacket", "letter.seal"],
                "expects": {"letter.seal": "opened"},
                "transitions": [
                    {
                        "track": "jane.jacket",
                        "from": "clean_buttoned",
                        "to": "wet_open",
                    }
                ],
            },
            {
                "id": "S01",
                "title": "The letter arrives",
                "story_order": 10,
                "shoot": {"day": 3, "order": 2},
                "tracks": ["jane.jacket", "letter.seal"],
                "expects": {"letter.seal": "sealed"},
                "transitions": [
                    {
                        "track": "letter.seal",
                        "from": "sealed",
                        "to": "opened",
                        "note": "Jane opens it",
                    }
                ],
            },
        ],
    }


def load(tmp_path: Path, raw: dict[str, object]) -> Project:
    path = tmp_path / "project.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return load_project(path)


def test_propagate_story_orders_scenes_and_calculates_entry_exit_states(tmp_path: Path) -> None:
    timeline = propagate_story(load(tmp_path, project_data()))

    assert [scene.id for scene in timeline.scenes] == ["S01", "S02"]
    first = timeline.scenes[0]
    second = timeline.scenes[1]
    assert dict(first.entry_states) == {
        "jane.jacket": "clean_buttoned",
        "letter.seal": "sealed",
    }
    assert dict(first.exit_states)["letter.seal"] == "opened"
    assert dict(second.entry_states)["letter.seal"] == "opened"
    assert dict(second.exit_states)["jane.jacket"] == "wet_open"
    assert dict(timeline.final_states) == {
        "jane.jacket": "wet_open",
        "letter.seal": "opened",
    }


def test_propagate_story_applies_multiple_transitions_in_declared_order(tmp_path: Path) -> None:
    raw = project_data()
    scenes = raw["scenes"]
    assert isinstance(scenes, list)
    first_in_story = scenes[1]
    assert isinstance(first_in_story, dict)
    first_in_story["transitions"] = [
        {"track": "letter.seal", "from": "sealed", "to": "cracked"},
        {"track": "letter.seal", "from": "cracked", "to": "opened"},
    ]

    timeline = propagate_story(load(tmp_path, raw))

    assert dict(timeline.scenes[0].exit_states)["letter.seal"] == "opened"


def test_propagate_story_rejects_false_scene_expectation(tmp_path: Path) -> None:
    raw = project_data()
    scenes = raw["scenes"]
    assert isinstance(scenes, list)
    second_in_story = scenes[0]
    assert isinstance(second_in_story, dict)
    second_in_story["expects"] = {"letter.seal": "sealed"}

    with pytest.raises(StateSlateError, match=r"EXPECTATION_MISMATCH.*S02.*letter.seal"):
        propagate_story(load(tmp_path, raw))


def test_propagate_story_rejects_transition_from_mismatch(tmp_path: Path) -> None:
    raw = project_data()
    scenes = raw["scenes"]
    assert isinstance(scenes, list)
    first_in_story = scenes[1]
    assert isinstance(first_in_story, dict)
    transitions = first_in_story["transitions"]
    assert isinstance(transitions, list)
    transition = transitions[0]
    assert isinstance(transition, dict)
    transition["from"] = "already_open"

    with pytest.raises(StateSlateError, match=r"TRANSITION_MISMATCH.*S01.*letter.seal"):
        propagate_story(load(tmp_path, raw))


def test_propagate_story_only_emits_tracks_relevant_to_each_scene(tmp_path: Path) -> None:
    raw = project_data()
    scenes = raw["scenes"]
    assert isinstance(scenes, list)
    second_in_story = scenes[0]
    assert isinstance(second_in_story, dict)
    second_in_story["tracks"] = ["jane.jacket"]
    second_in_story["expects"] = {}

    timeline = propagate_story(load(tmp_path, raw))

    assert dict(timeline.scenes[1].entry_states) == {"jane.jacket": "clean_buttoned"}
    assert dict(timeline.final_states)["letter.seal"] == "opened"
