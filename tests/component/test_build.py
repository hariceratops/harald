import dataclasses
import gzip
import hashlib
import sqlite3
from pathlib import Path

import pytest

from harald.build.errors import (
    BuildFailed,
    BuildLocked,
    SourceMissing,
    StagingNotSameFilesystem,
    TooFewEntries,
)
from harald.build.publish import build_lock
from harald.build.run import build
from harald.build.sources import EN_FILENAME
from harald.config import Config
from tests.conftest import Workspace


def _rows(db: Path, sql: str) -> list[tuple[object, ...]]:
    con = sqlite3.connect(db)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_build_writes_lexicon_from_local_source(workspace: Workspace) -> None:
    res = build(workspace.config)

    assert res.is_ok
    assert res.unwrap().entries == 8
    assert res.unwrap().bad_lines == 1
    assert workspace.config.lexicon.exists()


def test_hund_entry_has_gender_plural_and_glosses(built: Workspace) -> None:
    db = built.config.lexicon
    entry = _rows(
        db,
        "SELECT e.gender, e.plural FROM entry e JOIN headword h ON h.id = e.headword_id "
        "WHERE h.lemma = 'Hund'",
    )
    glosses = _rows(
        db,
        "SELECT s.gloss FROM sense s JOIN entry e ON e.id = s.entry_id "
        "JOIN headword h ON h.id = e.headword_id WHERE h.lemma = 'Hund' ORDER BY s.ord",
    )

    assert entry == [("m", "Hunde")]
    assert [g[0] for g in glosses][0] == "dog (Canis familiaris)"
    assert len(glosses) == 4


def test_gender_falls_back_to_head_template(built: Workspace) -> None:
    rows = _rows(
        built.config.lexicon,
        "SELECT e.gender, e.plural FROM entry e JOIN headword h ON h.id = e.headword_id "
        "WHERE h.lemma = 'Band' ORDER BY e.ord",
    )

    assert rows == [("n", "Bänder"), ("m", "Bände")]


def test_form_of_character_and_non_german_entries_are_skipped(built: Workspace) -> None:
    lemmas = {r[0] for r in _rows(built.config.lexicon, "SELECT lemma FROM headword")}

    assert lemmas == {
        "Hund",
        "Band",
        "Berlin",
        "Aufenthaltsgenehmigung",
        "laufen",
        "anrufen",
        "schnell",
    }


def test_proper_nouns_are_imported(built: Workspace) -> None:
    assert _rows(built.config.lexicon, "SELECT pos FROM headword WHERE lemma = 'Berlin'") == [
        ("name",)
    ]


def test_missing_source_is_an_error(workspace: Workspace) -> None:
    (workspace.config.sources_dir / "raw-wiktextract-data.jsonl.gz").unlink()

    res = build(workspace.config)

    assert isinstance(res.unwrap_err(), SourceMissing)


def test_too_few_entries_refuses_to_publish(workspace: Workspace) -> None:
    config = Config(
        workspace.config.lexicon, workspace.config.sources_dir, workspace.config.staging_dir, 50_000
    )

    res = build(config)

    assert isinstance(res.unwrap_err(), TooFewEntries)
    assert not config.lexicon.exists()


def test_build_leaves_no_staging_files(built: Workspace) -> None:
    assert list(built.config.staging_dir.glob("*.db")) == []


def test_only_the_importer_reads_source_files() -> None:
    src = Path(__file__).parents[2] / "src" / "harald"
    offenders = [
        p.relative_to(src)
        for p in src.rglob("*.py")
        if "build" not in p.relative_to(src).parts
        and ("gzip" in p.read_text() or "jsonl" in p.read_text())
    ]

    assert offenders == []


def _stat_and_hash(path: Path) -> tuple[int, str]:
    return path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def test_forced_rebuild_leaves_published_file_untouched(built: Workspace) -> None:
    before = _stat_and_hash(built.config.lexicon)

    res = build(built.config, force=True)

    assert res.is_ok
    assert not res.unwrap().published
    assert _stat_and_hash(built.config.lexicon) == before


def test_rebuild_with_nothing_new_takes_the_fast_path(built: Workspace) -> None:
    before = _stat_and_hash(built.config.lexicon)

    res = build(built.config)

    assert res.unwrap().unchanged
    assert _stat_and_hash(built.config.lexicon) == before


def test_changed_source_republishes(built: Workspace) -> None:
    source = built.config.sources_dir / EN_FILENAME
    lines = gzip.decompress(source.read_bytes()).splitlines(keepends=True)
    source.write_bytes(gzip.compress(b"".join(lines[:-1])))

    res = build(built.config)

    assert res.is_ok
    assert not res.unwrap().unchanged


