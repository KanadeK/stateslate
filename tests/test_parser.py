from __future__ import annotations

import json
from pathlib import Path

import pytest

from stateslate.errors import StateSlateError
from stateslate.parser import load_project


def valid_project() -> dict[str, object]:
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
                "story_order": 1,
                "shoot": {"day": 3, "order": 2},
                "tracks": ["jane.jacket", "letter.seal"],
                "expects": {"letter.seal": "sealed"},
                "transitions": [
                    {
                        "track": "letter.seal",
                        "from": "sealed",
                        "to": "opened",
                        "note": "Jane opens the letter on camera",
                    }
                ],
            },
            {
                "id": "S02",
                "title": "After the storm",
                "story_order": 2,
                "shoot": {"day": 1, "order": 1},
                "tracks": ["jane.jacket", "letter.seal"],
                "transitions": [],
            },
        ],
    }


def write_project(path: Path, project: dict[str, object]) -> Path:
    path.write_text(json.dumps(project), encoding="utf-8")
    return path


def test_load_project_builds_validated_model(tmp_path: Path) -> None:
    project = load_project(write_project(tmp_path / "project.json", valid_project()))

    assert project.title == "Paper Moon"
    assert [track.id for track in project.tracks] == ["jane.jacket", "letter.seal"]
    assert project.scenes[0].transitions[0].to_state == "opened"
    assert project.scenes[1].shoot.day == 1


def test_load_project_rejects_unknown_top_level_key(tmp_path: Path) -> None:
    raw = valid_project()
    raw["upload_url"] = "https://example.invalid"

    with pytest.raises(StateSlateError, match=r"UNKNOWN_KEY.*upload_url"):
        load_project(write_project(tmp_path / "project.json", raw))


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda raw: raw["tracks"].append(raw["tracks"][0]), "DUPLICATE_TRACK"),
        (lambda raw: raw["scenes"].append(raw["scenes"][0]), "DUPLICATE_SCENE"),
    ],
)
def test_load_project_rejects_duplicate_identifiers(
    tmp_path: Path, mutation: object, code: str
) -> None:
    raw = valid_project()
    assert callable(mutation)
    mutation(raw)

    with pytest.raises(StateSlateError, match=code):
        load_project(write_project(tmp_path / "project.json", raw))


def test_load_project_rejects_duplicate_story_and_shoot_positions(tmp_path: Path) -> None:
    raw = valid_project()
    scenes = raw["scenes"]
    assert isinstance(scenes, list)
    second = scenes[1]
    assert isinstance(second, dict)
    second["story_order"] = 1
    second["shoot"] = {"day": 3, "order": 2}

    with pytest.raises(StateSlateError, match="DUPLICATE_STORY_ORDER"):
        load_project(write_project(tmp_path / "project.json", raw))


def test_load_project_rejects_unknown_or_unlisted_transition_track(tmp_path: Path) -> None:
    raw = valid_project()
    scenes = raw["scenes"]
    assert isinstance(scenes, list)
    first = scenes[0]
    assert isinstance(first, dict)
    first["transitions"] = [{"track": "ghost.hat", "from": "on", "to": "off"}]

    with pytest.raises(StateSlateError, match="UNKNOWN_TRACK.*ghost.hat"):
        load_project(write_project(tmp_path / "project.json", raw))


def test_load_project_rejects_boolean_where_integer_is_required(tmp_path: Path) -> None:
    raw = valid_project()
    scenes = raw["scenes"]
    assert isinstance(scenes, list)
    first = scenes[0]
    assert isinstance(first, dict)
    first["story_order"] = True

    with pytest.raises(StateSlateError, match="TYPE"):
        load_project(write_project(tmp_path / "project.json", raw))


def test_load_project_rejects_oversized_file(tmp_path: Path) -> None:
    path = tmp_path / "project.json"
    path.write_bytes(b" " * (2 * 1024 * 1024 + 1))

    with pytest.raises(StateSlateError, match="FILE_TOO_LARGE"):
        load_project(path)


def test_load_project_reports_invalid_utf8_and_json(tmp_path: Path) -> None:
    utf8_path = tmp_path / "utf8.json"
    utf8_path.write_bytes(b"\xff")
    with pytest.raises(StateSlateError, match="INVALID_UTF8"):
        load_project(utf8_path)

    json_path = tmp_path / "syntax.json"
    json_path.write_text("{", encoding="utf-8")
    with pytest.raises(StateSlateError, match="INVALID_JSON"):
        load_project(json_path)
