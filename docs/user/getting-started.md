# Getting started

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Several GB of disk and bandwidth for the first fetch (the English Wiktionary
  extract alone is about 2.8 GB compressed)

## Install

```sh
git clone <repo-url> harald
cd harald
uv sync
```

## Build the lexicon

```sh
uv run harald build --fetch
```

`--fetch` downloads the source files into the sources directory, then the
build runs. The first build takes a while; later builds with unchanged
sources do nothing. See [Building the lexicon](build.md).

## Look something up

```sh
uv run harald lookup lief          # inflected form → laufen
uv run harald lookup --conj gehen  # every tense
uv run harald lookup --en use      # English → German
```

## Browse in the TUI

```sh
uv run harald        # same as: uv run harald tui
```

`l` opens lookup, `i` shows the sources, `q` quits. In a lookup, Enter
searches, then pick a result to open the entry; `c` toggles full conjugation
and `esc` goes back. The layout adapts down to 40 columns.

## See what you built from

```sh
uv run harald info
```

Shows each source, its date, attribution and licence, and how complete the
data is (verbs with full Stammformen, nouns with a gender, senses with a
translated example).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | failed, or no match for the lookup |
| 2 | refused: bad config, or `lexicon.db` missing or at a different schema version (run `harald build`) |
| 130 | interrupted |
