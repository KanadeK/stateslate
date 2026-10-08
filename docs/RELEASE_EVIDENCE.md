# StateSlate v0.1.0 release evidence

Verified on 2026-10-07 (America/Los_Angeles).

## Published version

- Public repository: [KanadeK/stateslate](https://github.com/KanadeK/stateslate)
- Release: [v0.1.0](https://github.com/KanadeK/stateslate/releases/tag/v0.1.0),
  neither draft nor prerelease.
- Release commit: `438b8440783a49bfa1e060225fc05829c265391c`.
- Annotated tag object: `46974410a1a96e65b319775e1a37d840cf2e9094`,
  pointing to the release commit.
- The immutable release tag remains on the validated functional commit; later
  documentation commits do not move it.

## Quality gates

- 45 tests passed; branch coverage was 91.40%.
- Formatting, Ruff, strict mypy, lock validation, example reproduction, blocking
  inputs, wheel/sdist construction, packaging, and isolated installation passed.
- The release audit found three urllib3 2.7.0 advisories in the development
  toolchain. The lock was updated to 2.8.0 and the complete audit passed.
- [Main CI](https://github.com/KanadeK/stateslate/actions/runs/37735781726)
  and [tag CI](https://github.com/KanadeK/stateslate/actions/runs/37735955894)
  passed on Ubuntu/Python 3.11 and Windows/Python 3.14.
- [Release workflow](https://github.com/KanadeK/stateslate/actions/runs/37735955936)
  passed and published the assets below.

## Downloadable assets

| Asset | Bytes |
| --- | ---: |
| `stateslate-0.1.0-py3-none-any.whl` | 21,232 |
| `stateslate-0.1.0.tar.gz` | 18,038 |
| `stateslate-examples-v0.1.0.zip` | 18,042 |
| `SHA256SUMS` | 287 |

## Public-install acceptance

All four files were downloaded from public Release URLs without authentication
headers. All three archive hashes matched the downloaded `SHA256SUMS` manifest.
The public wheel was installed offline into a new Python environment.

- `stateslate --version` returned `stateslate 0.1.0`.
- The bundled JSON and built-in demo each produced all five reports: four
  scenes, three tracks, three preparations, three resets, two high risks, and
  two medium risks.
- `--fail-on high` returned exit 1 and retained the report.
- The contradictory transition example returned exit 2 and created no report.
- The online contributor list and local author/committer history contained only
  `KanadeK`; no co-author trailer was present.
- Private vulnerability reporting was enabled.
- The release completion notification was delivered through Gmail and confirmed
  in Sent after a transient connector quota error was resolved.

## Reproduce

```console
python -m pip install https://github.com/KanadeK/stateslate/releases/download/v0.1.0/stateslate-0.1.0-py3-none-any.whl
stateslate demo --out moonlit-letter-report
```

StateSlate validates declared continuity states. On-set setup and visual
continuity remain production-team decisions.
