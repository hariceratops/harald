# Project: Harald

## Context
Harald is a personal, offline German vocabulary tool for a learner who picks German up from reading and conversation. It has a Textual TUI for study and browsing, plus plain CLI commands for lookup, the lexicon build and checks. It has two modes: dictionary lookup (German, German → German, or English → German, with gender, conjugation and examples), and phrase lookup (German/English sentence pairs). Anything worth keeping becomes a spaced-repetition card.
The app is mobile first: the lexicon is built where Harald runs, with `harald-cli build --fetch`, and study happens on the phone (Termux). The desktop works the same way.
Prototype language: Python 3.12+, packaged with uv. A Rust rewrite of hot paths is anticipated later.
Data: Wiktionary extracts from kaikki.org (wiktextract JSONL, English and German editions) and Tatoeba sentence pairs, imported into `lexicon.db`, the built, read-only lexicon. The user's cards, decks and review log live in `learning.db`, which a rebuild never touches.
Target terminals: 40 columns minimum (phone, portrait); 80 or more on desktop and SSH. Output adapts to the terminal width.
Code is layered front-ends (`cli.py`, `tui/`) → `use_cases/` → `lexicon/`, `learning/`, `build/` → `infrastructure/`, `db/`, `core/`. Front-ends call only use cases, each a class with an `execute()` method; only the per-database packages touch a session, a connection or a file.

## Overrides

Broad exception catching at failure seams: `harald.infrastructure.uow.DbTransaction.execute` and `harald.infrastructure.transaction_context.DbTransactionContext.run` (the same two functions as kohle's Override), the upgrade step in `harald.learning.migrate`, the per-file download in `harald.build.fetch`, `harald.build.graph.run_job` and `harald.build.run.build` catch `Exception` rather than explicit types. This replaces the python-developer rule to catch explicit types. These are the seams where arbitrary failure is converted into an `Err` and partial state is rolled back or deleted: an open transaction, a half-applied migration, a `.part` download, staging and shard files, worker processes. An unanticipated exception escaping there would leave exactly the partial state the design exists to prevent. Ruff reports these as `BLE001`; they are deliberate. `BaseException` is never caught. Anywhere else, catch explicit types.

## Conventions

A function whose "no value" is an expected outcome (a parser skipping a line, a lookup that may find nothing) returns `harald.core.option.Option`, not `X | None`; failures that carry a reason stay `Result`. Record and model fields that map to nullable columns stay `X | None`, converted at the boundary with `to_optional()`.

## Documentation

`docs/` is the user-facing description of behaviour, published to GitHub Pages from `main`; the README is only a pitch that points to it. A slice that changes user-visible behaviour updates the matching page in the same PR.

Build the guide and the local-only developer notes (`dev/docs/`, never built in CI or published) strictly; `serve` instead of `build` reads either live:

```sh
uv run --with-requirements docs/requirements.txt mkdocs build --strict -f docs/mkdocs.yml
uv run --with-requirements docs/requirements.txt mkdocs build --strict -f dev/docs/mkdocs.yml
```

CI runs `uv run --frozen pytest tests/docs` and the guide's strict build on every PR, and publishes only from `main` when both pass.

Every `console` block in `docs/` and `README.md` is run by `uv run pytest`, against the sample lexicon built from `docs/examples/`. The module docstring of `tests/docs/checker.py` defines the example syntax, the `docs:` options and the key tables. Command output is shown only in console blocks. When an example's output changes, fix the page; never loosen the example.

The README roadmap follows the briefs in `dev/inbox/`.

Personal data: the user's own cards, notes, decks, review history, the words they are learning, and their own setup (devices, paths, sync arrangements) never appear in user-facing docs. Examples use the sample lexicon's words and invented notes.
