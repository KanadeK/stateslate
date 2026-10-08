# Changelog

All notable changes to StateSlate are documented here.

## [0.1.0] - 2026-10-07

### Added

- Strict versioned JSON contract for continuity tracks, scenes, expectations,
  story transitions, and shoot positions.
- Deterministic story-state propagation with contradiction diagnostics.
- Shoot-order preparation and reset actions.
- High-risk future-reference and configurable medium day-gap findings.
- Stable JSON, CSV, Markdown, SVG, and standalone HTML reports.
- Transactional, no-overwrite CLI with `validate`, `compile`, and `demo`.
- Clean and blocking examples, cross-platform CI, release packaging, and one
  complete contributor acceptance gate.

### Security

- Refreshed the development-toolchain lock to urllib3 2.8.0 after the release
  audit identified three advisories in 2.7.0. Runtime dependencies remain empty.
