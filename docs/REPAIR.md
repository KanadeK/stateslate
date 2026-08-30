# Failure and repair guide

StateSlate writes one stable error code, a plain explanation, and a `Repair:`
line to standard error. Invalid input and unsafe output use exit `2` and do not
create the requested report directory.

## Read and syntax failures

| Code | Cause | Repair |
| --- | --- | --- |
| `FILE_READ` | Missing/unreadable input | Check the path and permissions |
| `FILE_TOO_LARGE` | JSON exceeds 2 MiB | Split the production into smaller projects |
| `INVALID_UTF8` | File is not UTF-8 | Re-save as UTF-8 JSON |
| `INVALID_JSON` | Syntax error, NaN, or Infinity | Correct the reported location/value |

Validate after repair:

```console
stateslate validate project.json
```

## Schema failures

| Code | Cause | Repair |
| --- | --- | --- |
| `SCHEMA_VERSION` | Version is not integer `1` | Use the v0.1 schema |
| `UNKNOWN_KEY` | Typo or unsupported field | Compare with `docs/FORMAT.md` |
| `MISSING_KEY` | Required field absent | Add the named field |
| `TYPE` / `STRING` / `IDENTIFIER` | Wrong JSON type or invalid text | Use the stated type and identifier grammar |
| `LIMIT` / `EMPTY_LIST` | Declared boundary exceeded | Add required data or split the project |
| `DUPLICATE_TRACK` / `DUPLICATE_SCENE` | Reused identifier | Rename one item and update references |
| `DUPLICATE_STORY_ORDER` | Two scenes claim one story position | Assign unique story positions |
| `DUPLICATE_SHOOT_POSITION` | Two scenes claim one day/order pair | Assign unique shoot positions |
| `UNKNOWN_TRACK` | Scene references undeclared track | Declare it or fix the identifier |
| `UNLISTED_TRACK` | Expectation/transition track absent from scene | Add it to scene `tracks` |
| `NOOP_TRANSITION` | `from` equals `to` | Remove it or declare the real change |

Reproduce three common blockers:

```console
stateslate compile examples/invalid-duplicate-order.json --out should-not-exist
stateslate compile examples/invalid-unknown-track.json --out should-not-exist
stateslate compile examples/invalid-transition-mismatch.json --out should-not-exist
```

## Story-state failures

`EXPECTATION_MISMATCH` means a scene's asserted entry value differs from the
state produced by earlier story scenes. `TRANSITION_MISMATCH` means a
transition's `from` does not equal the current story state.

Do not change the assertion only to silence the tool. Check the story chain:

1. Is the initial value correct?
2. Is an earlier scene missing a transition?
3. Is the current scene using the wrong track or state spelling?
4. If the story really jumps, declare that change in the scene where it occurs.

Then run `stateslate validate project.json` before compiling again.

## Output failures

`OUTPUT_EXISTS` protects owner data. Choose a new path; StateSlate intentionally
has no overwrite flag. `OUTPUT_PARENT` means the parent directory must be
created first. `OUTPUT_WRITE` indicates permissions, disk space, antivirus, or
filesystem failure; the requested final directory was not published.

## Risk gate exit 1

Exit `1` is not a compile failure. All five reports exist. Inspect the named
risks in `continuity.json` or `report.html`, establish manual references/reset
checks, then choose whether the production's CI policy should pass.

## Contributor gate failures

Run the single authoritative command:

```console
uv sync --locked --all-groups
uv run --no-sync python scripts/check.py
```

- Fix formatting with `uv run --no-sync ruff format .`.
- Do not disable Ruff/mypy rules, skip tests, or lower coverage.
- If wheel installation fails, inspect the built asset list and console entry
  point before changing the test.
- If generated demo bytes differ only on Windows line endings, confirm Git
  checkout bytes and `.gitattributes`; retain the byte comparison.
- If dependency download hits a network permission error, rerun the unchanged
  command in an execution context permitted to access PyPI.
- If one host separates filesystem and network permissions, export and audit the
  locked requirements in the network-capable context, then run
  `scripts/check.py --skip-audit` locally. CI must still run the default command.
