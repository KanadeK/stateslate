# StateSlate v0.1.0

StateSlate compiles reviewed story-order continuity states into deterministic
shoot-day setup states, reset actions, and reference risks—fully offline.

## Highlights

- Strict JSON validation and explicit `from → to` story transitions
- Exact shoot-order prepare/reset diffs
- High-risk references whose story predecessor shoots later
- Configurable long-gap review findings
- JSON, CSV, Markdown, SVG, and standalone HTML from one compiled model
- Zero runtime dependencies and no network calls

## Install

Download `stateslate-0.1.0-py3-none-any.whl`, then:

```console
python -m pip install stateslate-0.1.0-py3-none-any.whl
stateslate demo --out moonlit-letter-report
```

`stateslate-examples-v0.1.0.zip` contains the reviewed input, generated reports,
format contract, and repair guide. Verify all assets with `SHA256SUMS`.

## Boundary

StateSlate proves only the internal consistency of declared states and reports.
It does not parse scripts, compare photos, verify physical setups, or replace
the production crew's approved continuity notes.
