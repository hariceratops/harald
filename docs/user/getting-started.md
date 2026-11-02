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
are marked. `n` and `b` move between steps, `space` toggles a sense; each step says so
under its title. Confirming with nothing ticked says that nothing was ticked.

Studying shows the next due card. On a German to English card, type your
answer first and press `enter`: the card then shows what you typed above the real answer, and `1` Again or `2` Good grades it; each grade
is saved at once. Pressing `enter` with nothing typed counts as not knowing
and is graded Again. An English to German card is checked for you: it shows
the English gloss, its labels and the part of speech, and you type the German
word. A German to German card is checked the same way: it shows the German
definition and the part of speech, and you type the word it defines. Press `enter` (or tap `Check (enter)`) to check. A noun with a known gender
is typed with its article, as in `der Hund`; the field reads `Art. + noun`,
and any of the word's genders counts. Other words, proper nouns and
nouns with no stored gender included, are typed alone and the field reads
`Word`; an article typed there is refused with a message, ungraded, and you
type again. The right word is graded Good. A typing slip is forgiven and
graded Good too, as long as it is not itself a German word: one wrong,
missing, extra or swapped letter in a word of 5 to 9 letters, two in a longer
word, none in a word of up to 4 letters; wrong capitalisation alone counts,
unless the other case is another word (`essen` for `Essen`), which is graded
Again. The card shows the right spelling. If you type another German word of
the same part of speech, nothing is graded yet: the field clears and a hint
shows the first letter and the length, as in `Another noun. Try: H _ _ _`,
and you get one more try. Right on that try is graded Hard; anything else is
graded Again. A wrong or missing article still
passes but is graded Hard, and a second wrong article in a row on the same
card is graded Again. Any other answer, or none, is graded Again. The card
then shows the verdict, what you typed and the right word, and `enter` moves
on. `ae`, `oe`, `ue` and `ss` are accepted for `ä`, `ö`, `ü` and `ß`, and a
verb may be typed with a leading `sich`. Checking needs `lexicon.db`; study
returns to Home with a message if it has gone. On a touch screen the same
actions are buttons. Adding a verb also adds a
Stammformen card: type the 3rd person singular present, the Präteritum and the Perfekt (`hat` or `ist`
plus the Partizip II), moving between the three fields with `enter`; `ae`,
`oe`, `ue` and `ss` are accepted for `ä`, `ö`, `ü` and `ß`, and the card
says so under the fields. A verb whose data lacks a form is refused the card
and the confirm step names the missing forms. Neither card hints that a verb
is separable; typing the form without the prefix counts as wrong. Adding
a verb also offers a tense step, with no tense ticked: each ticked tense
makes six conjugation cards, one per person (ich, du, er/sie/es, wir, ihr,
sie/Sie). Tenses that already have cards are marked, and a later add can
request more tenses without picking a sense again.  A conjugation card shows
the verb, the tense and one person; type the form without the pronoun, such
as `rufe an`. A missing form refuses only its own person and tense, and the
confirm step names it. A summary of cards reviewed and answered correctly
ends the session. Cards live in `learning.db`, created on first use; Harald
refuses one written by a newer version.

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
