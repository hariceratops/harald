import sqlite3
from collections.abc import Sequence
from pathlib import Path

from harald.build.records import EntryRecord, FormOfRecord
from harald.db.connection import make_engine
from harald.lexicon.fuzzy import fuzzy_deletes
from harald.lexicon.models import Base
from harald.lexicon.schema import SCHEMA_VERSION
from harald.text import fold


def write_lexicon(
    path: Path, records: Sequence[EntryRecord], form_ofs: Sequence[FormOfRecord]
) -> None:
    """Ids come from rules (sorted natural keys, source order), never from write order."""
    engine = make_engine(path)
    Base.metadata.create_all(engine)
    engine.dispose()

    headwords = sorted({(r.lemma, r.pos) for r in records})
    hw_id = {hw: i for i, hw in enumerate(headwords, 1)}
    richness = dict.fromkeys(headwords, 0)
    ord_in_hw = dict.fromkeys(headwords, 0)
    entry_rows: list[tuple[int, int, int, str, str | None, str | None]] = []
    sense_rows: list[tuple[int, int, int, str]] = []
    form_rows: list[tuple[int, str, int, str, str]] = []
    sense_id = 0
    for entry_id, r in enumerate(records, 1):
        hw = (r.lemma, r.pos)
        ord_in_hw[hw] += 1
        entry_rows.append(
            (entry_id, hw_id[hw], ord_in_hw[hw], r.gender, r.plural, r.separable_prefix)
        )
        for n, gloss in enumerate(r.glosses, 1):
            sense_id += 1
            sense_rows.append((sense_id, entry_id, n, gloss))
        richness[hw] += len(r.glosses)
        per_slot: dict[str, int] = {}
        for vf in r.verb_forms:
            per_slot[vf.slot] = per_slot.get(vf.slot, 0) + 1
            form_rows.append((entry_id, vf.slot, per_slot[vf.slot], vf.form, vf.variant))

    # (folded key, headword id) -> kind; a lemma match (0) wins over a form match (1)
    matches: dict[tuple[str, int], int] = {}
    for lemma, pos in headwords:
        matches[(fold(lemma), hw_id[(lemma, pos)])] = 0
    for r in records:
        for form in r.index_forms:
            matches.setdefault((fold(form), hw_id[(r.lemma, r.pos)]), 1)
    for fo in form_ofs:
        if (fo.lemma, fo.pos) in hw_id:
            matches.setdefault((fold(fo.form), hw_id[(fo.lemma, fo.pos)]), 1)
    keys = sorted({k for k, _ in matches})
    key_id = {k: i for i, k in enumerate(keys, 1)}
    key_rows = sorted((key_id[k], hw, kind) for (k, hw), kind in matches.items())

    fuzzy_rows = sorted((d, key_id[k]) for k in keys for d in fuzzy_deletes(k))

    counts: dict[tuple[str, str], int] = {}
    examples: dict[tuple[str, str], tuple[str, str]] = {}
    for r in records:
        for u in r.unmapped:
            counts[(u.pos, u.tagset)] = counts.get((u.pos, u.tagset), 0) + 1
            examples.setdefault((u.pos, u.tagset), (u.word, u.form))
    unmapped_rows = [(*k, counts[k], *examples[k]) for k in sorted(counts)]

    con = sqlite3.connect(path)
    try:
        con.execute("PRAGMA journal_mode=OFF")
        con.execute("PRAGMA synchronous=OFF")
        con.execute("INSERT INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
        con.executemany(
            "INSERT INTO headword VALUES (?, ?, ?, ?)",
            [(hw_id[hw], hw[0], hw[1], richness[hw]) for hw in headwords],
        )
        con.executemany("INSERT INTO entry VALUES (?, ?, ?, ?, ?, ?)", entry_rows)
        con.executemany("INSERT INTO sense VALUES (?, ?, ?, ?)", sense_rows)
        con.executemany("INSERT INTO verb_form VALUES (?, ?, ?, ?, ?)", form_rows)
        con.executemany("INSERT INTO unmapped_tagset VALUES (?, ?, ?, ?, ?)", unmapped_rows)
        con.executemany(
            "INSERT INTO search_key VALUES (?, 'de', ?)", [(i, k) for k, i in key_id.items()]
        )
        con.executemany("INSERT INTO key_headword VALUES (?, ?, ?)", key_rows)
        con.executemany("INSERT INTO fuzzy_delete VALUES (?, ?)", fuzzy_rows)
        con.commit()
    finally:
        con.close()
