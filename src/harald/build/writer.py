import sqlite3
from collections.abc import Callable, Sequence
from pathlib import Path

from harald.build.jobs import CoverageCounts, ParseCounts
from harald.build.sources import SOURCES
from harald.build.stage import WRITER_DDL, WRITER_TABLES
from harald.db.connection import make_engine
from harald.lexicon.models import Base
from harald.lexicon.schema import SCHEMA_VERSION

# SQLite allows 10 attached databases by default; main and temp are two of them
_ATTACH_BATCH = 8


def open_staging(path: Path) -> sqlite3.Connection:
    """The only connection that writes the staging file. Its schema comes from the models."""
    engine = make_engine(path)
    Base.metadata.create_all(engine)
    engine.dispose()
    con = sqlite3.connect(path, isolation_level=None)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.executescript(WRITER_DDL)
    return con


def _merge_shards(
    con: sqlite3.Connection, shards: Sequence[str], merge: Callable[[list[str]], None]
) -> None:
    """Detaches after every batch, so no shard stays attached while workers write to it."""
    for i in range(0, len(shards), _ATTACH_BATCH):
        aliases: list[str] = []
        for n, shard in enumerate(shards[i : i + _ATTACH_BATCH]):
            con.execute(f"ATTACH ? AS s{n}", (shard,))
            aliases.append(f"s{n}")
        con.execute("BEGIN")
        merge(aliases)
        con.execute("COMMIT")
        for alias in aliases:
            con.execute(f"DETACH {alias}")


def merge_lexicon(
    con: sqlite3.Connection, shards: Sequence[str], parsed: dict[int, ParseCounts]
) -> None:
    """Ids come from rules: chunk offsets in seq order, sorted (lemma, pos) for headwords."""
    entry_off = sense_off = 0
    offsets = []
    for seq in sorted(parsed):
        offsets.append((seq, entry_off, sense_off))
        entry_off += parsed[seq].entries
        sense_off += parsed[seq].senses
    con.executemany("INSERT INTO offset_stage VALUES (?, ?, ?)", offsets)

    def collect_headwords(aliases: list[str]) -> None:
        for a in aliases:
            con.execute(f"INSERT INTO hw_stage SELECT DISTINCT lemma, pos FROM {a}.entry_stage")

    _merge_shards(con, shards, collect_headwords)
    con.execute("BEGIN")
    con.execute(
        "INSERT INTO headword SELECT row_number() OVER (ORDER BY lemma, pos), lemma, pos, 0 "
        "FROM (SELECT DISTINCT lemma, pos FROM hw_stage)"
    )
    con.execute("COMMIT")

    def merge(aliases: list[str]) -> None:
        for a in aliases:
            con.execute(
                "INSERT INTO entry "
                "SELECT o.entry_off + e.local_id, h.id, 0, e.gender, e.plural, e.ipa, "
                "e.separable_prefix "
                f"FROM {a}.entry_stage e JOIN offset_stage o ON o.seq = e.seq "
                "JOIN headword h ON h.lemma = e.lemma AND h.pos = e.pos "
                "ORDER BY e.seq, e.local_id"
            )
            con.execute(
                "INSERT INTO sense "
                "SELECT o.sense_off + s.local_id, o.entry_off + s.entry_local, s.ord, s.gloss, "
                "s.labels "
                f"FROM {a}.sense_stage s JOIN offset_stage o ON o.seq = s.seq "
                "ORDER BY s.seq, s.local_id"
            )
            # ids follow insertion order, which is shard order then source order
            con.execute(
                "INSERT INTO example (sense_id, ord, text, translation, kind, ref) "
                "SELECT o.sense_off + x.sense_local, x.ord, x.text, x.translation, x.kind, x.ref "
                f"FROM {a}.example_stage x JOIN offset_stage o ON o.seq = x.seq "
                "ORDER BY x.seq, x.rowid"
            )
            con.execute(
                "INSERT INTO verb_form "
                "SELECT o.entry_off + v.entry_local, v.slot, v.ord, v.form, v.variant "
                f"FROM {a}.verb_form_stage v JOIN offset_stage o ON o.seq = v.seq"
            )

    _merge_shards(con, shards, merge)
    con.execute("BEGIN")
    con.execute(
        "UPDATE entry SET ord = r.n FROM (SELECT id, row_number() OVER "
        "(PARTITION BY headword_id ORDER BY id) AS n FROM entry) r WHERE entry.id = r.id"
    )
    con.execute(
        "UPDATE headword SET richness = r.n FROM (SELECT e.headword_id AS hw, count(*) AS n "
        "FROM sense s JOIN entry e ON e.id = s.entry_id GROUP BY e.headword_id) r "
        "WHERE headword.id = r.hw"
    )
    con.execute("COMMIT")


