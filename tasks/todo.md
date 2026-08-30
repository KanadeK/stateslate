# StateSlate v0.1.0 task list

- [x] Task 1: Strict JSON contract
  - Acceptance: valid project parses; unknown keys, duplicates, and bounds fail.
  - Verify: focused parser tests fail first, then pass.
- [ ] Task 2: Story-order state propagation
  - Acceptance: entry/exit states are exact; contradictory `from`/`expects` fail.
  - Verify: focused compiler tests fail first, then pass.
- [ ] Task 3: Shoot-order resets and risks
  - Acceptance: prepare/reset actions and reference availability are deterministic.
  - Verify: focused projection tests fail first, then pass.
- [ ] Task 4: Five report formats
  - Acceptance: outputs agree, are deterministic, and escape untrusted text.
  - Verify: renderer unit tests and golden demo comparison.
- [ ] Task 5: CLI and exit codes
  - Acceptance: validate/compile/demo/version work; failure leaves no output.
  - Verify: subprocess integration tests.
- [ ] Task 6: Examples and documentation
  - Acceptance: clean and three blocking examples plus repair instructions exist.
  - Verify: every documented command is executed.
- [ ] Task 7: Packaging and automation
  - Acceptance: wheel/sdist, isolated install, CI matrix, and release assets work.
  - Verify: `uv run --locked python scripts/check.py`.
- [ ] Task 8: Independent five-axis review
  - Acceptance: no unresolved correctness, simplicity, architecture, security, or
    performance blockers.
  - Verify: review record and regression tests for every discovered blocker.
- [ ] Task 9: Public release closure
  - Acceptance: public repo, green CI, annotated tag, Release assets/checksums,
    fresh public install, contributor audit, and verified Gmail notice.
  - Verify: public API/CLI checks and sent-message retrieval.
