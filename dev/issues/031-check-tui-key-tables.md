# [feat] Check the TUI key tables against the screens

The key tables in the guide are written by hand, so a rebound key goes unnoticed. Verify each table against the screen it describes.

Depends on 028. Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- Each key table in the guide names its screen: Home, lookup, entry, add word or study.
- A test fails when a table row's key is not handled by its screen.
- A test fails when a visible bound key is missing from its table.
- Keys handled by a widget rather than the screen's `BINDINGS` (such as `space` ticking a row, or `enter` submitting an input) are declared and accounted for, so they pass.
- The prose around the tables is unchanged.