def merge_keys(con: sqlite3.Connection, shards: Sequence[str]) -> None:
    """A lemma match (kind 0) wins over a form match (kind 1); form-of pairs need a headword."""

    def collect(aliases: list[str]) -> None:
        for a in aliases:
            con.execute(
                "INSERT INTO keyall_stage SELECT k.key, h.id, k.kind "
                f"FROM {a}.key_stage k JOIN headword h ON h.lemma = k.lemma AND h.pos = k.pos"
            )

    _merge_shards(con, shards, collect)
    con.execute("BEGIN")
    con.execute(
        "INSERT INTO search_key SELECT row_number() OVER (ORDER BY key), 'de', key "
        "FROM (SELECT DISTINCT key FROM keyall_stage)"
    )
    con.execute(
        "INSERT INTO key_headword SELECT s.id, k.headword_id, min(k.kind) "
        "FROM keyall_stage k JOIN search_key s ON s.key = k.key GROUP BY s.id, k.headword_id"
    )
    con.execute("COMMIT")


def merge_fuzzy(con: sqlite3.Connection, shards: Sequence[str]) -> None:
    def merge(aliases: list[str]) -> None:
        for a in aliases:
            con.execute(
                f"INSERT INTO fuzzy_delete SELECT d, key_id FROM {a}.fuzzy_stage ORDER BY d, key_id"
            )

    _merge_shards(con, shards, merge)


def finalize(
    con: sqlite3.Connection,
    parsed: dict[int, ParseCounts],
    source_files: Sequence[tuple[str, str, str, str]],
) -> None:
    """Writes the bookkeeping tables and drops the stage tables.

    Unmapped-tagset tallies merge by key, in chunk order. `source_files` rows are
    (filename, source, source_date, sha256).
    """
    cov = sum((p.coverage for p in parsed.values()), CoverageCounts())
    counts: dict[tuple[str, str], int] = {}
    examples: dict[tuple[str, str], tuple[str, str]] = {}
    for seq in sorted(parsed):
        for pos, tagset, n, word, form in parsed[seq].unmapped:
            counts[(pos, tagset)] = counts.get((pos, tagset), 0) + n
            examples.setdefault((pos, tagset), (word, form))
    con.execute("BEGIN")
    con.execute("INSERT INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
    con.executemany(
        "INSERT INTO source VALUES (?, ?, ?, ?)",
        [(s.name, s.title, s.licence, s.attribution) for s in SOURCES],
    )
    con.executemany("INSERT INTO source_file VALUES (?, ?, ?, ?)", source_files)
    con.executemany(
        "INSERT INTO build_stat VALUES (?, ?, ?)",
        [
            ("bad_lines.wiktionary-en", sum(p.bad_lines for p in parsed.values()), None),
            ("coverage.stammformen", cov.verbs_complete, cov.verbs),
            ("coverage.noun_gender", cov.nouns_gendered, cov.nouns),
            ("coverage.translated_example", cov.senses_translated, cov.senses),
        ],
    )
    con.executemany(
        "INSERT INTO unmapped_tagset VALUES (?, ?, ?, ?, ?)",
        [(*k, counts[k], *examples[k]) for k in sorted(counts)],
    )
    for table in WRITER_TABLES:
        con.execute(f"DROP TABLE {table}")
    con.execute("COMMIT")
