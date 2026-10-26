# [feat] German-edition definitions and examples in lookup

Import `de-extract` and relate it to English-edition words by (word, pos), never per sense. Depends on 005.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- Lookup shows German-edition monolingual definitions as their own block with their own sense numbering, grouped once per (word, pos). Band (3 English-edition and 4 German-edition entries) is the test case.
- Lookup shows German-edition examples in a separate per-word block marked untranslated.
- No attempt is made to match German-edition senses to English-edition senses.

## Review 2026-10-25
- `cli.py:9` and `cli.py:36-45` import and call `open_lexicon` directly (used by `info` and `lookup`, `cli.py:107`, `cli.py:122`), against AGENTS.md "front-ends call only use cases". Move opening the lexicon into `LookUpGerman` and `QueryLexiconInfo`, returning Result like `BuildLexicon`, and remove `harald.lexicon.db` from the allowlist in `tests/unit/test_layering.py:6-14`. Introduced in fbe6864.
- `core/option.py` (7e5c00e) has no consumer in `src/`; only `tests/unit/test_option.py` uses it. Resolved in 107a334 by adopting it, not deleting it: it now replaces the `X | None` returns that mean "nothing here" (parsers, slot lookups, `osa_within`, `_german_examples`). Nullable record fields stay `X | None`, converted with `to_optional()`.
