# Contributing

Thank you for improving StateSlate. Keep contributions narrow, deterministic,
and grounded in an observed continuity workflow.

## Setup

```console
git clone https://github.com/KanadeK/stateslate.git
cd stateslate
uv sync --locked --all-groups
uv run --no-sync python scripts/check.py
```

## Change process

1. Open an issue describing the real input, expected result, and current result.
2. Add a failing behavior test before changing logic.
3. Implement the smallest complete fix or feature.
4. Run the focused test, then the full release gate.
5. Update the format contract or ADR if a public contract changes.

Do not add runtime dependencies, AI/script parsing, cloud features, or a second
state authority without prior design agreement. Do not weaken a test, lint rule,
type check, coverage threshold, failure exit code, or no-overwrite behavior to
make a contribution pass.

## Commit style

Use focused conventional messages such as:

```text
feat: explain unavailable story references
fix: reject duplicate shoot positions
docs: clarify compound state modeling
```

Never commit production data, photos, credentials, generated virtual
environments, or build output.
