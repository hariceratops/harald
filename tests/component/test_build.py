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
