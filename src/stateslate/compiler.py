"""Pure story-order continuity compilation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from stateslate.errors import StateSlateError
from stateslate.models import Project, ShootPosition, Transition


@dataclass(frozen=True, slots=True)
class StoryScene:
    id: str
    title: str
    story_order: int
    shoot: ShootPosition
    entry_states: tuple[tuple[str, str], ...]
    exit_states: tuple[tuple[str, str], ...]
    transitions: tuple[Transition, ...]


@dataclass(frozen=True, slots=True)
class StoryTimeline:
    project: Project
    scenes: tuple[StoryScene, ...]
    final_states: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ShootAction:
    kind: Literal["prepare", "reset"]
    track: str
    from_state: str | None
    to_state: str
    source_scene: str | None


@dataclass(frozen=True, slots=True)
class Reference:
    track: str
    status: Literal["initial", "available", "future"]
    source_scene: str | None
    day_gap: int | None


@dataclass(frozen=True, slots=True)
class Risk:
    code: Literal["FUTURE_REFERENCE", "LONG_REFERENCE_GAP"]
    severity: Literal["high", "medium"]
    scene: str
    track: str
    source_scene: str
    day_gap: int


@dataclass(frozen=True, slots=True)
class ShootScene:
    id: str
    title: str
    story_order: int
    shoot: ShootPosition
    setup_states: tuple[tuple[str, str], ...]
    exit_states: tuple[tuple[str, str], ...]
    actions: tuple[ShootAction, ...]
    references: tuple[Reference, ...]


@dataclass(frozen=True, slots=True)
class Summary:
    scene_count: int
    track_count: int
    prepare_count: int
    reset_count: int
    high_risk_count: int
    medium_risk_count: int


@dataclass(frozen=True, slots=True)
class Compilation:
    timeline: StoryTimeline
    shoot_scenes: tuple[ShootScene, ...]
    risks: tuple[Risk, ...]
    summary: Summary


def propagate_story(project: Project) -> StoryTimeline:
    """Propagate declared transitions using story order as the authority."""

    current = {track.id: track.initial for track in project.tracks}
    compiled: list[StoryScene] = []
    for scene in sorted(project.scenes, key=lambda item: item.story_order):
        for track, expected in scene.expects:
            actual = current[track]
            if actual != expected:
                raise StateSlateError(
                    "EXPECTATION_MISMATCH",
                    f"scene {scene.id!r} expects {track!r} to be {expected!r}; "
                    f"story state is {actual!r}",
                    "Correct the expectation or add the missing transition to an earlier scene.",
                )

        entry_states = tuple((track, current[track]) for track in scene.tracks)
        for transition in scene.transitions:
            actual = current[transition.track]
            if actual != transition.from_state:
                raise StateSlateError(
                    "TRANSITION_MISMATCH",
                    f"scene {scene.id!r} transition for {transition.track!r} starts from "
                    f"{transition.from_state!r}; story state is {actual!r}",
                    "Correct 'from' or add the missing transition to an earlier scene.",
                )
            current[transition.track] = transition.to_state
        exit_states = tuple((track, current[track]) for track in scene.tracks)
        compiled.append(
            StoryScene(
                id=scene.id,
                title=scene.title,
                story_order=scene.story_order,
                shoot=scene.shoot,
                entry_states=entry_states,
                exit_states=exit_states,
                transitions=scene.transitions,
            )
        )

    return StoryTimeline(
        project=project,
        scenes=tuple(compiled),
        final_states=tuple((track.id, current[track.id]) for track in project.tracks),
    )


def compile_project(project: Project, *, risk_days: int = 3) -> Compilation:
    """Compile story states into shoot-order preparations and reference risks."""

    if type(risk_days) is not int or risk_days < 1:
        raise StateSlateError(
            "RISK_DAYS",
            "risk_days must be a positive integer",
            "Use a whole number of at least 1 day.",
        )
    timeline = propagate_story(project)
    previous_story_use: dict[tuple[str, str], StoryScene | None] = {}
    last_use: dict[str, StoryScene] = {}
    for scene in timeline.scenes:
        for track, _state in scene.entry_states:
            previous_story_use[(scene.id, track)] = last_use.get(track)
            last_use[track] = scene

    last_shot_state: dict[str, tuple[str, str]] = {}
    shoot_scenes: list[ShootScene] = []
    risks: list[Risk] = []
    for scene in sorted(timeline.scenes, key=lambda item: item.shoot):
        actions: list[ShootAction] = []
        references: list[Reference] = []
        for track, required_state in scene.entry_states:
            previous_shot = last_shot_state.get(track)
            if previous_shot is None:
                actions.append(
                    ShootAction(
                        kind="prepare",
                        track=track,
                        from_state=None,
                        to_state=required_state,
                        source_scene=None,
                    )
                )
            elif previous_shot[0] != required_state:
                actions.append(
                    ShootAction(
                        kind="reset",
                        track=track,
                        from_state=previous_shot[0],
                        to_state=required_state,
                        source_scene=previous_shot[1],
                    )
                )

            story_source = previous_story_use[(scene.id, track)]
            if story_source is None:
                references.append(
                    Reference(
                        track=track,
                        status="initial",
                        source_scene=None,
                        day_gap=None,
                    )
                )
            elif story_source.shoot > scene.shoot:
                day_gap = story_source.shoot.day - scene.shoot.day
                references.append(
                    Reference(
                        track=track,
                        status="future",
                        source_scene=story_source.id,
                        day_gap=day_gap,
                    )
                )
                risks.append(
                    Risk(
                        code="FUTURE_REFERENCE",
                        severity="high",
                        scene=scene.id,
                        track=track,
                        source_scene=story_source.id,
                        day_gap=day_gap,
                    )
                )
            else:
                day_gap = scene.shoot.day - story_source.shoot.day
                references.append(
                    Reference(
                        track=track,
                        status="available",
                        source_scene=story_source.id,
                        day_gap=day_gap,
                    )
                )
                if day_gap >= risk_days:
                    risks.append(
                        Risk(
                            code="LONG_REFERENCE_GAP",
                            severity="medium",
                            scene=scene.id,
                            track=track,
                            source_scene=story_source.id,
                            day_gap=day_gap,
                        )
                    )

        for track, state in scene.exit_states:
            last_shot_state[track] = (state, scene.id)
        shoot_scenes.append(
            ShootScene(
                id=scene.id,
                title=scene.title,
                story_order=scene.story_order,
                shoot=scene.shoot,
                setup_states=scene.entry_states,
                exit_states=scene.exit_states,
                actions=tuple(actions),
                references=tuple(references),
            )
        )

    all_actions = tuple(action for scene in shoot_scenes for action in scene.actions)
    return Compilation(
        timeline=timeline,
        shoot_scenes=tuple(shoot_scenes),
        risks=tuple(risks),
        summary=Summary(
            scene_count=len(project.scenes),
            track_count=len(project.tracks),
            prepare_count=sum(action.kind == "prepare" for action in all_actions),
            reset_count=sum(action.kind == "reset" for action in all_actions),
            high_risk_count=sum(risk.severity == "high" for risk in risks),
            medium_risk_count=sum(risk.severity == "medium" for risk in risks),
        ),
    )
