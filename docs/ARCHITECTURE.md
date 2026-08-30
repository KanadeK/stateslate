# Architecture

StateSlate is a one-way compiler. No report becomes an input to another report,
and no renderer owns continuity logic.

```text
JSON file
  -> parser.py       strict boundary validation and immutable input dataclasses
  -> compiler.py     story-state propagation
  -> compiler.py     shoot-order resets and reference risks
  -> render.py       five deterministic views of one Compilation object
  -> cli.py          transactional directory publication and exit-code policy
```

## Authority and data flow

Story order is the only state authority. The compiler starts from every track's
declared `initial` value, checks scene expectations, checks each transition's
`from`, and applies its `to`. Shoot order never changes story state. It only
compares required entry states against the last scheduled exit state and asks
whether the previous story occurrence has already shot.

This prevents two mutable state graphs. See
[ADR-0001](decisions/0001-story-order-is-state-authority.md).

## Determinism

- Scenes sort by unique integer positions.
- Track order follows the reviewed project arrays.
- JSON keys sort and every text artifact uses LF endings.
- Reports contain no generation timestamp or machine-specific path.
- The committed example is regenerated and compared byte-for-byte in the gate.

## Failure atomicity

Parsing and compilation finish before any report path is created. Rendering
finishes in memory. The CLI then writes all five artifacts to a uniquely named
temporary directory beside the requested output and renames it only after every
write succeeds. Existing output directories are rejected.

## Complexity

The compiler is linear in declared scene-track uses plus transitions. It does no
combinatorial search, image processing, network access, or background work.
Input caps bound both memory and report size.

## Trust boundary

The JSON file and every contained string are untrusted. The parser validates
shape and size; HTML and SVG escape text; CSV prefixes formula-leading cells;
Markdown escapes table delimiters. JSON preserves the exact reviewed values.
