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

`l` opens lookup, `s` starts a study session, `i` shows the sources, `q`
quits. In a lookup, Enter searches, then pick a result to open the entry; `esc`
or `/` on the results returns to the query to fix a typo or search again. In an
entry, `c` toggles full conjugation, `a` adds the word as cards and `esc` goes
back. The layout adapts down to 40 columns.

Adding a word is a short wizard: pick English senses (each gives a German to
English and an English to German card), pick German definitions (each gives a
German to German card), then confirm with `c`. Senses that already have cards
are marked. `n` and `b` move between steps, `space` toggles a sense.

Studying shows the next due card. `space` reveals the answer, then `1` Again,
`2` Hard, `3` Good or `4` Easy grades it; each grade is saved at once. On
a touch screen the same actions are buttons. Adding a noun also adds an article
card: press `1` der, `2` die or `3` das, read the result, then `enter` or
`space` continues; a right answer counts as Good, a wrong one as Again. A noun
with no gender in the data is refused an article card, and the confirm step
says so. Adding a verb also adds a Stammformen card: type the 3rd person
singular present, the Präteritum and the Perfekt (`hat` or `ist` plus the
Partizip II), moving between the three fields with `enter`; `ae`, `oe`, `ue`
and `ss` are accepted for `ä`, `ö`, `ü` and `ß`. A verb whose data lacks a form
is refused the card and the confirm step names the missing forms. A summary of cards reviewed and
answered correctly ends the session. Cards live in `learning.db`, created on
first use; Harald refuses one written by a newer version.

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
