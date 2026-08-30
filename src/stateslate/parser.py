"""Strict JSON boundary for StateSlate projects."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import NoReturn, cast

from stateslate.errors import StateSlateError
from stateslate.models import Project, Scene, ShootPosition, Track, Transition

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TRACKS = 500
MAX_SCENES = 1_000
MAX_TRANSITIONS = 10_000
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def _fail(code: str, message: str, repair: str) -> NoReturn:
    raise StateSlateError(code, message, repair)


def _object(
    value: object,
    *,
    path: str,
    required: set[str],
    optional: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, dict):
        _fail("TYPE", f"{path} must be an object", "Use a JSON object at this location.")
    result = cast(dict[str, object], value)
    allowed = required | (optional or set())
    unknown = sorted(set(result) - allowed)
    if unknown:
        _fail(
            "UNKNOWN_KEY",
            f"{path} contains unknown key {unknown[0]!r}",
            "Remove the key or correct its spelling against docs/FORMAT.md.",
        )
    missing = sorted(required - set(result))
    if missing:
        _fail(
            "MISSING_KEY",
            f"{path} is missing required key {missing[0]!r}",
            "Add the required key described in docs/FORMAT.md.",
        )
    return result


def _array(value: object, *, path: str, minimum: int = 0, maximum: int) -> list[object]:
    if not isinstance(value, list):
        _fail("TYPE", f"{path} must be an array", "Use a JSON array at this location.")
    result = cast(list[object], value)
    if len(result) < minimum:
        _fail("EMPTY_LIST", f"{path} must not be empty", "Add at least one item.")
    if len(result) > maximum:
        _fail(
            "LIMIT",
            f"{path} has {len(result)} items; maximum is {maximum}",
            "Split the production into smaller StateSlate projects.",
        )
    return result


def _string(value: object, *, path: str, maximum: int) -> str:
    if not isinstance(value, str):
        _fail("TYPE", f"{path} must be a string", "Use a JSON string at this location.")
    if not value or value != value.strip():
        _fail(
            "STRING",
            f"{path} must be non-empty and have no edge whitespace",
            "Provide a concise value without leading or trailing spaces.",
        )
    if any(ord(character) < 32 for character in value):
        _fail(
            "STRING",
            f"{path} contains a control character",
            "Remove tabs, line breaks, nulls, and other control characters.",
        )
    if len(value) > maximum:
        _fail(
            "LIMIT",
            f"{path} is {len(value)} characters; maximum is {maximum}",
            "Shorten the value.",
        )
    return value


def _identifier(value: object, *, path: str) -> str:
    identifier = _string(value, path=path, maximum=64)
    if IDENTIFIER.fullmatch(identifier) is None:
        _fail(
            "IDENTIFIER",
            f"{path} has invalid identifier {identifier!r}",
            "Use ASCII letters, digits, dots, underscores, or hyphens.",
        )
    return identifier


def _positive_int(value: object, *, path: str) -> int:
    if type(value) is not int or not 1 <= value <= 1_000_000:
        _fail(
            "TYPE",
            f"{path} must be an integer from 1 to 1000000",
            "Use a positive JSON integer; booleans are not accepted.",
        )
    return value


def _parse_track(value: object, index: int) -> Track:
    path = f"tracks[{index}]"
    raw = _object(
        value,
        path=path,
        required={"id", "label", "category", "initial"},
    )
    return Track(
        id=_identifier(raw["id"], path=f"{path}.id"),
        label=_string(raw["label"], path=f"{path}.label", maximum=200),
        category=_string(raw["category"], path=f"{path}.category", maximum=64),
        initial=_string(raw["initial"], path=f"{path}.initial", maximum=120),
    )


def _parse_transition(value: object, *, scene_path: str, index: int) -> Transition:
    path = f"{scene_path}.transitions[{index}]"
    raw = _object(
        value,
        path=path,
        required={"track", "from", "to"},
        optional={"note"},
    )
    from_state = _string(raw["from"], path=f"{path}.from", maximum=120)
    to_state = _string(raw["to"], path=f"{path}.to", maximum=120)
    if from_state == to_state:
        _fail(
            "NOOP_TRANSITION",
            f"{path} does not change state {from_state!r}",
            "Remove the transition or give it a different 'to' state.",
        )
    note_value = raw.get("note", "")
    note = "" if note_value == "" else _string(note_value, path=f"{path}.note", maximum=500)
    return Transition(
        track=_identifier(raw["track"], path=f"{path}.track"),
        from_state=from_state,
        to_state=to_state,
        note=note,
    )


def _parse_scene(value: object, index: int, track_ids: set[str]) -> Scene:
    path = f"scenes[{index}]"
    raw = _object(
        value,
        path=path,
        required={"id", "title", "story_order", "shoot", "tracks"},
        optional={"expects", "transitions"},
    )
    shoot_raw = _object(
        raw["shoot"],
        path=f"{path}.shoot",
        required={"day", "order"},
    )
    raw_tracks = _array(raw["tracks"], path=f"{path}.tracks", minimum=1, maximum=MAX_TRACKS)
    scene_tracks = tuple(
        _identifier(track, path=f"{path}.tracks[{track_index}]")
        for track_index, track in enumerate(raw_tracks)
    )
    if len(set(scene_tracks)) != len(scene_tracks):
        _fail(
            "DUPLICATE_SCENE_TRACK",
            f"{path}.tracks contains a duplicate identifier",
            "List each continuity track once per scene.",
        )
    for track in scene_tracks:
        if track not in track_ids:
            _fail(
                "UNKNOWN_TRACK",
                f"{path}.tracks references unknown track {track!r}",
                "Declare the track at project level or remove it from the scene.",
            )

    expects_raw = raw.get("expects", {})
    if not isinstance(expects_raw, dict):
        _fail("TYPE", f"{path}.expects must be an object", "Map track identifiers to states.")
    expects_mapping = cast(dict[str, object], expects_raw)
    expects: list[tuple[str, str]] = []
    for track_value, state_value in expects_mapping.items():
        track = _identifier(track_value, path=f"{path}.expects key")
        if track not in track_ids:
            _fail(
                "UNKNOWN_TRACK",
                f"{path}.expects references unknown track {track!r}",
                "Declare the track at project level or remove the expectation.",
            )
        if track not in scene_tracks:
            _fail(
                "UNLISTED_TRACK",
                f"{path}.expects uses {track!r}, which is absent from scene tracks",
                "Add the track to the scene's 'tracks' array.",
            )
        expects.append((track, _string(state_value, path=f"{path}.expects.{track}", maximum=120)))

    transition_values = _array(
        raw.get("transitions", []),
        path=f"{path}.transitions",
        maximum=MAX_TRANSITIONS,
    )
    transitions = tuple(
        _parse_transition(item, scene_path=path, index=transition_index)
        for transition_index, item in enumerate(transition_values)
    )
    for transition in transitions:
        if transition.track not in track_ids:
            _fail(
                "UNKNOWN_TRACK",
                f"{path}.transitions references unknown track {transition.track!r}",
                "Declare the track at project level or remove the transition.",
            )
        if transition.track not in scene_tracks:
            _fail(
                "UNLISTED_TRACK",
                f"{path}.transitions uses {transition.track!r}, which is absent from scene tracks",
                "Add the track to the scene's 'tracks' array.",
            )

    return Scene(
        id=_identifier(raw["id"], path=f"{path}.id"),
        title=_string(raw["title"], path=f"{path}.title", maximum=200),
        story_order=_positive_int(raw["story_order"], path=f"{path}.story_order"),
        shoot=ShootPosition(
            day=_positive_int(shoot_raw["day"], path=f"{path}.shoot.day"),
            order=_positive_int(shoot_raw["order"], path=f"{path}.shoot.order"),
        ),
        tracks=scene_tracks,
        expects=tuple(sorted(expects)),
        transitions=transitions,
    )


def _reject_json_constant(value: str) -> NoReturn:
    _fail(
        "INVALID_JSON",
        f"non-standard JSON number {value!r} is not accepted",
        "Replace NaN or Infinity with a finite JSON value.",
    )


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(
                "DUPLICATE_KEY",
                f"JSON object contains duplicate key {key!r}",
                "Keep one value for the key; duplicate JSON keys are ambiguous.",
            )
        result[key] = value
    return result


def load_project(path: Path) -> Project:
    """Load and strictly validate a StateSlate project from a UTF-8 JSON file."""

    try:
        size = path.stat().st_size
    except OSError as error:
        _fail("FILE_READ", f"cannot inspect {path}: {error}", "Check the path and permissions.")
    if size > MAX_FILE_BYTES:
        _fail(
            "FILE_TOO_LARGE",
            f"{path} is {size} bytes; maximum is {MAX_FILE_BYTES}",
            "Split the production into smaller project files.",
        )
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        _fail("INVALID_UTF8", f"{path} is not valid UTF-8", "Save the project as UTF-8 JSON.")
    except OSError as error:
        _fail("FILE_READ", f"cannot read {path}: {error}", "Check the path and permissions.")
    try:
        decoded = json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_strict_json_object,
        )
    except json.JSONDecodeError as error:
        _fail(
            "INVALID_JSON",
            f"{path}:{error.lineno}:{error.colno}: {error.msg}",
            "Correct the JSON syntax and run validate again.",
        )
    except ValueError as error:
        _fail(
            "INVALID_JSON",
            f"{path} contains a JSON value Python cannot represent safely: {error}",
            "Replace the oversized numeric value with a bounded integer or string.",
        )

    raw = _object(
        decoded,
        path="$",
        required={"schema_version", "title", "tracks", "scenes"},
    )
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        _fail(
            "SCHEMA_VERSION",
            "$.schema_version must be the integer 1",
            "Use schema_version 1 or a compatible StateSlate release.",
        )
    track_values = _array(raw["tracks"], path="$.tracks", minimum=1, maximum=MAX_TRACKS)
    tracks = tuple(_parse_track(item, index) for index, item in enumerate(track_values))
    track_ids: set[str] = set()
    for track in tracks:
        if track.id in track_ids:
            _fail(
                "DUPLICATE_TRACK",
                f"track identifier {track.id!r} appears more than once",
                "Give every track a unique identifier.",
            )
        track_ids.add(track.id)

    scene_values = _array(raw["scenes"], path="$.scenes", minimum=1, maximum=MAX_SCENES)
    scenes = tuple(_parse_scene(item, index, track_ids) for index, item in enumerate(scene_values))
    if sum(len(scene.transitions) for scene in scenes) > MAX_TRANSITIONS:
        _fail(
            "LIMIT",
            f"project has more than {MAX_TRANSITIONS} transitions",
            "Split the production into smaller StateSlate projects.",
        )

    scene_ids: set[str] = set()
    story_orders: set[int] = set()
    shoot_positions: set[ShootPosition] = set()
    for scene in scenes:
        if scene.id in scene_ids:
            _fail(
                "DUPLICATE_SCENE",
                f"scene identifier {scene.id!r} appears more than once",
                "Give every scene a unique identifier.",
            )
        if scene.story_order in story_orders:
            _fail(
                "DUPLICATE_STORY_ORDER",
                f"story order {scene.story_order} appears more than once",
                "Assign every scene a unique story_order value.",
            )
        if scene.shoot in shoot_positions:
            _fail(
                "DUPLICATE_SHOOT_POSITION",
                f"shoot position day {scene.shoot.day}, order {scene.shoot.order} is duplicated",
                "Assign every scene a unique shoot day/order pair.",
            )
        scene_ids.add(scene.id)
        story_orders.add(scene.story_order)
        shoot_positions.add(scene.shoot)

    return Project(
        schema_version=1,
        title=_string(raw["title"], path="$.title", maximum=200),
        tracks=tracks,
        scenes=scenes,
    )
