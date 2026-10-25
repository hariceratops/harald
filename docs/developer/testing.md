# Testing

```sh
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

## Layers

| Directory | Verifies |
|---|---|
| `tests/unit/` | pure logic: `Result`/`Option`, fuzzy matching, width formatting, text normalisation, the layering rule |
| `tests/component/` | a package against a real SQLite file: build, lexicon queries, use cases, fetch, schema drift |
| `tests/smoke/` | the `harald` command end to end, as a subprocess, at a fixed terminal width |
| `tests/tui/` | Textual screens (placeholders until the TUI lands) |

`tests/unit/test_layering.py` enforces the dependency direction described in
[Architecture](architecture.md): front-ends import only use cases.

## Fixtures

`tests/fixtures/en-edition.jsonl` and `de-edition.jsonl` are small hand-cut
wiktextract extracts. The `workspace` fixture in `tests/conftest.py` gzips
them into a temporary sources directory and writes a config pointing at it
with `build_min_entries = 0`; `built` runs a build on top. Nothing touches
your real `~/.local/share/harald`.

When a slice needs a new entry (a verb, an English word with translations),
add it to the fixture rather than building a second one. Keep lines that a
test deliberately drops (for example the "drop the last line" test) last.

## Skipped tests

Some tests are placeholders for later slices and are skipped with a TODO.
They mark where a future slice's test belongs; they are not failures.
