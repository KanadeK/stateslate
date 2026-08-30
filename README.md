# StateSlate

**Compile story continuity into shoot-day reset sheets.**

[![CI](https://github.com/KanadeK/stateslate/actions/workflows/ci.yml/badge.svg)](https://github.com/KanadeK/stateslate/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/KanadeK/stateslate)](https://github.com/KanadeK/stateslate/releases/latest)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776ab)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-635bff)](LICENSE)

[简体中文](README.zh-CN.md) ·
[generated report](docs/demo/report.html) ·
[input format](docs/FORMAT.md) ·
[failure repair](docs/REPAIR.md) ·
[research](docs/RESEARCH.md)

![StateSlate compares story order with shoot order](docs/demo/timeline.svg)

StateSlate is an offline, zero-runtime-dependency CLI for small film, video,
commercial, and photo productions. Give it reviewed continuity tracks, scene
order, shooting order, and explicit state changes. It propagates each state in
story order, then tells the shoot what to prepare, what to reset, and which
reference cannot exist yet because its story predecessor shoots later.

It is a compiler, not a continuity database or an AI guesser. It never uploads
production data, parses scripts, evaluates photos, or claims that a setup is
visually correct.

## The problem

Continuity lives in story order, while production works in shoot order. A coat
may become rain-soaked in scene 20 even though scene 20 shoots before scene 10.
The required state is knowable, but the usual reference photo from scene 10 is
not available yet. A spreadsheet can list both scenes; it does not prove that
the state chain is internally consistent or calculate the exact reset between
two scheduled uses.

StateSlate makes the two orders explicit:

```text
reviewed JSON
    │
    ├─ story order ──> validate expectations and transitions ──> entry/exit states
    │
    └─ shoot order ──> prepare/reset diff + reference availability + day-gap risks
                                                              │
                    JSON · CSV · Markdown · SVG · standalone HTML
```

## 60-second proof

Requires Python 3.11 or newer. Download the wheel from the
[latest Release](https://github.com/KanadeK/stateslate/releases/latest), then:

```console
python -m pip install stateslate-0.1.0-py3-none-any.whl
stateslate demo --out moonlit-letter-report
```

The command creates exactly five files:

```text
moonlit-letter-report/
├── continuity.json       exact machine evidence
├── shoot-plan.csv        spreadsheet-safe scene/track rows
├── reset-checklist.md    printable shoot-order actions
├── timeline.svg          story/shoot order comparison
└── report.html           standalone, script-free report
```

The built-in example produces four scenes, three continuity tracks, three
preparations, three resets, two high risks, and two medium risks. Inspect the
[committed output](docs/demo/continuity.json) or compile the public source file:

```console
stateslate compile examples/moonlit-letter.json --out report
```

## What the compiler proves

For the declared project, StateSlate proves that:

- every identifier and story/shoot position is unique;
- every used track was declared;
- every `expects` value equals the inherited story state;
- every transition's `from` equals the current story state;
- each report uses the same compiled entry/exit states;
- each shoot-order reset names its previous scheduled state and required state;
- each reference names its previous story occurrence and whether that scene has
  already shot;
- identical input and options produce byte-identical output.

It does **not** prove that a label is accurate, a costume was reset correctly,
a photo matches, or the production followed the report. The crew remains the
authority for real-world continuity.

## Input at a glance

```json
{
  "schema_version": 1,
  "title": "Moonlit Letter",
  "tracks": [
    {
      "id": "mara.coat",
      "label": "Mara's blue coat",
      "category": "wardrobe",
      "initial": "clean_buttoned"
    }
  ],
  "scenes": [
    {
      "id": "S20",
      "title": "Rain in the alley",
      "story_order": 20,
      "shoot": {"day": 1, "order": 1},
      "tracks": ["mara.coat"],
      "expects": {"mara.coat": "clean_buttoned"},
      "transitions": [
        {
          "track": "mara.coat",
          "from": "clean_buttoned",
          "to": "rain_soaked_open"
        }
      ]
    }
  ]
}
```

State values are deliberately atomic strings in v0.1. If the buttoning and
wetness need independent continuity, declare separate tracks. See the complete
[format contract](docs/FORMAT.md).

## Commands and exit codes

```console
stateslate validate project.json
stateslate compile project.json --out report
stateslate compile project.json --out report --risk-days 5 --fail-on medium
stateslate demo --out demo-report
stateslate --version
```

| Exit | Meaning | Output |
| --- | --- | --- |
| `0` | Valid command; selected risk gate passed | Reports written for `compile`/`demo` |
| `1` | Valid compilation; requested risk threshold was met | Reports kept as evidence |
| `2` | Invalid input, unsafe output target, I/O, or CLI usage | No report directory created |

StateSlate refuses an existing `--out` directory. It never merges or replaces
owner files. Read [failure repair](docs/REPAIR.md) for every stable error code.

## Why this is different

Existing production suites are designed around databases, photos, schedules,
and team workflows. StateSlate has one narrow job: compile a reviewed state log
into reproducible evidence without an account, service, or proprietary file.
The research record documents representative commercial neighbors, rejected
ideas, GitHub searches, and the limits of the differentiation claim.

## Design limits

v0.1 accepts at most 2 MiB of UTF-8 JSON, 500 tracks, 1,000 scenes, and 10,000
transitions. It supports one shoot sequence, integer shoot days/orders, and
short string states. It intentionally excludes:

- screenplay parsing, OCR, or AI inference;
- continuity-photo storage or comparison;
- call-sheet or shooting-schedule optimization;
- accounts, collaboration, cloud sync, or a hosted API;
- automatic artistic, physical, legal, or safety decisions.

## Contributor verification

```console
git clone https://github.com/KanadeK/stateslate.git
cd stateslate
uv sync --locked --all-groups
uv run --no-sync python scripts/check.py
```

The release gate runs formatting, Ruff, strict mypy, branch coverage, examples,
blocking failures, dependency audit, wheel/sdist build, an isolated wheel
install, and the installed console entry point. See [CONTRIBUTING.md](CONTRIBUTING.md)
and the [architecture](docs/ARCHITECTURE.md).

## License

MIT. See [LICENSE](LICENSE).
