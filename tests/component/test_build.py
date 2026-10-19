import sqlite3
from pathlib import Path

import pytest

from harald.build.errors import SourceMissing, TooFewEntries
from harald.build.run import build
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
    assert list(built.config.staging_dir.iterdir()) == []


def test_only_the_importer_reads_source_files() -> None:
    src = Path(__file__).parents[2] / "src" / "harald"
    offenders = [
        p.relative_to(src)
        for p in src.rglob("*.py")
        if "build" not in p.relative_to(src).parts
        and ("gzip" in p.read_text() or "jsonl" in p.read_text())
    ]

    assert offenders == []


@pytest.mark.skip(reason="placeholder")
def test_placeholder() -> None:
    # TODO: byte-identical rebuild (004a), atomic failure, reverse-order task hook (004b)
    ...
