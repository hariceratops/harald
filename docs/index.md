# Harald

A personal, offline German vocabulary tool for a learner who picks German up
from reading, TV and conversation. It does two jobs:

- **Look things up fast** — a German word, an English word → German, and
  (planned) a phrase as German/English sentence pairs.
- **Turn what is worth keeping into spaced-repetition cards** and study them,
  with typed, checked answers.

## How this guide is organised

- **[Getting started](user/getting-started.md)** — install, build the lexicon,
  first lookup.
- **[Cards and study](user/study.md)** — add a word, notes, typed answers, grades.
- **[Lookup](user/lookup.md)** — what `harald-cli lookup` shows and how it matches.
- **[Building the lexicon](user/build.md)** — sources, fetching, determinism.
- **[Configuration](user/configuration.md)** — `config.toml` and file locations.
- **[Data and licences](user/data.md)** — where the data comes from and what you
  may do with it.

## Two databases

| File | Holds | Written by |
|---|---|---|
| `lexicon.db` | the dictionary: entries, translations, search keys | `harald-cli build`; read-only otherwise |
| `learning.db` | cards, review log (decks planned) | the study device only |

A rebuild replaces `lexicon.db` and never touches `learning.db`. Build the lexicon on
the device you study on.

## Terminal width

Output adapts to the terminal: 40 columns minimum (a phone in portrait), 80 or
more on desktop and SSH.

## About the examples

Every console session in this guide is run by the test suite against a small
sample lexicon built from a few hand-cut Wiktionary entries, at 80 columns, so
the output shows that lexicon's words, counts and coverage. Source dates read
2026-11-01 and build timings 0.0 s. A real lexicon gives longer entries.
