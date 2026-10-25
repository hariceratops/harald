# [feat] Fuzzy-ranked German lookup

Results are always ranked fuzzily so typos still find the word. Depends on 002.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- `harald lookup schnel` returns schnell as the top result.
- Exact and lemma matches rank above fuzzy matches.
