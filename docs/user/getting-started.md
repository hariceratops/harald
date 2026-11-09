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

## Install on Termux

The phone builds its own lexicon and needs no dev tools. uv cannot download a
Python on Android, so use the one Termux ships.

<!-- docs: illustration -->
```sh
pkg install python git
export UV_PYTHON_DOWNLOADS=never
git clone <repo-url> harald
cd harald
uv sync --no-dev           # skips pytest, ruff and mypy, which build slowly here
source .venv/bin/activate
harald-cli build --fetch   # about 11 minutes on a Pixel 9
harald-cli prune --yes     # frees about 3.4 GB of sources
harald
```

- Run `harald` and `harald-cli` directly once the venv is active.
- Do not use `uv run` there: it syncs the dev tools back in. If you must sync
  again, use `uv sync --no-dev`.
- Put `export UV_PYTHON_DOWNLOADS=never` and the `source` line in `~/.bashrc` to
  skip typing them.
- If Python is older than 3.12, run `pkg upgrade`.

## Build the lexicon

<!-- docs: illustration -->
```sh
uv run harald-cli build --fetch
```

`--fetch` downloads the source files into the sources directory, then the
build runs. The first build takes a while; later builds with unchanged
sources do nothing. See [Building the lexicon](build.md).

Free about 3.4 GB once the lexicon is built (a rebuild then needs `--fetch`
again):

<!-- docs: illustration -->
```sh
uv run harald-cli prune
```

## Look something up

<!-- docs: illustration -->
```sh
uv run harald-cli lookup lief          # inflected form → laufen
uv run harald-cli lookup --conj gehen  # every tense
uv run harald-cli lookup --en use      # English → German
```

## Browse in the TUI

```sh
uv run harald
```

<!-- docs: keys home -->
| Key | Does |
|---|---|
| `l` | lookup |
| `s` | study due cards |
| `i` | sources |
| `q` | quit |

- In a lookup, `enter` searches, then pick a result to open the entry.
- `esc` or `/` on the results returns to the query.

<!-- docs: keys lookup -->
| Key | Does |
|---|---|
| `enter` | search, then open the highlighted result |
| `/` | back to the query |
| `esc` | from the results, back to the query; otherwise back |

- In an entry: `c` toggles full conjugation, `a` adds the word as cards, `esc` goes back.

<!-- docs: keys entry -->
| Key | Does |
|---|---|
| `c` | all tenses |
| `a` | add the word as cards |
| `esc` | back |

- The layout adapts down to 40 columns.

Adding words and studying are in [Cards and study](study.md).

## See what you built from

<!-- docs: illustration -->
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
