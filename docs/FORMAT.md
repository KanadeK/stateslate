# StateSlate v0.1 input format

StateSlate accepts one UTF-8 JSON object. Unknown keys are errors so a typo can
never silently change the continuity plan.

## Project

| Key | Type | Rules |
| --- | --- | --- |
| `schema_version` | integer | Must be `1` |
| `title` | string | 1–200 chars, no edge whitespace |
| `tracks` | array | 1–500 unique track objects |
| `scenes` | array | 1–1,000 unique scene objects |

The whole file is limited to 2 MiB and 10,000 total transitions.

## Identifiers

Track and scene identifiers are 1–64 ASCII characters and match:

```text
[A-Za-z0-9][A-Za-z0-9._-]{0,63}
```

Identifiers are case-sensitive. Use stable semantic names such as
`mara.coat.wetness`; do not put labels or changing state in an identifier.

## Track

```json
{
  "id": "mara.coat",
  "label": "Mara's blue coat",
  "category": "wardrobe",
  "initial": "clean_buttoned"
}
```

`label` is display text up to 200 chars. `category` is a project-defined string
up to 64 chars. `initial` is the state before the first story scene, up to 120
chars.

## Scene

```json
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
      "to": "rain_soaked_open",
      "note": "Coat becomes wet during the scene"
    }
  ]
}
```

- `story_order` is a unique positive integer. Values need not be contiguous.
- `shoot.day` and `shoot.order` are positive integers; the pair must be unique.
- `tracks` lists every continuity track relevant to this scene. A track appears
  at most once.
- `expects` is optional. It asserts a relevant track's story-entry state.
- `transitions` is optional. Each transition track must be relevant to the scene.
- Multiple transitions for one track are allowed and run in declared order.
- `from` must equal the current story state; `to` must be different.
- `note` is optional display text up to 500 chars.

## State modeling

States are exact, case-sensitive strings. StateSlate does not parse their
meaning. Prefer a controlled project vocabulary and avoid ambiguous prose.

Use separate tracks when dimensions can change independently:

```text
mara.coat.wetness: dry -> soaked
mara.coat.fastening: buttoned -> open
```

That is easier to review than one combinatorial state such as
`soaked_open_dirty_left_sleeve`.

## Risk threshold

`--risk-days N` is a positive integer, default `3`.

- `FUTURE_REFERENCE` is always high: the previous story occurrence is scheduled
  later than the current shoot scene.
- `LONG_REFERENCE_GAP` is medium: the previous story occurrence has already
  shot, but the day difference is at least `N`.

These are coordination risks, not predictions that continuity will fail.
