# ADR-0001: Story order is the sole state authority

## Status

Accepted

## Date

2026-08-30

## Context

Continuity teams need both story order and shoot order. If each order owns a
mutable copy of state, corrections can diverge and reports can disagree.

## Decision

Propagate and validate state only in story order. Treat shoot order as a pure
projection that reads the compiled entry/exit states, calculates reset diffs,
and evaluates reference availability. Render every artifact from the resulting
immutable compilation model.

## Alternatives considered

### Store independent story and shoot states

Rejected because it creates two truth sources and requires reconciliation.

### Infer continuity from scene descriptions or photos

Rejected because v0.1 cannot prove semantic or visual correctness. Inference
would introduce dependencies and hidden uncertainty into the authoritative path.

### Make a database the authority

Rejected for v0.1 because a local reviewed JSON file is easier to diff, archive,
package, and reproduce. Team collaboration is outside the selected scope.

## Consequences

- Every contradiction has one precise location in the story chain.
- Shoot-order changes do not rewrite continuity state.
- Reports remain deterministic and mutually consistent.
- Users must explicitly declare states and transitions; StateSlate does not fill
  missing creative or production knowledge.