def test_interrupted_build_keeps_previous_lexicon(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = _stat_and_hash(built.config.lexicon)

    def interrupt(*_: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("harald.build.run._vacuum_into", interrupt)
    with pytest.raises(KeyboardInterrupt):
        build(built.config, force=True)

    assert _stat_and_hash(built.config.lexicon) == before
    assert list(built.config.staging_dir.glob("*.db")) == []


def test_crashed_build_keeps_previous_lexicon(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = _stat_and_hash(built.config.lexicon)

    def crash(*_: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("harald.build.run._vacuum_into", crash)
    res = build(built.config, force=True)

    assert isinstance(res.unwrap_err(), BuildFailed)
    assert _stat_and_hash(built.config.lexicon) == before
    assert list(built.config.staging_dir.glob("*.db")) == []


def test_concurrent_build_is_refused(workspace: Workspace) -> None:
    workspace.config.staging_dir.mkdir()
    with build_lock(workspace.config.staging_dir):
        res = build(workspace.config)

    assert isinstance(res.unwrap_err(), BuildLocked)


def test_staging_on_another_filesystem_is_refused(
    workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("harald.build.run._same_filesystem", lambda a, b: False)

    res = build(workspace.config)

    assert isinstance(res.unwrap_err(), StagingNotSameFilesystem)
    assert not workspace.config.lexicon.exists()


def _built_hash(workspace: Workspace, workers: int) -> str:
    config = dataclasses.replace(workspace.config, build_workers=workers)
    assert build(config, force=True).is_ok
    return hashlib.sha256(config.lexicon.read_bytes()).hexdigest()


@pytest.mark.parametrize("workers", [1, 2, 3])
def test_output_is_byte_identical_for_any_worker_count(
    workspace: Workspace, workers: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    inline = _built_hash(workspace, 0)
    workspace.config.lexicon.unlink()

    # one line per chunk, so chunks finish out of order across workers
    monkeypatch.setattr("harald.build.run.CHUNK_BYTES", 1)

    assert _built_hash(workspace, workers) == inline
    assert list(workspace.config.staging_dir.glob("*.db")) == []


def test_ids_follow_source_order_whatever_the_chunking(
    workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("harald.build.run.CHUNK_BYTES", 1)
    config = dataclasses.replace(workspace.config, build_workers=2)
    assert build(config).is_ok

    order = _rows(
        config.lexicon,
        "SELECT h.lemma FROM entry e JOIN headword h ON h.id = e.headword_id ORDER BY e.id",
    )

    assert [r[0] for r in order][:2] == ["Hund", "Band"]


@pytest.mark.parametrize("workers", [0, 2])
def test_failing_task_publishes_nothing_and_cleans_up(built: Workspace, workers: int) -> None:
    source = built.config.sources_dir / EN_FILENAME
    poisoned = b'{"lang_code": "de", "pos": "noun", "senses": [{"glosses": ["x"]}]}\n'
    source.write_bytes(gzip.compress(gzip.decompress(source.read_bytes()) + poisoned))
    before = _stat_and_hash(built.config.lexicon)
    config = dataclasses.replace(built.config, build_workers=workers)

    res = build(config, force=True)

    assert isinstance(res.unwrap_err(), BuildFailed)
    assert "en.parse" in str(res.unwrap_err())
    assert _stat_and_hash(config.lexicon) == before
    assert list(config.staging_dir.glob("*.db")) == []


def test_interrupt_in_a_pooled_build_leaves_no_files(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = _stat_and_hash(built.config.lexicon)

    def interrupt(*_: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("harald.build.run.merge_keys", interrupt)
    config = dataclasses.replace(built.config, build_workers=2)
    with pytest.raises(KeyboardInterrupt):
        build(config, force=True)

    assert _stat_and_hash(config.lexicon) == before
    assert list(config.staging_dir.glob("*.db")) == []


def test_build_reports_per_node_timings(workspace: Workspace) -> None:
    report = build(workspace.config).unwrap()

    assert [t.node for t in report.timings] == [
        "en.read+parse",
        "lexicon.merge",
        "keys.merge",
        "fuzzy",
        "fuzzy.merge",
        "finalize",
    ]


def test_lexicon_records_sources_dates_and_attribution(built: Workspace) -> None:
    db = built.config.lexicon

    sources = _rows(db, "SELECT name, licence, attribution FROM source ORDER BY name")
    files = _rows(db, "SELECT filename, source, source_date, sha256 FROM source_file")

    assert [s[:2] for s in sources] == [
        ("tatoeba", "CC BY 2.0 FR"),
        ("wiktionary-de", "CC BY-SA 4.0"),
        ("wiktionary-en", "CC BY-SA 4.0"),
    ]
    assert sources[0][2] == "Tatoeba contributors (tatoeba.org)"
    assert files == [
        (
            EN_FILENAME,
            "wiktionary-en",
            "unknown",
            hashlib.sha256((built.config.sources_dir / EN_FILENAME).read_bytes()).hexdigest(),
        )
    ]


def test_build_records_coverage(built: Workspace) -> None:
    stats = dict(
        (r[0], r[1:])
        for r in _rows(
            built.config.lexicon, "SELECT metric, numerator, denominator FROM build_stat"
        )
    )

    # nouns: Hund, Band x2, Aufenthaltsgenehmigung; Berlin is a proper noun and left out
    assert stats["coverage.noun_gender"] == (4, 4)
    assert stats["coverage.stammformen"] == (2, 2)
    assert stats["coverage.translated_example"][0] == 1
    assert stats["bad_lines.wiktionary-en"] == (1, None)


def test_fetch_failure_aborts_the_build_and_keeps_the_lexicon(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    from harald.build import run
    from harald.build.errors import FetchFailed
    from harald.core.result import Result

    before = _stat_and_hash(built.config.lexicon)
    monkeypatch.setattr(run, "fetch_all", lambda _: Result.err(FetchFailed("x", "offline")))

    res = build(built.config, fetch=True)

    assert isinstance(res.unwrap_err(), FetchFailed)
    assert _stat_and_hash(built.config.lexicon) == before
    assert list(built.config.staging_dir.glob("*.db")) == []
