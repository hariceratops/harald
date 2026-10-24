import sqlite3

from harald.lexicon.db import Lexicon, open_lexicon
from harald.lexicon.schema import SCHEMA_VERSION
from harald.use_cases.lexicon import LookUpGerman, QueryLexiconInfo
from tests.conftest import Workspace


def _lex(ws: Workspace) -> Lexicon:
    return open_lexicon(ws.config.lexicon).unwrap()


def test_look_up_german_finds_hund(built: Workspace) -> None:
    result = LookUpGerman(_lex(built)).execute("Hund")

    assert result.shown


def test_query_lexicon_info_reports_the_schema_version(built: Workspace) -> None:
    info = QueryLexiconInfo(_lex(built)).execute()

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

    info = {s.title: s.date for s in QueryLexiconInfo(_lex(built)).execute().sources}

    assert info["Tatoeba"] == "2026-10-17"
    assert info["Wiktionary (de)"] == "unknown"
