import pytest

from harald.lexicon.db import open_lexicon
from harald.lexicon.errors import LexiconMissing, NotALexicon, SchemaMismatch
from harald.lexicon.lookup import lookup_de
from tests.conftest import Workspace


def test_lookup_hund_returns_gender_plural_and_senses(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    result = lookup_de(lex, "hund")

    (hw,) = result.shown
    assert (hw.lemma, hw.pos) == ("Hund", "noun")
    assert (hw.entries[0].gender, hw.entries[0].plural) == ("m", "Hunde")
    assert hw.entries[0].senses[0] == "dog (Canis familiaris)"


def test_band_groups_both_entries_under_one_headword(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    (hw,) = lookup_de(lex, "Band").shown

    assert [e.gender for e in hw.entries] == ["n", "m"]


def test_no_match_is_empty(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    assert lookup_de(lex, "Zzzzzz").shown == ()


def test_missing_lexicon(workspace: Workspace) -> None:
    assert isinstance(open_lexicon(workspace.config.lexicon).unwrap_err(), LexiconMissing)


def test_not_a_lexicon(workspace: Workspace) -> None:
    path = workspace.root / "junk.db"
    path.write_bytes(b"this is not sqlite" * 100)

    assert isinstance(open_lexicon(path).unwrap_err(), NotALexicon)


def test_schema_mismatch_names_both_versions(built: Workspace) -> None:
    import sqlite3

    con = sqlite3.connect(built.config.lexicon)
    con.execute("UPDATE meta SET value = '99' WHERE key = 'schema_version'")
    con.commit()
    con.close()

    err = open_lexicon(built.config.lexicon).unwrap_err()

    assert isinstance(err, SchemaMismatch)
    assert "schema 99" in str(err)
    assert "needs schema 1" in str(err)


@pytest.mark.skip(reason="placeholder")
def test_placeholder() -> None:
    # TODO: lookup_en, phrase AND-tier ('repeats itself')
    ...
