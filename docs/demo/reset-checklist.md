# Moonlit Letter — reset checklist

Scenes: **4** · prepare: **3** · reset: **3** · high risks: **2** · medium risks: **2**

## Day 1 / 1 — S20 — Rain in the alley

- Prepare `mara.coat` as `clean_buttoned`.
- Prepare `letter.seal` as `opened`.

| Track | Label | Category | Setup | Exit | Reference |
| --- | --- | --- | --- | --- | --- |
| `mara.coat` | Mara's blue coat | wardrobe | `clean_buttoned` | `rain_soaked_open` | future: S10 (3 day gap) |
| `letter.seal` | Red letter seal | props | `opened` | `opened` | future: S10 (3 day gap) |

Risks:
- **HIGH FUTURE_REFERENCE** — `mara.coat` references S10 across 3 shoot day(s).
- **HIGH FUTURE_REFERENCE** — `letter.seal` references S10 across 3 shoot day(s).

## Day 1 / 2 — S30 — The diner confession

- Prepare `cafe.glass` as `full`.

| Track | Label | Category | Setup | Exit | Reference |
| --- | --- | --- | --- | --- | --- |
| `mara.coat` | Mara's blue coat | wardrobe | `rain_soaked_open` | `rain_soaked_open` | available: S20 (0 day gap) |
| `cafe.glass` | Cafe water glass | props | `full` | `half` | initial state |

## Day 4 / 1 — S10 — The letter arrives

- Reset `mara.coat`: `rain_soaked_open` → `clean_buttoned` (after S30).
- Reset `letter.seal`: `opened` → `sealed` (after S20).

| Track | Label | Category | Setup | Exit | Reference |
| --- | --- | --- | --- | --- | --- |
| `mara.coat` | Mara's blue coat | wardrobe | `clean_buttoned` | `clean_buttoned` | initial state |
| `letter.seal` | Red letter seal | props | `sealed` | `opened` | initial state |

## Day 6 / 1 — S40 — Morning pickup

- Reset `mara.coat`: `clean_buttoned` → `rain_soaked_open` (after S10).

| Track | Label | Category | Setup | Exit | Reference |
| --- | --- | --- | --- | --- | --- |
| `mara.coat` | Mara's blue coat | wardrobe | `rain_soaked_open` | `rain_soaked_open` | available: S30 (5 day gap) |
| `cafe.glass` | Cafe water glass | props | `half` | `half` | available: S30 (5 day gap) |

Risks:
- **MEDIUM LONG_REFERENCE_GAP** — `mara.coat` references S30 across 5 shoot day(s).
- **MEDIUM LONG_REFERENCE_GAP** — `cafe.glass` references S30 across 5 shoot day(s).

> StateSlate compiles declared states. Confirm every setup against the approved 
> continuity notes and on-set reference material.
