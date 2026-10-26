import sqlite3
from datetime import UTC, datetime

from harald.core.option import Option
from harald.lexicon.model import Headword
from harald.use_cases.cards import CreateWordCards, PlanWordCards
from harald.use_cases.lexicon import LoadHeadword
from harald.use_cases.study import NextCard
from tests.conftest import Workspace

NOW = datetime(2026, 10, 26, 9, 0, tzinfo=UTC)


def _headword(ws: Workspace, lemma: str, pos: str = "noun") -> Headword:
    return LoadHeadword(ws.config).execute(lemma, pos).unwrap().unwrap()


def _rows(ws: Workspace, sql: str) -> list[tuple[object, ...]]:
    with sqlite3.connect(ws.config.learning_db) as db:
        return db.execute(sql).fetchall()


def test_each_english_sense_gives_a_de_en_and_an_en_de_card(built: Workspace) -> None:
    hund = _headword(built, "Hund")

    plan = PlanWordCards(built.config).execute(hund, 0, [0, 1], []).unwrap()

    assert [c.card_type for c in plan.cards] == [
        "meaning_de_en",
        "meaning_en_de",
        "meaning_de_en",
        "meaning_en_de",
    ]
    assert plan.word_hint.lemma == "Hund"
    assert plan.word_hint.discriminator == "m|Hunde"


def test_german_edition_senses_give_de_de_cards(built: Workspace) -> None:
    band = _headword(built, "Band")

    plan = PlanWordCards(built.config).execute(band, None, [], [(0, 0), (0, 1), (0, 2)]).unwrap()

    # (0, 1) is a heading line and cannot be picked
    assert [c.card_type for c in plan.cards] == ["meaning_de_de", "meaning_de_de"]
    assert plan.cards[0].content["definition"] == "dasjenige, was verbindet oder verknüpft"
    assert plan.word_hint.discriminator == ""


def test_german_only_headword_can_be_added(built: Workspace) -> None:
    fernweh = _headword(built, "Fernweh")

    plan = PlanWordCards(built.config).execute(fernweh, None, [], [(0, 0)]).unwrap()
    ids = CreateWordCards(built.config).execute(plan, NOW).unwrap()

    assert len(ids) == 1
    assert _rows(built, "SELECT lemma, pos, discriminator FROM word") == [("Fernweh", "noun", "")]


def test_cards_store_their_own_copy_and_no_lexicon_ids(built: Workspace) -> None:
    hund = _headword(built, "Hund")
    plan = PlanWordCards(built.config).execute(hund, 0, [0], []).unwrap()

    CreateWordCards(built.config).execute(plan, NOW).unwrap()

    card = next(c for c in plan.cards if c.card_type == "meaning_de_en")
    assert card.content["gloss"] == "dog (Canis familiaris)"
    assert card.content["gender"] == "m"
    assert card.content["example"]["translation"] == "The dog barks."
    stored = _rows(built, "SELECT card_type, content FROM card ORDER BY id")
    assert [t for t, _ in stored] == ["meaning_de_en", "meaning_en_de"]
    assert all('"gloss": "dog (Canis familiaris)"' in str(c) for _, c in stored)
    columns = [r[1] for r in _rows(built, "PRAGMA table_info(card)")]
    assert not any("lexicon" in c or "sense" in c for c in columns)


def test_creating_cards_is_one_audited_transaction(built: Workspace) -> None:
    hund = _headword(built, "Hund")
    plan = PlanWordCards(built.config).execute(hund, 0, [0], []).unwrap()

    ids = CreateWordCards(built.config).execute(plan, NOW).unwrap()

    assert len(ids) == 2
    assert _rows(built, "SELECT COUNT(*) FROM operation_groups") == [(1,)]
    assert _rows(built, "SELECT entity_type, action FROM operations ORDER BY id") == [
        ("word", "create"),
        ("card", "create"),
        ("card", "create"),
    ]
    assert _rows(built, "SELECT COUNT(*) FROM card WHERE last_review IS NULL") == [(2,)]


def test_already_live_cards_are_dropped_from_a_new_plan(built: Workspace) -> None:
    hund = _headword(built, "Hund")
    first = PlanWordCards(built.config).execute(hund, 0, [0], []).unwrap()
    CreateWordCards(built.config).execute(first, NOW).unwrap()

    again = PlanWordCards(built.config).execute(hund, 0, [0, 1], []).unwrap()

    assert len(again.cards) == 2
    assert {c.content["gloss"] for c in again.cards} == {"hound (any dog used for hunting)"}


def test_second_add_reuses_the_word_row(built: Workspace) -> None:
    hund = _headword(built, "Hund")
    for sense in (0, 1):
        plan = PlanWordCards(built.config).execute(hund, 0, [sense], []).unwrap()
        CreateWordCards(built.config).execute(plan, NOW).unwrap()

    assert _rows(built, "SELECT COUNT(*) FROM word") == [(1,)]
    assert _rows(built, "SELECT COUNT(*) FROM card") == [(4,)]


def test_homographs_get_separate_word_rows(built: Workspace) -> None:
    band = _headword(built, "Band")
    for entry in (0, 1):
        plan = PlanWordCards(built.config).execute(band, entry, [0], []).unwrap()
        CreateWordCards(built.config).execute(plan, NOW).unwrap()

    assert _rows(built, "SELECT discriminator FROM word ORDER BY id") == [
        ("n|Bänder",),
        ("m|Bände",),
    ]


def test_deleted_cards_are_not_dedupe_targets_nor_studied(built: Workspace) -> None:
    hund = _headword(built, "Hund")
    plan = PlanWordCards(built.config).execute(hund, 0, [0], []).unwrap()
    CreateWordCards(built.config).execute(plan, NOW).unwrap()
    with sqlite3.connect(built.config.learning_db) as db:
        db.execute("UPDATE card SET deleted_at = '2026-10-26 08:00:00'")

    again = PlanWordCards(built.config).execute(hund, 0, [0], []).unwrap()
    nxt = NextCard(built.config).execute(NOW)

    assert len(again.cards) == 2
    assert nxt.unwrap() == Option.none()
