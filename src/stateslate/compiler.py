"""Pure story-order continuity compilation."""

from __future__ import annotations

from dataclasses import dataclass

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
