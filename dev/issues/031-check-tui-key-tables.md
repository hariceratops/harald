# [feat] Check the TUI key tables against the screens

The key tables in the guide are written by hand, so a rebound key goes unnoticed. Verify each table against the screen it describes.

Depends on 028 and 029 (`keys` is a word in the checker's vocabulary). Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- Each key table in the guide names its screen: Home, lookup, entry, add word or study.
- A test fails when a table row's key is not handled by its screen.
- A test fails when a visible bound key is missing from its table.
- Keys handled by a widget rather than the screen's `BINDINGS` (such as `space` ticking a row, or `enter` submitting an input) are declared and accounted for, so they pass.
- Lookup, entry and study have no key table today, so three are added. Existing prose on those pages is unchanged.
- The Info screen, the end-of-session summary and the two pop-up dialogs are out of scope and recorded as a follow-up.
- `markdown-it-py` is declared in the `dev` dependency group of `pyproject.toml`. The docs toolchain (mkdocs and its plugins) stays out of it.
- The prose around the tables is unchanged.
