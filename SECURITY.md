# Security policy

## Supported versions

Security fixes are applied to the latest published StateSlate release.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for
[`KanadeK/stateslate`](https://github.com/KanadeK/stateslate/security/advisories/new).
Please do not include real production continuity data in a report. Include a
minimal synthetic project and the affected version.

## Security model

StateSlate is an offline CLI with no runtime dependencies, server, telemetry,
accounts, subprocess execution, or network calls. Its trust boundary is the
local JSON project and destination path.

Controls include:

- 2 MiB file, 500-track, 1,000-scene, and 10,000-transition limits;
- strict keys and types with no dynamic evaluation;
- escaped HTML/SVG text and script-free reports;
- spreadsheet formula neutralization in CSV while JSON preserves exact values;
- full in-memory render before transactional output publication;
- refusal to overwrite or merge an existing output directory;
- locked development dependencies and release-time audit.

Generated reports may still contain the continuity names and states supplied by
the user. Store and share them under the production's own confidentiality rules.
