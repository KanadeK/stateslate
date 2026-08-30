# Spec: StateSlate v0.1.0

## Objective

StateSlate is an offline continuity compiler for small film, video, and photo
productions. It turns explicit story-order state changes into shoot-order setup
states, reset actions, and reference risks. The primary users are script
supervisors and wardrobe, props, hair, or makeup teams who shoot scenes out of
story order.

StateSlate is successful when a reviewed JSON project can be compiled into a
deterministic machine report, a spreadsheet-ready shoot plan, a printable reset
checklist, an SVG timeline, and a standalone HTML report. Contradictory state
transitions must fail before any output directory is created.

## Functional contract

- A project declares uniquely identified continuity tracks, each with a category
  and initial state.
- Scenes have unique story positions and unique `(shoot day, shoot order)`
  positions.
- Scene `tracks` declare what must be prepared or observed for that scene.
- Optional `expects` assert inherited entry states.
- Scene transitions explicitly declare `from` and `to` state values. `from`
  must match the propagated story state.
- The compiler calculates every relevant entry and exit state in story order.
- The shoot-order projection calculates prepare/reset actions against the last
  scheduled use of each track.
- A reference is marked unavailable when a scene's previous story occurrence
  is scheduled later in shoot order.
- A configurable day-gap threshold marks otherwise available references as a
  review risk.
- Output contains no wall-clock timestamps and is byte-stable for the same
  input and options.

### CLI

```console
stateslate validate PROJECT.json
stateslate compile PROJECT.json --out REPORT_DIR [--risk-days N] [--fail-on none|medium|high]
stateslate demo --out REPORT_DIR
stateslate --version
```

Exit codes:

- `0`: command completed and the selected risk gate passed.
- `1`: valid project compiled, but findings met the requested `--fail-on` gate.
- `2`: invalid input, I/O error, unsafe output target, or CLI usage error.

`compile` and `demo` require a new output directory. They never merge with or
replace an existing directory.

## Input boundary

- UTF-8 JSON, schema version `1`, maximum 2 MiB.
- At most 500 tracks, 1,000 scenes, and 10,000 total transitions.
- Identifiers use ASCII letters, digits, `.`, `_`, and `-`, maximum 64 chars.
- Labels, titles, categories, and states are bounded strings.
- Unknown keys are rejected so misspellings fail fast.
- No URLs, scripts, binary attachments, or external file references exist in
  the v0.1 schema.

## Outputs

- `continuity.json`: normalized story states, shoot states, risks, and resets.
- `shoot-plan.csv`: one row per scene/track with spreadsheet-safe text cells.
- `reset-checklist.md`: shoot-order preparations and changes.
- `timeline.svg`: accessible, standalone story/shoot comparison.
- `report.html`: escaped, script-free standalone report.

## Tech stack

- Python 3.11+
- Standard library only at runtime
- `pytest`, `coverage`, `ruff`, `mypy`, `build`, and `pip-audit` for development
- `uv` with a committed lockfile

## Commands

```console
uv sync --locked --all-groups
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy src tests
uv run --locked coverage run -m pytest
uv run --locked coverage report --fail-under=90
uv run --locked python -m build
uv run --locked python scripts/check.py
```

## Project structure

```text
src/stateslate/       package, parser, compiler, renderers, CLI
tests/                unit and CLI integration tests
examples/             clean and blocking input fixtures
docs/                 research, format, architecture, repair guidance, demo
scripts/check.py       one-command release gate
tasks/                 implementation plan and completion record
.github/workflows/     cross-platform CI and release automation
```

## Code style

Use explicit dataclasses and pure transformations. Invalid external data raises
one typed boundary error; internal invariants are trusted.

```python
def compile_project(project: Project, risk_days: int) -> Compilation:
    story_states = propagate_story(project)
    return project_shoot_order(project, story_states, risk_days)
```

## Testing strategy

- Unit tests cover schema validation, state propagation, resets, references,
  deterministic ordering, and escaping.
- Integration tests execute the installed-style CLI against temporary paths.
- Failure tests prove contradictions and unsafe output reuse create no reports.
- Branch coverage must remain at or above 90%.
- The release gate builds wheel/sdist and runs the console entry point from an
  isolated environment.

## Boundaries

### Always

- Validate only at JSON/CLI/file boundaries.
- Escape HTML/SVG and neutralize spreadsheet formula cells.
- Preserve exact values in JSON.
- Keep reports deterministic and local.
- Re-run the complete release gate after release-script changes.

### Ask first

- Add runtime dependencies.
- Add screenplay parsing, image analysis, cloud storage, or collaboration.
- Change the v0.1 schema or exit-code contract after release.

### Never

- Claim the tool proves physical or visual continuity.
- Infer states the production did not declare.
- Overwrite an existing output directory.
- Upload production data or execute values from input.
- Weaken a failing quality gate to make a release pass.

## Success criteria

- The committed demo produces all five outputs with at least one reset, one
  future-reference risk, and one long-gap risk.
- Blocking examples cover duplicate order, unknown track, and contradictory
  transition state; each exits `2` and leaves no output.
- Format, lint, strict type checking, tests, >=90% branch coverage, packaging,
  dependency audit, demo reproducibility, and clean-wheel execution pass.
- GitHub CI passes on Windows and Ubuntu for supported Python versions.
- An annotated `v0.1.0` tag and public non-draft Release contain wheel, sdist,
  examples archive, and checksums.
- A fresh environment installs the public wheel and compiles the public example.
- Repository visibility, tag target, assets, and contributor identity are
  independently verified before the completion email is sent.

## Explicit non-goals

- OCR or screenplay parsing
- Photo storage, comparison, or biometric analysis
- Multi-user sync, permissions, mobile apps, or a hosted service
- Scheduling optimization or call-sheet generation
- Automatic artistic or safety decisions

## Open questions

None for v0.1. The user delegated project choice and full release execution; the
scope above deliberately chooses deterministic planning over speculative AI.
