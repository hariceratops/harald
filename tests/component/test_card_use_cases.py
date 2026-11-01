import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from fsrs import Rating

from harald.core.option import Option
from harald.core.result import Result
from harald.learning.answers import ARTICLES
from harald.learning.content import CardPlan
from harald.learning.errors import LearningDbError
from harald.learning.study import SummaryCounts
from harald.lexicon.model import Headword, PrincipalParts
from harald.use_cases.cards import CreateWordCards, PlanWordCards
from harald.use_cases.lexicon import LoadHeadword
from harald.use_cases.study import (
    AnswerConjugation,
    AnswerMeaning,
    MeaningCheck,
    MeaningGraded,
    NextCard,
    NoArticleStored,
    SessionSummary,
)
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

    assert [c.card_type for c in again.cards] == ["meaning_de_en", "meaning_en_de"]
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


def test_a_noun_with_no_sense_picked_gets_no_cards(built: Workspace) -> None:
    hund = _headword(built, "Hund")

    plan = PlanWordCards(built.config).execute(hund, 0, [], []).unwrap()

    assert plan.cards == ()
    assert plan.refusals == ()


def test_a_verb_gets_one_stammformen_card_with_its_copied_content(built: Workspace) -> None:
    anrufen = _headword(built, "anrufen", "verb")

    plan = PlanWordCards(built.config).execute(anrufen, 0, [0], []).unwrap()

    stamm = [c for c in plan.cards if c.card_type == "stammformen"]
    assert [c.content for c in stamm] == [
        {
            "infinitive": "anrufen",
            "hint": "to call; to phone",
            "pres3sg": "ruft an",
            "preterite": "rief an",
            "participle": "angerufen",
            "auxiliaries": ["haben"],
            "separable_prefix": "an",
        }
    ]
    assert plan.refusals == ()


def test_a_second_sense_added_later_does_not_add_a_second_stammformen_card(
    built: Workspace,
) -> None:
    laufen = _headword(built, "laufen", "verb")
    entry = laufen.entries[0]
    two = replace(
        laufen,
        entries=(
            replace(entry, senses=(*entry.senses, replace(entry.senses[0], gloss="to race"))),
        ),
    )
    for sense in (0, 1):
        plan = PlanWordCards(built.config).execute(two, 0, [sense], []).unwrap()
        CreateWordCards(built.config).execute(plan, NOW).unwrap()

    assert _rows(built, "SELECT COUNT(*) FROM card WHERE card_type = 'stammformen'") == [(1,)]


def test_a_verb_with_missing_forms_refuses_stammformen_and_names_them(
    built: Workspace,
) -> None:
    anrufen = _headword(built, "anrufen", "verb")
    entry = anrufen.entries[0]
    gaps = replace(entry, principal_parts=PrincipalParts("ruft an", None, "angerufen", ()))
    gappy = replace(anrufen, entries=(gaps,))

    plan = PlanWordCards(built.config).execute(gappy, 0, [0], []).unwrap()

    assert [c.card_type for c in plan.cards] == ["meaning_de_en", "meaning_en_de"]
    assert [(r.card_type, r.missing) for r in plan.refusals] == [
        ("stammformen", ("Präteritum", "auxiliary"))
    ]
    assert len(CreateWordCards(built.config).execute(plan, NOW).unwrap()) == 2


def test_a_verb_with_no_principal_parts_names_every_form(built: Workspace) -> None:
    anrufen = _headword(built, "anrufen", "verb")
    bare = replace(anrufen, entries=(replace(anrufen.entries[0], principal_parts=None),))

    plan = PlanWordCards(built.config).execute(bare, 0, [0], []).unwrap()

    assert [r.missing for r in plan.refusals] == [
        ("Präsens", "Präteritum", "Partizip II", "auxiliary")
    ]


def _conjugation(plan: CardPlan) -> dict[str, dict[str, object]]:
    return {c.content["slot"]: c.content for c in plan.cards if c.card_type == "conjugation"}


