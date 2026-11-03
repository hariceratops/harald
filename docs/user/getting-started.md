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
uv run harald-cli build --fetch
```

`--fetch` downloads the source files into the sources directory, then the
build runs. The first build takes a while; later builds with unchanged
sources do nothing. See [Building the lexicon](build.md).

Free about 3.4 GB once the lexicon is built (a rebuild then needs `--fetch`
again):

```sh
uv run harald-cli prune
```

## Look something up

```sh
uv run harald-cli lookup lief          # inflected form → laufen
uv run harald-cli lookup --conj gehen  # every tense
uv run harald-cli lookup --en use      # English → German
```

## Browse in the TUI

```sh
uv run harald
```

| Key | Does |
|---|---|
| `l` | lookup |
| `s` | study due cards |
| `i` | sources |
| `q` | quit |

- In a lookup, `enter` searches, then pick a result to open the entry.
- `esc` or `/` on the results returns to the query.
- In an entry: `c` toggles full conjugation, `a` adds the word as cards, `esc` goes back.
- The layout adapts down to 40 columns.

Adding words and studying are in [Cards and study](study.md).

## See what you built from

```sh
uv run harald-cli info
```

Shows each source, its date, attribution and licence, and how complete the
data is (verbs with full Stammformen, nouns with a gender, senses with a
translated example).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | failed, or no match for the lookup |
| 2 | refused: bad config, or `lexicon.db` missing or at a different schema version (run `harald-cli build`) |
| 130 | interrupted |
