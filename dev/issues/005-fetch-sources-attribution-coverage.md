# [feat] Fetch sources, record their dates, show attribution, report coverage

Explicit download of the source files, with only the latest copy kept, plus the source metadata and the informational coverage report. Depends on 004a.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- `harald build --fetch` downloads `raw-wiktextract-data.jsonl.gz`, `de-extract.jsonl.gz` and the Tatoeba files, and keeps only the most recent copy of each.
- The English-edition dump is streamed and filtered; it is never decompressed to disk. Deprecated postprocessed per-language files are not used.
- `lexicon.db` records the date of each source, and Harald can display sources, dates and attribution (Wiktionary CC BY-SA 4.0, Tatoeba CC-BY).
- The build prints coverage figures: verbs with complete Stammformen, nouns with a gender, senses with a translated example.

## Review 2026-10-20
- `UNKNOWN_DATE` is defined twice, in `src/harald/build/fetch.py` and `src/harald/lexicon/info.py`. Keep one definition.
- The fetch tests run against a local HTTP server only, so the real download URLs in `SOURCE_FILES` have never been exercised. Add a check that they resolve (for example a HEAD request, kept out of the default test run).
