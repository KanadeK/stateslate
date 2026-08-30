# Pre-release five-axis review

Review date: 2026-08-30

Scope: StateSlate v0.1 input boundary, state compiler, report renderers, CLI,
tests, documentation, packaging, and GitHub workflows.

## Findings repaired before release

1. **Correctness/security — duplicate JSON keys were silently accepted.** Python's
   default decoder keeps the last value, contradicting StateSlate's strict-input
   promise. Added duplicate-key detection and a regression test.
2. **Correctness — oversized JSON integers could escape the stable error contract.**
   Added conversion of decoder `ValueError` to `INVALID_JSON` and a regression
   test. A deep-nesting hypothesis was tested and rejected when Python 3.14
   returned a normal top-level type error instead of crashing.
3. **Security/readability — control characters could enter human reports.** Added
   boundary rejection for embedded tabs, line breaks, nulls, and other ASCII
   controls.
4. **Readability — Markdown inline code could break on a state containing a
   backtick.** Replaced backslash guessing with a fence longer than the longest
   declared backtick run and added a behavioral test.
5. **Release hygiene — generated Markdown contained trailing whitespace.** Added
   an all-artifact assertion, repaired the renderer, and regenerated the golden
   output.
6. **Supply chain — the first audit found `PYSEC-2026-1845` in pytest 8.4.2.**
   Updated the locked development dependency to pytest 9.1.1, reran all tests,
   and obtained a clean locked-dependency audit.

## Correctness

- Story order is the only state authority; shoot order cannot mutate it.
- Every expectation and transition is checked before reports are rendered.
- Tests cover valid compilation, sequential transitions, exact resets, initial
  and future references, long gaps, all five formats, CLI exit codes, refusal to
  overwrite, blocking examples, release assets, checksums, and clean install.
- The public and embedded demo are byte-identical; all committed demo outputs
  are regenerated and byte-compared.

Verdict: no unresolved correctness blocker.

## Readability and simplicity

- Five focused runtime modules own input models, parsing, compilation, rendering,
  and orchestration. There is no service, plugin system, database, or compatibility
  layer.
- Business rules live in the compiler; renderers consume one immutable model.
- Runtime dependency count is zero.

Verdict: the abstractions match the five real responsibilities and do not add a
second path.

## Architecture

- ADR-0001 records story-order authority and rejected alternatives.
- Output publication is transactional and existing owner paths are immutable.
- Release artifacts are derived from the same version and exact built wheel/sdist
  pair; checksums cover every downloadable asset except the manifest itself.

Verdict: no parallel truth source or compatibility shadow remains.

## Security

- External JSON is size/shape/type/key/value bounded before compilation.
- HTML/SVG escape user text, CSV neutralizes formula-leading cells, and Markdown
  uses safe delimiters. Exact values remain in JSON for auditability.
- No runtime dependency, network request, subprocess execution, dynamic code,
  credential, or telemetry exists in the installed tool.
- Locked development dependencies have no known vulnerabilities after the pytest
  repair.

Verdict: no unresolved security blocker within the declared local-file scope.

## Performance

Compilation is linear in scene-track uses plus transitions; all loops are bounded
by the 2 MiB/500-track/1,000-scene/10,000-transition input limits. Reports render
in memory before publication. No profiling is justified for the bounded v0.1
workload.

Verdict: no unbounded operation or performance blocker.

## Verification boundary

The HTML/SVG structure, escaping, deterministic bytes, accessible SVG title/desc,
and absence of scripts are automated. A Chrome DevTools MCP connection is not
configured, and workspace policy prohibits launching a local browser without an
explicit visual-browser request, so no claim of real-browser visual acceptance is
made. Remote CI and release verification remain mandatory before publication is
called complete.

## Review verdict

Approved for remote CI and release validation after the complete gate passes on
the exact commit. No Critical or Required findings remain.
