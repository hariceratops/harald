# Project: Harald

## Context
Harald is a personal, offline German vocabulary tool for a learner who picks German up from reading and conversation. It has a Textual TUI for study and browsing, plus plain CLI commands for lookup, the lexicon build and checks. It has two modes: dictionary lookup (German, German → German, or English → German, with gender, conjugation and examples), and phrase lookup (German/English sentence pairs). Anything worth keeping becomes a spaced-repetition card.
The lexicon is built on a desktop and pushed one way to a phone (Termux) with Syncthing. Study happens on the phone.
Prototype language: Python 3.12+, packaged with uv. A Rust rewrite of hot paths is anticipated later.
Data: Wiktionary extracts from kaikki.org (wiktextract JSONL, English and German editions) and Tatoeba sentence pairs, imported into `lexicon.db`, the built, read-only lexicon. The user's cards, decks and review log live in `learning.db`, which a rebuild never touches.
Target terminals: 40 columns minimum (phone, portrait); 80 or more on desktop and SSH. Output adapts to the terminal width.
Code is layered front-ends (`cli.py`, `tui/`) → `use_cases/` → `lexicon/`, `learning/`, `build/` → `infrastructure/`, `db/`, `core/`. Front-ends call only use cases, each a class with an `execute()` method; only the per-database packages touch a session, a connection or a file.

## Overrides

Broad exception catching at failure seams: `harald.infrastructure.uow.DbTransaction.execute` and `harald.infrastructure.transaction_context.DbTransactionContext.run` (the same two functions as kohle's Override), the upgrade step in `harald.learning.migrate`, the per-file download in `harald.build.fetch`, `harald.build.graph.run_job` and `harald.build.run.build` catch `Exception` rather than explicit types. This replaces the python-developer rule to catch explicit types. These are the seams where arbitrary failure is converted into an `Err` and partial state is rolled back or deleted: an open transaction, a half-applied migration, a `.part` download, staging and shard files, worker processes. An unanticipated exception escaping there would leave exactly the partial state the design exists to prevent. Ruff reports these as `BLE001`; they are deliberate. `BaseException` is never caught. Anywhere else, catch explicit types.

## Conventions

A function whose "no value" is an expected outcome (a parser skipping a line, a lookup that may find nothing) returns `harald.core.option.Option`, not `X | None`; failures that carry a reason stay `Result`. Record and model fields that map to nullable columns stay `X | None`, converted at the boundary with `to_optional()`.
