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

On the desktop, run the commands below through `uv run`, for example `uv run harald-cli lookup lief`.

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
harald-cli build --fetch   # about 11 minutes on a recent phone
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
harald-cli build --fetch
```

`--fetch` downloads the source files into the sources directory, then the
build runs. The first build takes a while; later builds with unchanged
sources do nothing. See [Building the lexicon](build.md).

Free about 3.4 GB once the lexicon is built (a rebuild then needs `--fetch`
again):

<!-- docs: illustration -->
```sh
harald-cli prune
```

## Look something up

```console
$ harald-cli lookup lief          # inflected form → laufen
lief → laufen (verb)
laufen  verb
läuft / lief / ist gelaufen
1. to walk; to jog; to run
          Präsens Präteritum Perfekt
ich       laufe   lief       bin gelaufen
du        läufst  liefst     bist gelaufen
er/sie/es läuft   lief       ist gelaufen
wir       laufen  liefen     sind gelaufen
ihr       lauft   lieft      seid gelaufen
sie/Sie   laufen  liefen     sind gelaufen
Imperativ: lauf, laufe! / lauft!
$ harald-cli lookup --conj laufen # every tense
laufen  verb
läuft / lief / ist gelaufen
1. to walk; to jog; to run
          Präsens Präteritum Perfekt
ich       laufe   lief       bin gelaufen
du        läufst  liefst     bist gelaufen
er/sie/es läuft   lief       ist gelaufen
wir       laufen  liefen     sind gelaufen
ihr       lauft   lieft      seid gelaufen
sie/Sie   laufen  liefen     sind gelaufen
          Konjunktiv II
ich       liefe
du        liefest
er/sie/es liefe
wir       liefen
ihr       liefet
sie/Sie   liefen
Imperativ: lauf, laufe! / lauft!
$ harald-cli lookup --en use      # English → German
use (verb)
  employ, apply
    benutzen
    verwenden
  to exhaust the supply of, to consume
    verbrauchen
  to exploit
    ausnutzen
    zum Vorwand nehmen  (use as a pretext)
use (noun)
  act of using
    die Benutzung
    der Gebrauch
  die Anwendung
```

## Browse in the TUI

```sh
harald
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

```console
$ harald-cli info
Lexicon schema 7
Sources
  Tatoeba
    unknown   CC BY 2.0 FR
    Tatoeba contributors (tatoeba.org)
  Wiktionary (de)
    2026-11-01   CC BY-SA 4.0
    Wiktionary contributors, extracted by wiktextract (kaikki.org)
  Wiktionary (en)
    2026-11-01   CC BY-SA 4.0
    Wiktionary contributors, extracted by wiktextract (kaikki.org)
Coverage (informational)
  verbs with complete Stammformen
    100.0 % (1/1)
  nouns with a gender
    0.0 % (0/0)
  senses with a translated example
    0.0 % (0/1)
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
