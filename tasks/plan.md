# Implementation Plan: StateSlate v0.1.0

## Overview

Build a dependency-free continuity compiler in thin vertical slices, prove each
behavior before expanding, then publish only after local and remote release gates
pass.

## Architecture decisions

- Story order is the sole authority for state propagation; shoot order is a
  projection used for preparation and reference risk.
- JSON stays the human-reviewable interchange format; internal dataclasses make
  invariants explicit after boundary validation.
- Reports are generated from one immutable compilation model so JSON, CSV,
  Markdown, SVG, and HTML cannot become separate truth sources.
- The package has zero runtime dependencies and never runs a local server.
- Existing output directories are rejected rather than merged or replaced.

## Dependency graph

```text
schema tests -> validated dataclasses -> story propagation
                                     -> shoot projection -> report model
                                                        -> renderers -> CLI
                                                        -> examples/golden demo
all slices -> release gate -> CI/release workflow -> public verification
```

## Phase 1: Contract and core

- Task 1: Write schema and parser tests, observe RED, implement strict parsing.
- Task 2: Write propagation tests, observe RED, implement story-state compiler.
- Task 3: Write shoot projection tests, observe RED, implement resets and risks.

### Checkpoint

- Focused tests pass; malformed and contradictory inputs fail without fallback.

## Phase 2: User-facing slice

- Task 4: Test and implement deterministic JSON/CSV/Markdown/SVG/HTML renderers.
- Task 5: Test and implement `validate`, `compile`, `demo`, and stable exit codes.
- Task 6: Add clean and blocking examples; generate and verify committed demo.

### Checkpoint

- The example works end-to-end and produces real, inspectable artifacts.

## Phase 3: Delivery system

- Task 7: Add README, format/architecture/repair/research docs, license, security,
  contribution guide, changelog, and ADR.
- Task 8: Add one-command local gate, CI matrix, release workflow, and packaging.
- Task 9: Run five-axis review and repair every correctness/security blocker with
  regression tests.

### Checkpoint

- Full gate passes from a clean checkout and isolated wheel installation.

## Phase 4: Public release

- Task 10: Create public repository, push exact clean commit, and wait for CI.
- Task 11: Create annotated tag and Release assets; verify public metadata and
  checksums.
- Task 12: Download and install the public wheel, run the example, verify sole
  contributor identity, then send and verify Gmail notice.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| State semantics become ambiguous | Incorrect plans | Keep v0.1 state values atomic strings and require explicit transitions |
| Report formats diverge | Conflicting truth sources | Render every artifact from one compiled dataclass model |
| Untrusted text injects HTML/CSV | Unsafe report opening | Escape markup and neutralize formula-leading cells |
| Large input causes excessive work | Local denial of service | Enforce file, scene, track, and transition caps at the boundary |
| GitHub auth is stale | Remote release blocked | Use official GitHub CLI reauthentication and verify remote state after every write |
| Cross-platform golden files drift | CI-only failure | Pin demo text outputs to LF and compare bytes on both OS families |

## Open questions

None that changes v0.1 scope.
