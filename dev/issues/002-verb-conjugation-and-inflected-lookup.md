# [feat] Verb conjugation and inflected-form lookup

Map the flat `forms` list of `{form, tags[]}` onto conjugation tables, dropping bookkeeping rows, and build an index from inflected forms back to the lemma. Depends on 001.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- `harald lookup lief` shows laufen, including läuft / lief / ist gelaufen.
- `harald lookup laufen` shows a conjugation table that fits the terminal width, down to 40 columns; separable verbs are shown split (ruft an).
- Tag sets the importer cannot map are recorded in `lexicon.db`.
