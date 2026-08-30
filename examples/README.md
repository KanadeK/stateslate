# StateSlate examples

- `moonlit-letter.json` is the complete valid demonstration used by `stateslate demo`.
- `invalid-duplicate-order.json` proves duplicate story positions are blocked.
- `invalid-unknown-track.json` proves undeclared continuity tracks are blocked.
- `invalid-transition-mismatch.json` proves story-state contradictions are blocked.

Run the valid example:

```console
stateslate compile examples/moonlit-letter.json --out report
```

Run any invalid example to see a stable error code and a concrete repair. The
command exits `2` and does not create the requested report directory.
