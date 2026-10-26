import pytest
from sqlalchemy import text

from harald.lexicon.db import open_lexicon
from harald.lexicon.errors import LexiconMissing, NotALexicon, SchemaMismatch
from harald.lexicon.lookup import _candidate_keys, lookup_de, lookup_en
from harald.lexicon.schema import SCHEMA_VERSION
from tests.conftest import Workspace


def test_lookup_hund_returns_gender_plural_and_senses(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    result = lookup_de(lex, "hund")

    (hw,) = result.shown
    assert (hw.lemma, hw.pos) == ("Hund", "noun")
    assert (hw.entries[0].gender, hw.entries[0].plural) == ("m", "Hunde")
    assert hw.entries[0].senses[0].gloss == "dog (Canis familiaris)"


def test_band_groups_all_entries_under_one_headword(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    (hw,) = lookup_de(lex, "Band").shown

    assert [e.gender for e in hw.entries] == ["n", "m", "f"]


def test_band_has_one_german_block_with_its_own_numbering(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    (hw,) = lookup_de(lex, "Band").shown

    assert [g.label for g in hw.german] == ["das Band", "das Band", "der Band", "die Band"]
    first = hw.german[0].senses
    assert [(s.index, s.gloss, s.labels) for s in first] == [
        ("1", "dasjenige, was verbindet oder verknüpft", ()),
        (None, "Plural »Bänder«:", ()),
        ("1a", "schmales Stück Stoff", ("colloquial",)),
    ]
    assert [(e.text, e.ref) for e in first[0].examples] == [
        ("Das Band der Freundschaft hielt jahrelang.", "Beispielquelle 1")
    ]
    assert [e.text for e in first[2].examples] == ["Sie trug ein Band im Haar.", "Das Band riss."]


def test_german_only_headword_has_no_english_entries(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    (hw,) = lookup_de(lex, "Fernweh").shown

    assert hw.entries == ()
    assert [g.label for g in hw.german] == ["das Fernweh"]


def test_headword_without_german_edition_data_has_no_german_block(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    (hw,) = lookup_de(lex, "Hund").shown

    assert hw.german == ()


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


def test_use_lists_german_words_under_each_english_sense(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    result = lookup_en(lex, "use")

    verb, noun = result.shown
    assert (verb.word, verb.pos) == ("use", "verb")
    assert [(g.sense, [t.german for t in g.words]) for g in verb.groups] == [
        ("employ, apply", ["benutzen", "verwenden"]),
        ("to exhaust the supply of, to consume", ["verbrauchen"]),
        ("to exploit", ["ausnutzen", "zum Vorwand nehmen"]),
    ]
    assert verb.groups[2].words[1].note == "use as a pretext"
    assert (noun.word, noun.pos) == ("use", "noun")
    assert [(g.sense, [(t.german, t.gender) for t in g.words]) for g in noun.groups] == [
        ("act of using", [("Benutzung", "f"), ("Gebrauch", "m")]),
        ("", [("Anwendung", "f")]),
    ]


def test_english_lookup_is_fuzzy(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    assert [w.word for w in lookup_en(lex, "usee").shown] == ["use", "use"]


def test_english_lookup_without_translations_finds_nothing(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    assert lookup_en(lex, "dog").shown == ()
    assert lookup_en(lex, "Hund").shown == ()


def test_german_lookup_ignores_english_keys(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()

    assert lookup_de(lex, "use").shown == ()


def test_fuzzy_candidates_are_driven_from_fuzzy_delete(built: Workspace) -> None:
    lex = open_lexicon(built.config.lexicon).unwrap()
    sql = str(_candidate_keys("de", "hund").compile(compile_kwargs={"literal_binds": True}))

    with lex.sessions() as session:
        plan = [row[3] for row in session.execute(text("EXPLAIN QUERY PLAN " + sql))]

    # scanning search_key by language first took ~4 s on the real 1.2M-key lexicon
    assert plan[0].startswith("SEARCH fuzzy_delete"), plan
