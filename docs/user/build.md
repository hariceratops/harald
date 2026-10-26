# Building the lexicon

```sh
harald build [--fetch] [--force]
```

`harald build` reads the locally kept source files and writes `lexicon.db`.

## Sources

| File | Source | Used for |
|---|---|---|
| `raw-wiktextract-data.jsonl.gz` | Wiktionary, English edition (kaikki.org) | German entries; German translations from English words |
| `de-extract.jsonl.gz` | Wiktionary, German edition (kaikki.org) | German definitions and extra examples |
| `deu_sentences.tsv.bz2`, `eng_sentences.tsv.bz2`, `deu-eng_links.tsv.bz2` | Tatoeba | sentence pairs (phrase mode, planned) |

The deprecated per-language postprocessed kaikki files are not used.

## Fetching

Nothing is downloaded unless you pass `--fetch`. Each file is downloaded to a
`.part` file and renamed when complete; an unchanged file is reported as
`already current`. Only the most recent download is kept, and its date is
recorded in the lexicon.

## Guarantees

- **Deterministic.** A rebuild from the same files produces identical bytes.
  If the result is identical, the published file is left untouched, so
  Syncthing has nothing to resend.
- **Atomic.** An interrupted build (Ctrl-C, crash, disk full) leaves the
  previous `lexicon.db` intact; staging files are removed and a partial file
  never reaches the phone.
- **Versioned.** If the lexicon's schema version differs from the one Harald
  expects, Harald refuses to start and names both versions. The fix is
  `harald build`.
- **Sanity check.** A build with fewer than `build_min_entries` entries is
  rejected rather than published.

## Flags

- `--fetch` — download the sources first.
- `--force` — rebuild even if nothing changed.

The build runs as a parallel task graph; `build_workers` sets the number of
worker processes. It prints per-stage timings, the entry and bad-line counts,
and the same report as `harald info`.