def test_each_chosen_tense_gives_a_card_per_person(built: Workspace) -> None:
    anrufen = _headword(built, "anrufen", "verb")

    plan = PlanWordCards(built.config).execute(anrufen, 0, [0], [], ["ind.pres"]).unwrap()

    cards = _conjugation(plan)
    assert list(cards) == [f"ind.pres.{p}" for p in ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl")]
    assert cards["ind.pres.1sg"] == {
        "infinitive": "anrufen",
        "hint": "to call; to phone",
        "separable_prefix": "an",
        "slot": "ind.pres.1sg",
        "forms": ["rufe an"],
    }
    assert plan.refusals == ()


def test_conjugation_cards_do_not_need_a_sense(built: Workspace) -> None:
    anrufen = _headword(built, "anrufen", "verb")

    plan = PlanWordCards(built.config).execute(anrufen, 0, [], [], ["ind.pret"]).unwrap()

    assert [c.card_type for c in plan.cards] == ["conjugation"] * 6
    assert plan.cards[0].content["hint"] == "to call; to phone"
    assert plan.refusals == ()


def test_a_third_person_only_verb_gets_those_cards_and_names_the_rest(
    built: Workspace,
) -> None:
    anrufen = _headword(built, "anrufen", "verb")
    forms = {s: f for s, f in anrufen.entries[0].conjugation.items() if s.endswith(".3sg")}
    nieseln = replace(anrufen, entries=(replace(anrufen.entries[0], conjugation=forms),))

    plan = PlanWordCards(built.config).execute(nieseln, 0, [0], [], ["ind.pres"]).unwrap()

    assert list(_conjugation(plan)) == ["ind.pres.3sg"]
    assert [(r.card_type, r.missing) for r in plan.refusals] == [
        ("conjugation", ("Präsens (ich, du, wir, ihr, sie/Sie)",))
    ]
    assert len(CreateWordCards(built.config).execute(plan, NOW).unwrap()) == 4


def test_a_verb_without_a_table_refuses_every_chosen_tense_as_all_persons(
    built: Workspace,
) -> None:
    anrufen = _headword(built, "anrufen", "verb")
    bare = replace(anrufen, entries=(replace(anrufen.entries[0], conjugation={}),))

    plan = PlanWordCards(built.config).execute(bare, 0, [0], [], ["ind.pres", "ind.pret"]).unwrap()

    assert _conjugation(plan) == {}
    assert [r.missing for r in plan.refusals] == [
        ("Präsens (all persons)", "Präteritum (all persons)")
    ]


def test_a_german_only_verb_refuses_its_tenses(built: Workspace) -> None:
    anrufen = _headword(built, "anrufen", "verb")
    german_only = replace(anrufen, entries=())

    plan = PlanWordCards(built.config).execute(german_only, None, [], [], ["ind.perf"]).unwrap()

    assert [r.missing for r in plan.refusals] == [("Perfekt (all persons)",)]


def test_a_two_auxiliary_perfekt_slot_keeps_both_forms(built: Workspace) -> None:
    anrufen = _headword(built, "anrufen", "verb")
    forms = {**anrufen.entries[0].conjugation, "ind.perf.1sg": ("habe gefahren", "bin gefahren")}
    fahren = replace(anrufen, entries=(replace(anrufen.entries[0], conjugation=forms),))

    plan = PlanWordCards(built.config).execute(fahren, 0, [0], [], ["ind.perf"]).unwrap()

    assert _conjugation(plan)["ind.perf.1sg"]["forms"] == ["habe gefahren", "bin gefahren"]


def test_a_conjugation_card_is_not_added_twice_whatever_its_forms_or_hint(
    built: Workspace,
) -> None:
    anrufen = _headword(built, "anrufen", "verb")
    first = PlanWordCards(built.config).execute(anrufen, 0, [0], [], ["ind.pres"]).unwrap()
    CreateWordCards(built.config).execute(first, NOW).unwrap()
    entry = anrufen.entries[0]
    changed = replace(
        anrufen,
        entries=(
            replace(
                entry,
                senses=(replace(entry.senses[0], gloss="to ring"),),
                conjugation={**entry.conjugation, "ind.pres.1sg": ("rufe telefonisch an",)},
            ),
        ),
    )

    again = PlanWordCards(built.config).execute(changed, 0, [0], [], ["ind.pres", "ind.pret"])

    slots = list(_conjugation(again.unwrap()))
    assert slots == [f"ind.pret.{p}" for p in ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl")]


def test_answering_a_conjugation_card_grades_it_by_the_check(built: Workspace) -> None:
    anrufen = _headword(built, "anrufen", "verb")
    plan = PlanWordCards(built.config).execute(anrufen, 0, [], [], ["ind.pres"]).unwrap()
    CreateWordCards(built.config).execute(plan, NOW).unwrap()
    rows = _rows(built, "SELECT json_extract(content, '$.slot'), id FROM card")
    ids = {str(slot): int(str(i)) for slot, i in rows}
    answer = AnswerConjugation(built.config, enable_fuzzing=False)

    right = answer.execute(ids["ind.pres.1sg"], "rufe an", NOW, "s1").unwrap()
    wrong = answer.execute(ids["ind.pres.2sg"], "rufst", NOW, "s1").unwrap()

    assert (right.label, right.correct, right.expected) == ("ich", True, "rufe an")
    assert (wrong.label, wrong.correct, wrong.expected) == ("du", False, "rufst an")
    assert _rows(built, "SELECT rating, answer FROM review ORDER BY id") == [
        (3, "rufe an"),
        (1, "rufst"),
    ]


def _add(
    ws: Workspace,
    lemma: str,
    pos: str,
    entry: int | None,
    en: list[int],
    de: list[tuple[int, int]],
    card_type: str,
) -> int:
    plan = PlanWordCards(ws.config).execute(_headword(ws, lemma, pos), entry, en, de).unwrap()
    CreateWordCards(ws.config).execute(plan, NOW).unwrap()
    rows = _rows(
        ws, f"SELECT id FROM card WHERE card_type = '{card_type}' ORDER BY id DESC LIMIT 1"
    )
    return int(str(rows[0][0]))


def _meaning(
    ws: Workspace, card_id: int, given: str, at: datetime = NOW, first_try: str | None = None
) -> Result[MeaningCheck, LearningDbError]:
    return AnswerMeaning(ws.config, enable_fuzzing=False).execute(
        card_id, given, first_try, at, "s1", 1500
    )


def test_a_right_typed_meaning_is_graded_good(built: Workspace) -> None:
    card = _add(built, "Hund", "noun", 0, [0], [], "meaning_en_de")

    checked = _meaning(built, card, "der Hund").unwrap()

    assert isinstance(checked, MeaningGraded)
    assert (checked.rating, checked.word, checked.article) == (Rating.Good, "right", "right")
    assert _rows(built, "SELECT rating, answer, duration_ms FROM review") == [(3, "der Hund", 1500)]


def test_a_wrong_article_is_graded_hard_into_the_review_row(built: Workspace) -> None:
    card = _add(built, "Hund", "noun", 0, [0], [], "meaning_en_de")

    checked = _meaning(built, card, "die Hund").unwrap()

    assert isinstance(checked, MeaningGraded)
    assert (checked.rating, checked.article, checked.expected) == (Rating.Hard, "wrong", "der Hund")
    assert _rows(built, "SELECT rating, answer FROM review") == [(2, "die Hund")]
    assert SessionSummary(built.config).execute("s1").unwrap() == SummaryCounts(1, 1)


def test_a_wrong_word_is_graded_again_and_counts_as_missed(built: Workspace) -> None:
    card = _add(built, "Hund", "noun", 0, [0], [], "meaning_en_de")

    checked = _meaning(built, card, "der Hnd").unwrap()

    assert isinstance(checked, MeaningGraded)
    assert checked.rating == Rating.Again
    assert _rows(built, "SELECT rating, answer FROM review") == [(1, "der Hnd")]
    assert SessionSummary(built.config).execute("s1").unwrap() == SummaryCounts(1, 0)


def test_an_empty_answer_is_graded_again(built: Workspace) -> None:
    card = _add(built, "Hund", "noun", 0, [0], [], "meaning_en_de")

    _meaning(built, card, "").unwrap()

    assert _rows(built, "SELECT rating, answer FROM review") == [(1, "")]


def test_a_wrong_article_twice_running_escalates_to_again(built: Workspace) -> None:
    card = _add(built, "Hund", "noun", 0, [0], [], "meaning_en_de")
    later = NOW + timedelta(days=1)

    first = _meaning(built, card, "Hund").unwrap()
    second = _meaning(built, card, "die Hund", later).unwrap()
    third = _meaning(built, card, "der Hund", later + timedelta(days=1)).unwrap()

    assert [c.rating for c in (first, second, third) if isinstance(c, MeaningGraded)] == [
        Rating.Hard,
        Rating.Again,
        Rating.Good,
    ]
    assert _rows(built, "SELECT rating FROM review ORDER BY id") == [(2,), (1,), (3,)]


def test_a_wrong_word_between_resets_the_escalation(built: Workspace) -> None:
    card = _add(built, "Hund", "noun", 0, [0], [], "meaning_en_de")

    _meaning(built, card, "Hund").unwrap()
    _meaning(built, card, "Katze", NOW + timedelta(days=1)).unwrap()
    third = _meaning(built, card, "Hund", NOW + timedelta(days=2)).unwrap()

    assert isinstance(third, MeaningGraded)
    assert third.rating == Rating.Hard


def test_a_noun_without_gender_typed_with_an_article_is_refused_and_writes_nothing(
    built: Workspace,
) -> None:
    card = _add(built, "Fernweh", "noun", None, [], [(0, 0)], "meaning_de_de")
    before = _rows(built, "SELECT due, fsrs_state, last_review FROM card")

    checked = _meaning(built, card, "das Fernweh").unwrap()

    assert checked == NoArticleStored()
    assert _rows(built, "SELECT COUNT(*) FROM review") == [(0,)]
    assert _rows(built, "SELECT due, fsrs_state, last_review FROM card") == before
    assert SessionSummary(built.config).execute("s1").unwrap() == SummaryCounts(0, 0)


def test_a_noun_without_gender_typed_alone_is_good(built: Workspace) -> None:
    card = _add(built, "Fernweh", "noun", None, [], [(0, 0)], "meaning_de_de")

    checked = _meaning(built, card, "Fernweh").unwrap()

    assert isinstance(checked, MeaningGraded)
    assert (checked.rating, checked.article) == (Rating.Good, "not_asked")


def test_a_proper_noun_ignores_the_article(built: Workspace) -> None:
    card = _add(built, "Berlin", "name", 0, [0], [], "meaning_en_de")

    with_article = _meaning(built, card, "der Berlin").unwrap()
    alone = _meaning(built, card, "Berlin", NOW + timedelta(days=1)).unwrap()

    assert [c.rating for c in (with_article, alone) if isinstance(c, MeaningGraded)] == [
        Rating.Good,
        Rating.Good,
    ]


def test_a_homograph_accepts_the_gender_of_its_own_entry(built: Workspace) -> None:
    band = _add(built, "Band", "noun", 0, [0], [], "meaning_en_de")
    entry_gender = str(
        _rows(built, f"SELECT json_extract(content, '$.gender') FROM card WHERE id = {band}")[0][0]
    )

    checked = _meaning(built, band, f"{ARTICLES[entry_gender]} Band").unwrap()

    assert isinstance(checked, MeaningGraded)
    assert checked.rating == Rating.Good


def test_a_retry_stores_both_tries_and_is_capped_at_hard(built: Workspace) -> None:
    card = _add(built, "Hund", "noun", 0, [0], [], "meaning_en_de")

    checked = _meaning(built, card, "der Hund", first_try="Katze").unwrap()

    assert isinstance(checked, MeaningGraded)
    assert checked.rating == Rating.Hard
    assert _rows(built, "SELECT rating, answer FROM review") == [(2, "Katze | der Hund")]


def test_answering_an_unknown_card_is_an_error(built: Workspace) -> None:
    assert _meaning(built, 999, "Hund").is_err
