# Lookup

```sh
harald lookup [--conj] WORD...
harald lookup --en WORD...
```

Several words are joined into one query.

## German lookup

`harald lookup WORD` matches in three ways:

- **Exact and inflected forms.** "lief" finds *laufen*; the entry shows
  *läuft / lief / ist gelaufen*.
- **Fuzzy ranking.** Results are always ranked by similarity, so typos still
  find the word.
- **Umlaut folding.** Search keys fold `ä/ö/ü` to `ae/oe/ue`, so either
  spelling finds the word.

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

`harald lookup --en use` lists German words under each English sense:

```text
use (verb)
  employ, apply
    benutzen
    verwenden
  to exhaust the supply of, to consume
    verbrauchen
```

Nouns carry their article. Only the best-matching tier is shown, capped at 20
results. Fuzzy matching applies here too.

## Width

Lines wrap to the terminal width with their indent kept, down to 40 columns.
