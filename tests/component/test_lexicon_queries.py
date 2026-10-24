import pytest

from harald.lexicon.db import open_lexicon
from harald.lexicon.errors import LexiconMissing, NotALexicon, SchemaMismatch
from harald.lexicon.lookup import lookup_de
from harald.lexicon.schema import SCHEMA_VERSION
from tests.conftest import Workspace


def test_lookup_hund_returns_gender_plural_and_senses(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    result = lookup_de(lex, "hund")

    (hw,) = result.shown
    assert (hw.lemma, hw.pos) == ("Hund", "noun")
    assert (hw.entries[0].gender, hw.entries[0].plural) == ("m", "Hunde")
    assert hw.entries[0].senses[0].gloss == "dog (Canis familiaris)"


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
    assert f"needs schema {SCHEMA_VERSION}" in str(err)


@pytest.mark.skip(reason="placeholder")
def test_placeholder() -> None:
    # TODO: lookup_en, phrase AND-tier ('repeats itself')
    ...


def test_typo_finds_the_word(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    result = lookup_de(lex, "schnel")

    assert result.shown[0].lemma == "schnell"


def test_transposition_finds_band(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    assert lookup_de(lex, "bnad").shown[0].lemma == "Band"


def test_exact_form_match_ranks_above_fuzzy_lemma(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    result = lookup_de(lex, "hunde")

    assert result.shown[0].lemma == "Hund"
    assert result.shown[0].via_form == "hunde"


def test_fuzzy_match_is_not_reported_as_a_form(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    assert lookup_de(lex, "hudn").shown[0].via_form is None


def test_hund_carries_ipa_labels_and_examples(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    (hw,) = lookup_de(lex, "Hund").shown
    entry = hw.entries[0]

    assert entry.ipa == "/hʊnt/"
    assert entry.senses[2].labels == ("derogatory",)
    first = entry.senses[0].examples
    assert [(e.text, e.translation, e.quotation) for e in first] == [
        ("Der Hund bellt.", "The dog barks.", False),
        ("Hund.", None, False),
    ]
    (quotation,) = entry.senses[1].examples
    assert (quotation.text, quotation.ref, quotation.quotation) == (
        "Der  Hundt lief  daron.",
        "Anon., 1850",
        True,
    )
