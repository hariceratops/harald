import sqlite3
from datetime import UTC, datetime, timedelta

from harald.use_cases.cards import CreateWordCards, PlanWordCards
from harald.use_cases.lexicon import LookUpGerman
from harald.use_cases.study import (
    AnswerMeaning,
    Grade,
    MeaningGraded,
    NextCard,
    SessionSummary,
    TryAgain,
)
from tests.conftest import Workspace

T0 = datetime(2026, 10, 26, 9, 0, tzinfo=UTC)


def test_lookup_add_study_and_summarise(built: Workspace) -> None:
    shown = LookUpGerman(built.config).execute("Hund").unwrap().shown[0]
    plan = PlanWordCards(built.config).execute(shown, 0, [0], []).unwrap()
    CreateWordCards(built.config).execute(plan, T0).unwrap()
    grade = Grade(built.config, enable_fuzzing=False)

    now = T0
    seen = []
    while (card := NextCard(built.config).execute(now).unwrap()).is_some:
        c = card.unwrap()
        seen.append(c.card_type)
        grade.execute(c.id, 4, now, "s1").unwrap()
        now += timedelta(seconds=20)

    assert sorted(seen) == ["meaning_de_en", "meaning_en_de"]
    summary = SessionSummary(built.config).execute("s1").unwrap()
    assert (summary.reviewed, summary.correct) == (2, 2)


def test_each_grade_is_durable_before_the_next_card_is_asked_for(built: Workspace) -> None:
    shown = LookUpGerman(built.config).execute("Hund").unwrap().shown[0]
    plan = PlanWordCards(built.config).execute(shown, 0, [0], []).unwrap()
    CreateWordCards(built.config).execute(plan, T0).unwrap()
    first = NextCard(built.config).execute(T0).unwrap().unwrap()

    Grade(built.config).execute(first.id, 3, T0, "s1").unwrap()

    # a fresh connection, as after a killed process, already sees the grade
    with sqlite3.connect(built.config.learning_db) as db:
        assert db.execute("SELECT card_id, rating FROM review").fetchall() == [(first.id, 3)]


def test_checked_english_german_card_is_graded_by_its_answer(built: Workspace) -> None:
    shown = LookUpGerman(built.config).execute("Hund").unwrap().shown[0]
    plan = PlanWordCards(built.config).execute(shown, 0, [0], []).unwrap()
    CreateWordCards(built.config).execute(plan, T0).unwrap()

    now = T0
    ratings = {}
    # Hard and Good leave a card in learning, so it comes straight back: take each card once
    while (card := NextCard(built.config).execute(now).unwrap()).is_some:
        c = card.unwrap()
        if c.card_type in ratings:
            break
        if c.card_type == "meaning_en_de":
            checked = AnswerMeaning(built.config, enable_fuzzing=False).execute(
                c.id, "die Hund", None, now, "s1"
            )
            graded = checked.unwrap()
            assert isinstance(graded, MeaningGraded)
            ratings[c.card_type] = int(graded.rating)
        else:
            Grade(built.config, enable_fuzzing=False).execute(c.id, 3, now, "s1").unwrap()
            ratings[c.card_type] = 3
        now += timedelta(seconds=20)

    assert ratings == {"meaning_en_de": 2, "meaning_de_en": 3}
    summary = SessionSummary(built.config).execute("s1").unwrap()
    assert (summary.reviewed, summary.correct) == (2, 2)


def test_another_noun_gets_one_retry_and_a_right_second_try_is_hard(built: Workspace) -> None:
    shown = LookUpGerman(built.config).execute("Hund").unwrap().shown[0]
    plan = PlanWordCards(built.config).execute(shown, 0, [0], []).unwrap()
    CreateWordCards(built.config).execute(plan, T0).unwrap()
    cards = {}
    while (card := NextCard(built.config).execute(T0).unwrap()).is_some:
        c = card.unwrap()
        if c.card_type in cards:
            break
        cards[c.card_type] = c
        Grade(built.config, enable_fuzzing=False).execute(c.id, 3, T0, "s0").unwrap()
    card_id = cards["meaning_en_de"].id
    answer = AnswerMeaning(built.config, enable_fuzzing=False)

    first = answer.execute(card_id, "die Katze", None, T0, "s1").unwrap()
    assert first == TryAgain("noun", "H", 4)
    with sqlite3.connect(built.config.learning_db) as db:
        assert db.execute("SELECT COUNT(*) FROM review WHERE session_id = 's1'").fetchone() == (0,)

    second = answer.execute(card_id, "der Hund", "die Katze", T0, "s1").unwrap()
    assert isinstance(second, MeaningGraded)
    assert (int(second.rating), second.second_try) == (2, True)
    with sqlite3.connect(built.config.learning_db) as db:
        assert db.execute(
            "SELECT rating, answer FROM review WHERE session_id = 's1'"
        ).fetchall() == [(2, "die Katze | der Hund")]


def test_checked_german_german_card_takes_the_gender_of_its_own_entry(built: Workspace) -> None:
    shown = LookUpGerman(built.config).execute("Band").unwrap().shown[0]
    plan = PlanWordCards(built.config).execute(shown, 0, [0], [(2, 0)]).unwrap()
    CreateWordCards(built.config).execute(plan, T0).unwrap()
    card_id = None
    while (card := NextCard(built.config).execute(T0).unwrap()).is_some:
        c = card.unwrap()
        if c.card_type == "meaning_de_de":
            card_id = c.id
            break
        Grade(built.config, enable_fuzzing=False).execute(c.id, 3, T0, "s0").unwrap()
    assert card_id is not None

    checked = (
        AnswerMeaning(built.config, enable_fuzzing=False)
        .execute(card_id, "der Band", None, T0, "s1")
        .unwrap()
    )

    assert isinstance(checked, MeaningGraded)
    assert (int(checked.rating), checked.expected) == (3, "der Band")
    with sqlite3.connect(built.config.learning_db) as db:
        assert db.execute(
            "SELECT rating, answer FROM review WHERE session_id = 's1'"
        ).fetchall() == [(3, "der Band")]
