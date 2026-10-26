# Build internals

The user-facing view is [Building the lexicon](../user/build.md). This page
is for changing the build.

## Shape: workers write shards, one writer merges

- The main process runs the scheduler, reads the sources and owns the only
  connection that writes the staging file.
- A process pool (`build_workers` processes) runs the CPU-heavy parse jobs.
  Each worker writes stage tables into its own shard file under the staging
  directory and returns only counts and timings.
- The writer `ATTACH`es the shards and merges them with `INSERT … SELECT`,
  assigning final ids by rule (sorted order), which is what makes the output
  byte-stable.

No row data crosses the process boundary by pickling; that was measured to
be the bottleneck.

## Graph

`en.read` / `en.parse`, `de.read` / `de.parse` and the Tatoeba parse run in
parallel. `lexicon.merge` then `keys.merge` assign ids, `fuzzy` jobs compute
the fuzzy index over key-id ranges in the pool, and `finalize` publishes.
The full node table is in design §3.7.

## Determinism

Everything that decides an id or an order is sorted on content, never on
arrival order: chunk boundaries and worker count do not change the output.
Any new table must follow the same rule, or a rebuild stops being
byte-identical and Syncthing resends the file.

## Schema versions

`lexicon/schema.py` holds `SCHEMA_VERSION`. Bump it whenever the lexicon
schema changes. An existing `lexicon.db` at another version is refused until
`harald build` is rerun, so a bump is user-visible; say so in the commit.

## Adding a parsed field

1. Extend the record in `build/records.py` and the stage table in
   `build/stage.py`.
2. Fill it in the `build/wiktextract_*.py` parser.
3. Merge it in `build/writer.py`.
4. Add the model in `lexicon/models.py` and bump `SCHEMA_VERSION`.
5. Add a line to the fixtures and a component test.
