# [feat] Look up a German noun from a locally built lexicon

First end-to-end path through the system: an importer for `lang_code == "de"` entries from the kept local English-edition source, `harald build` producing `lexicon.db`, and a one-shot `harald lookup <word>` CLI command.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- `harald build` (no flags) reads the locally kept source files and writes `lexicon.db`.
- `harald lookup Hund` shows English glosses per sense, gender and plural.
- Lookup output fits the terminal width, down to 40 columns.
- The importer is the only module that reads source files; the rest of Harald reads only `lexicon.db`.
