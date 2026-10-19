import json
import sqlite3
from dataclasses import dataclass

from harald.build.records import EntryRecord
from harald.build.wiktextract_en import parse_line
from harald.lexicon.fuzzy import fuzzy_deletes
from harald.text import fold


@dataclass(frozen=True)
class ParseCounts:
    entries: int
    senses: int
    bad_lines: int
    # (pos, tagset, occurrences, example word, example form), in first-seen order
    unmapped: tuple[tuple[str, str, int, str, str], ...]


def parse_chunk(shard: sqlite3.Connection, seq: int, chunk: bytes) -> ParseCounts:
    """Writes one chunk's rows to the shard with chunk-local ids; the writer offsets them."""
    entry_rows: list[tuple[object, ...]] = []
    sense_rows: list[tuple[object, ...]] = []
    form_rows: list[tuple[object, ...]] = []
    keys: dict[tuple[str, str, str, int], None] = {}
    counts: dict[tuple[str, str], int] = {}
    examples: dict[tuple[str, str], tuple[str, str]] = {}
    bad_lines = 0
    senses = 0
    for line in chunk.split(b"\n"):
        if not line:
            continue
        try:
            record = parse_line(line)
        except json.JSONDecodeError:
            bad_lines += 1
            continue
        if record is None:
            continue
        if not isinstance(record, EntryRecord):
            keys[(fold(record.form), record.lemma, record.pos, 1)] = None
            continue
        local = len(entry_rows) + 1
        entry_rows.append(
            (seq, local, record.lemma, record.pos, record.gender, record.plural,
             record.separable_prefix)
        )  # fmt: skip
        for n, gloss in enumerate(record.glosses, 1):
            senses += 1
            sense_rows.append((seq, senses, local, n, gloss))
        per_slot: dict[str, int] = {}
        for vf in record.verb_forms:
            per_slot[vf.slot] = per_slot.get(vf.slot, 0) + 1
            form_rows.append((seq, local, vf.slot, per_slot[vf.slot], vf.form, vf.variant))
        keys[(fold(record.lemma), record.lemma, record.pos, 0)] = None
        for form in record.index_forms:
            keys[(fold(form), record.lemma, record.pos, 1)] = None
        for u in record.unmapped:
            counts[(u.pos, u.tagset)] = counts.get((u.pos, u.tagset), 0) + 1
            examples.setdefault((u.pos, u.tagset), (u.word, u.form))

    shard.executemany("INSERT INTO entry_stage VALUES (?, ?, ?, ?, ?, ?, ?)", entry_rows)
    shard.executemany("INSERT INTO sense_stage VALUES (?, ?, ?, ?, ?)", sense_rows)
    shard.executemany("INSERT INTO verb_form_stage VALUES (?, ?, ?, ?, ?, ?)", form_rows)
    shard.executemany(
        "INSERT INTO key_stage VALUES (?, ?, ?, ?, ?)",
        [(seq, k, lemma, pos, kind) for k, lemma, pos, kind in keys],
    )
    unmapped = tuple((*k, counts[k], *examples[k]) for k in counts)
    return ParseCounts(len(entry_rows), senses, bad_lines, unmapped)


def fuzzy_range(shard: sqlite3.Connection, keys: list[tuple[int, str]]) -> int:
    rows = [(d, key_id) for key_id, key in keys for d in fuzzy_deletes(key)]
    shard.executemany("INSERT INTO fuzzy_stage VALUES (?, ?)", rows)
    return len(rows)
