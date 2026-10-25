import sqlite3

from harald.lexicon.schema import SCHEMA_VERSION
from harald.use_cases.lexicon import LookUpEnglish, LookUpGerman, QueryLexiconInfo
from tests.conftest import Workspace


def test_look_up_german_finds_hund(built: Workspace) -> None:
    result = LookUpGerman(built.config).execute("Hund").unwrap()

    assert result.shown


def test_query_lexicon_info_reports_the_schema_version(built: Workspace) -> None:
    info = QueryLexiconInfo(built.config).execute().unwrap()

    assert info.schema_version == SCHEMA_VERSION


def test_source_date_is_the_newest_trusted_one(built: Workspace) -> None:
    with sqlite3.connect(built.config.lexicon) as db:
        db.execute("DELETE FROM source_file WHERE source = 'tatoeba'")
        db.executemany(
            "INSERT INTO source_file (filename, source, source_date, sha256) VALUES (?, 'tatoeba', ?, 'x')",
            [("a", "2026-10-01"), ("b", "2026-10-17"), ("c", "unknown")],
        )
        db.execute("DELETE FROM source_file WHERE source = 'wiktionary-de'")
        db.execute(
            "INSERT INTO source_file (filename, source, source_date, sha256) VALUES ('d', 'wiktionary-de', 'unknown', 'x')"
        )

    info = {s.title: s.date for s in QueryLexiconInfo(built.config).execute().unwrap().sources}

    assert info["Tatoeba"] == "2026-10-17"
    assert info["Wiktionary (de)"] == "unknown"


def test_look_up_english_finds_use(built: Workspace) -> None:
    result = LookUpEnglish(built.config).execute("use").unwrap()

    assert result.shown
