# [feat] Two-way Tatoeba phrase search

Depends on 005 and 009.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- The build imports Tatoeba German/English sentence pairs into `lexicon.db`.
- Phrase search accepts English or German input, from the CLI and from the TUI.
- Matching finds the construction even when the exact wording misses: "repeats itself" finds "Geschichte wiederholt sich."
