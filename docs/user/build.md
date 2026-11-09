# Building the lexicon

`harald-cli build` reads the locally kept source files and writes `lexicon.db`.
Every option is in the [command reference](../reference.md#build).

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

## Freeing disk space

The sources are about 3.4 GB and stay after a build, so you can rebuild
without downloading again.

<!-- docs: illustration -->
```sh
harald-cli prune          # lists the files, asks, then deletes them
harald-cli prune --yes    # no question
```

- Deletes only the files `--fetch` writes, plus their `.meta.json` and
  `.part` leftovers. Other files in `sources_dir` stay.
- Refuses unless `lexicon.db` opens, so you never delete your only way to
  rebuild.
- Refuses while a build is running.
- Never touches `lexicon.db` or `learning.db`.
- The next rebuild needs `harald-cli build --fetch` and downloads about 3 GB
  again. It may get a newer dump, so the lexicon can differ.
- Without the sources, `harald-cli build` says so and points at `--fetch`.

## Guarantees

- **Deterministic.** A rebuild from the same files produces identical bytes.
  If the result is identical, the published file is left untouched.
- **Atomic.** An interrupted build (Ctrl-C, crash, disk full) leaves the
  previous `lexicon.db` intact; staging files are removed and a partial file
  never reaches the phone.
- **Versioned.** If the lexicon's schema version differs from the one Harald
  expects, Harald refuses to start and names both versions. The fix is
  `harald-cli build`.
- **Sanity check.** A build with fewer than `build_min_entries` entries is
  rejected rather than published.

A forced rebuild from unchanged sources shows the first guarantee:

```console
$ harald-cli build --force
rebuilt identical bytes: published file left untouched
  en.read+parse     0.0 s (jobs 0.0 s)
  de.read+parse     0.0 s (jobs 0.0 s)
  lexicon.merge     0.0 s
  keys.merge        0.0 s
  fuzzy             0.0 s (jobs 0.0 s)
  fuzzy.merge       0.0 s
  finalize          0.0 s
1 entries, 0 bad lines
~/.local/share/harald/lexicon.db (0.1 MB) in 0.0 s
Lexicon schema 7
Sources
  Tatoeba
    unknown   CC BY 2.0 FR
    Tatoeba contributors (tatoeba.org)
  Wiktionary (de)
    2026-11-01   CC BY-SA 4.0
    Wiktionary contributors, extracted by wiktextract (kaikki.org)
  Wiktionary (en)
    2026-11-01   CC BY-SA 4.0
    Wiktionary contributors, extracted by wiktextract (kaikki.org)
Coverage (informational)
  verbs with complete Stammformen
    100.0 % (1/1)
  nouns with a gender
    0.0 % (0/0)
  senses with a translated example
    0.0 % (0/1)
```

## What a build does

The build runs as a parallel task graph; `build_workers` sets the number of
worker processes. It prints per-stage timings, the entry and bad-line counts,
and the same report as `harald-cli info`.
