# Lookup

<!-- docs: illustration -->
```sh
harald-cli lookup [--conj] WORD...
harald-cli lookup --en WORD...
```

Several words are joined into one query.

## German lookup

`harald-cli lookup WORD` matches in three ways:

- **Exact and inflected forms.** "lief" finds *laufen*; the entry shows
  *läuft / lief / ist gelaufen*.
- **Fuzzy ranking.** Results are always ranked by similarity, so typos still
  find the word.
- **Umlaut folding.** Search keys fold `ä/ö/ü` to `ae/oe/ue`, so either
  spelling finds the word.

```console
$ harald-cli lookup lief
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
```

An entry shows, when the data has them:

- English glosses per sense, with register labels
- German-edition definitions, as a separate block with their own numbering
  (the two editions cannot be matched sense by sense)
- gender and plural
- conjugation (`--conj` expands every tense)
- IPA
- examples: English-edition examples with translations, per sense; German-edition examples in a separate block, marked untranslated

Quotation examples are shown verbatim, typos included.

If nothing matches, the command prints `No match for '...'` and exits 1.

## English → German

`harald-cli lookup --en use` lists German words under each English sense:

```console
$ harald-cli lookup --en use
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

Nouns carry their article. Only the best-matching tier is shown, capped at 20
results. Fuzzy matching applies here too.

## Width

Lines wrap to the terminal width with their indent kept, down to 40 columns.
