"""Validated StateSlate input models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Track:
    id: str
    label: str
    category: str
    initial: str


@dataclass(frozen=True, slots=True, order=True)
class ShootPosition:
    day: int
    order: int


@dataclass(frozen=True, slots=True)
class Transition:
    track: str
    from_state: str
    to_state: str
    note: str


@dataclass(frozen=True, slots=True)
class Scene:
    id: str
    title: str
    story_order: int
    shoot: ShootPosition
    tracks: tuple[str, ...]
    expects: tuple[tuple[str, str], ...]
    transitions: tuple[Transition, ...]


@dataclass(frozen=True, slots=True)
class Project:
    schema_version: int
    title: str
    tracks: tuple[Track, ...]
    scenes: tuple[Scene, ...]
