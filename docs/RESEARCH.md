# Project selection and prior-art record

Research was performed on 2026-08-30. Star counts and product features are a
time-specific snapshot, not a permanent uniqueness claim.

## Selection constraints

The project had to avoid the large local portfolio under `D:\我的\GitHub`, avoid
previously discussed projects, expose a real algorithm/data flow, demonstrate
useful failure behavior, and remain feasible to package and verify in one release.

## Candidates considered

### Cross-stitch route planning — rejected

The need is real: multiple stitchers asked for a map-like route that minimizes
thread and restarts. However,
[`talitahalboth/ai-for-cross-stitching`](https://github.com/talitahalboth/ai-for-cross-stitching)
already uses a genetic algorithm to find a short per-colour path, while
[`XStitchLab`](https://github.com/tomekhotdog/XStitchLab) covers pattern creation,
thread estimation, and export. A new route planner would be substantially similar
at its core.

### Tile layout optimization — rejected

The problem is useful and visual, but current products such as
[`Herron`](https://herron.app/) already optimize offsets, flag slivers, reuse
offcuts, and generate exact cut guides. The open-source
[`openGrid-planner`](https://github.com/brettmiller/openGrid-planner) is adjacent.
The available v0.1 differentiation was too thin.

### Story-to-shoot continuity compilation — selected

Commercial tools validate the workflow and audience:

- [`Setikit Continuity`](https://setikit.com/continuity) organizes costume and
  hair/makeup changes, story days, shoot days, photos, and continuity books.
- [`Storyflow Continuity Tracker`](https://storyflow.so/continuity-tracker)
  explicitly describes continuity as state in story order projected against an
  out-of-order shoot.
- [`Dramatify Wardrobe`](https://dramatify.com/features/wardrobe-for-tv-and-film/)
  tracks wardrobe items and continuity photos per scene.
- [`Celtx`](https://support.celtx.com/hc/en-us/articles/360033780533-The-Schedule)
  records dramatic days in production schedules.

Targeted GitHub searches found scheduling, show-control, and media-management
projects, but no representative repository dedicated to compiling explicit
story-state transitions into deterministic shoot-order reset actions and
reference-availability findings. Absence from these searches is not proof that no
similar code exists; it supports only the narrower claim that StateSlate occupies
a useful open-source gap among the inspected results.

## Differentiation

StateSlate is not a continuity database, photo gallery, scheduling suite, or AI
script parser. Its single authority is a reviewed state-transition log. It:

1. propagates declared states in story order;
2. proves every asserted `from` and expected entry state;
3. projects those states into shoot order;
4. calculates exact setup/reset actions;
5. names references that cannot yet exist because their story predecessor shoots
   later; and
6. renders the same evidence as machine and human artifacts without a service.

That compiler contract, stable failure behavior, zero-runtime-dependency package,
and reproducible reports are the v0.1 distinction.
