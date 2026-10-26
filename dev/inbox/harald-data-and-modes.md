# Harald: data source, learning modes, CLI-first

## Goal

A personal tool for a B1 learner who picks German up from reading and
conversation rather than a course. Words and phrases come from real
encounters and are curated by hand into a deck; the tool's job is to make
looking things up fast and to turn what's worth keeping into spaced-repetition
cards. It is CLI-first and offline after a data sync.

The problem behind it: the existing design (`german_learning_app_design.md`)
put most of its weight on a hand-written Wikitext parser for `dewiktionary`,
and treated learning as word-only. Both turned out to be the wrong centre of
gravity. German Wiktionary defines words in German, so the schema's
`text_en NOT NULL` and the German→English card type had no data behind them.
And the way this learner actually needs to produce German, phrases such as
"and the pattern then repeats itself", had no place in a schema where every
card points at a dictionary headword.

## Two modes

**Dictionary mode.** Look up a word (German, or English → German) and see
glosses, gender, plural, conjugation, IPA and examples. Optionally add it to
the deck; often the lookup is the whole point and nothing is added. Cards
drawn from words cover meaning, gender/article and conjugation.

**Phrase mode.** Put in an English or German phrase and get back German/English
sentence pairs. Save a pair to the deck, either one found by search or one
typed by hand when search misses. Phrase cards are English → German
production, self-graded.

## Considerations surfaced

- **Data comes from kaikki.org / wiktextract, not our own parser.** Checked
  against real entries (`laufen`, `Hund`, `anrufen`, `verschlimmbessern`,
  `Aufenthaltsgenehmigung`, `use`):
  - English-edition German entries carry English glosses per sense, register
    tags, IPA, etymology, synonyms, and full inflection. That includes all
    nine planned tenses with auxiliaries composed in, and separable verbs in
    both split ("rufe an") and subordinate-clause ("anrufe") forms.
  - Examples are attached per sense, mostly with English translations and
    bold offsets on the headword. They are thin (1–9 per word).
  - The German edition (`kaikki.org/dewiktionary/`) has many more examples
    (31 for `laufen`; all five citations for `Aufenthaltsgenehmigung`), but
    they are untranslated, and its sense numbering differs from the English
    edition's. Plan: import both, join on (word, pos), and attach German-edition
    examples at word level.
  - `type: quotation` examples quote published sources verbatim, typos
    included (two misspellings appear in the `Aufenthaltsgenehmigung`
    citations). Show them, but don't derive cloze answers from them.
- **The importer becomes the real work.** `forms` is a flat list of
  `{form, tags[]}`, with bookkeeping rows (`table-tags`,
  `inflection-template`, `error-unknown-tag`), variant markers (`rare`,
  `formal`, `nonstandard`), duplicates, and tense tag names that aren't the
  obvious guess. Gender sits in sense tags and the head template, not a
  top-level field. The old `parse_errors` idea survives in a smaller form:
  record the tag sets the importer couldn't map.
- **Keep the importer as the only module that knows where the data came
  from.** Pin a dated snapshot and re-import deliberately. If kaikki or
  wiktextract goes away, the fallbacks in order are: keep the last snapshot
  (vocabulary doesn't go stale quickly); run or fork wiktextract, which is
  MIT-licensed; and only then write our own parser.
- **Licensing.** Kaikki states no data licence; wiktextract's MIT covers its
  code only. The data inherits Wiktionary's CC BY-SA 4.0 (and GFDL for older
  text). This is our reading, not something kaikki states. Shipping a built
  DB means CC BY-SA for that file. Having sync download on the user's machine
  avoids redistributing it. Tatoeba is CC-BY.
- **Tatoeba moves from P4 to the core of phrase mode,** as a two-way
  sentence-pair search rather than example enrichment. Live checks:
  "pattern repeats" got 0 hits, "repeats itself" got 4 ("History repeats
  itself" → "Geschichte wiederholt sich."), and "make use of" got 49.
  Exact technical phrasing often misses, but the construction is found by
  searching the core of the phrase. Matching would use English-side
  stemming plus `form_index` on the German side.
- **Context-based English → German lookup is nearly free.** The English
  edition's English entries list German translations grouped by sense: *use*
  "employ, apply" → benutzen/verwenden/gebrauchen/nutzen, "consume" →
  verbrauchen, "exploit" → ausnutzen. Combined with Tatoeba sentences, this
  shows which word is chosen in context. It was parked during the
  discussion and then judged cheap enough to take off hold.
- **The schema has to admit phrases.** `cards.word_id NOT NULL` can't hold a
  phrase. Proposed: a `phrases` table, plus a nullable `phrase_id` on `cards`
  with a check that exactly one of `word_id` or `phrase_id` is set. P0
  creates these tables, so this needs deciding before P0.
- **Production cards are self-graded.** "Und das Muster wiederholt sich dann"
  and "und dann wiederholt sich das Muster" are both right; typed exact-match
  would mark one of them wrong.
- **CLI-first.** `textual` leaves v1. A line-based study loop suits SSH on a
  phone. Conjugation tables have to fit 80 columns in plain stdout, and that
  is the first place the CLI will feel cramped.

- **Name: Harald**, the German form of Harold. It replaces GermanDeck and the
  `gd` command. It's free on PyPI and crates.io (as of 2026-10-18), so the
  Python prototype and the Rust rewrite can share it. `hari`, `sepp`,
  `kalle` and `fritz` were taken.

## Directions rejected

- **Hand-written two-layer Wikitext parser over `dewiktionary`.** Writing a
  parser was only the price of getting the data, not a goal, and wiktextract
  already pays it. It's kept as the last fallback.
- **`Renderer` abstraction over `textual`.** Textual's model doesn't map onto
  curses or ratatui, and the Rust rewrite would redo the UI anyway. CLI-first
  makes the question moot.
- **Built-in curated decks (Goethe A1, Everyday life…) as the main way
  cards arrive.** They have no source and unclear rights, and this learner
  builds decks from their own encounters. Decks stay as an import/export
  format.
- **A unified "note" model for everything.** It was proposed and judged
  overcomplicated. Two plain modes, word and phrase, are the cleaner cut.
- **Offline machine translation for phrases.** It's a different project. On a
  search miss, the learner brings the German.

## Open questions

- How complete is the data across the whole dataset? Measure on the full
  German JSONL: verbs with a complete Präsens indicative, nouns with a gender
  tag, senses with at least one translated `example`. The answer decides
  whether the hand-curated seed CSV of irregular verbs is still needed.
- How should German-edition examples and sense-indexed translations be
  reconciled with English-edition senses, if at all beyond word-level
  attachment?
- Conjugation drill granularity: one card per (verb, tense, person) is about
  27k cards for 500 verbs. Which tenses and persons actually get cards, and
  are sibling cards buried?
- Umlaut and ß input on phone keyboards: accept ae/oe/ue/ss as equivalents?
  This only matters where answers are typed.
- When phrase search misses, what makes typing your own pair painless in a
  CLI?
- Should a saved phrase link to the dictionary words it contains (via
  `form_index`), so lookups show "you have a phrase using this"? Is that
  worth it in v1?
- Still open from the original design: FSRS parameter scope (global vs
  per-deck), and typo-tolerant search (trigram vs a fuzzy layer).
