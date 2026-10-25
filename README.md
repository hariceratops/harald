# Harald

A personal, offline German vocabulary tool for a learner who picks German up
from reading and conversation rather than a course. Look a word up fast,
keep what is worth keeping as a spaced-repetition card.

The dictionary is built on a desktop from Wiktionary and Tatoeba data, then
pushed one way to a phone (Termux) with Syncthing. Study happens on the phone.

## Use case

- You meet a word or phrase while reading or talking. You look it up in a
  second: German, or English → German, with gender, plural, conjugation, IPA
  and examples.
- Often the lookup is all you need. When it isn't, the word or phrase becomes
  a card.
- Everything works offline after the data is built, and output adapts to the
  terminal width (40 columns on a phone, 80 or more on a desktop).

## Features

Working today:

- `harald build` builds `lexicon.db` from locally kept sources: deterministic,
  atomic, parallel. `--fetch` downloads new sources.
- `harald info` shows sources, dates, attribution and data coverage.
- `harald lookup WORD` finds German words, including inflected forms
  ("lief" finds *laufen*) and typos, with English glosses, German definitions,
  register labels, IPA and examples. `--conj` shows every tense.
- `harald lookup --en WORD` lists German words under each English sense.

Planned: Textual TUI, spaced-repetition cards (FSRS), Tatoeba phrase search,
`harald check`, backups. See the [roadmap](#roadmap).

## Quick start

```sh
uv sync
uv run harald build --fetch   # downloads several GB of sources; first build takes a while
uv run harald lookup lief
uv run harald lookup --en use
```

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

## Documentation

The full guide lives in [`docs/`](docs/index.md), split into a user guide and
a developer guide, and renders as a site with mkdocs-material:

```sh
pip install -r docs/requirements.txt

mkdocs serve -f docs/mkdocs.yml   # live-reloading site on http://127.0.0.1:8000
mkdocs build -f docs/mkdocs.yml   # or render once into site/
```

The pages are plain markdown with relative links, so they also read fine
straight from `docs/` on GitHub.

## Development

```sh
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

Test layers, build internals and workflow are in the
[developer guide](docs/developer/workflow.md). Project rules are in
[`AGENTS.md`](AGENTS.md); the spec, design and issues are under `dev/`.

## Roadmap

- [x] German lookup: nouns, glosses, gender, plural
- [x] Verb conjugation and inflected-form lookup
- [x] Fuzzy ranking
- [x] Deterministic, atomic, parallel lexicon build
- [x] Fetch sources; attribution and coverage report
- [x] Full English-edition entry (IPA, register, examples)
- [x] German-edition definitions and examples
- [x] English → German lookup
- [ ] TUI browsing, verified in Termux
- [ ] Add a word; meaning cards and study
- [ ] Article, Stammformen and per-tense conjugation cards
- [ ] German → German cards
- [ ] New-card cap and sibling burying
- [ ] Decks
- [ ] Edit, suspend, delete cards
- [ ] Tatoeba phrase search, saving phrases, writing your own in `$EDITOR`
- [ ] `harald check` after a rebuild
- [ ] `learning.db` backup
- [ ] Rust rewrite of hot paths (later)

## Licence and data

The code's licence is not yet chosen. Dictionary data comes from Wiktionary
(CC BY-SA 4.0, via wiktextract/kaikki.org) and Tatoeba (CC BY 2.0 FR). The
built `lexicon.db` is never redistributed. See
[Data and licences](docs/user/data.md).
