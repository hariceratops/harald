# [feat] English → German lookup grouped by sense

English → German lookup depends on German translations held in English-word entries. Depends on 005.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- The build keeps German translations, grouped by sense, from `lang_code == "en"` entries.
- `harald lookup --en use` lists German words under each English sense (e.g. "employ" → benutzen/verwenden; "consume" → verbrauchen).
