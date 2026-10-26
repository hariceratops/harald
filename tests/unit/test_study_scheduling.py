import sqlite3
from datetime import UTC, datetime, timedelta

from fsrs import Scheduler

from harald.learning.content import CardPlan
from harald.learning.scheduling import CARD_SCOPE, scheduler_for
from harald.lexicon.model import Headword
from harald.use_cases.cards import CreateWordCards, PlanWordCards
from harald.use_cases.lexicon import LoadHeadword
from harald.use_cases.study import Grade, NextCard, SessionSummary
from tests.conftest import Workspace

T0 = datetime(2026, 10, 26, 9, 0, tzinfo=UTC)
AGAIN, GOOD = 1, 3


def _add(ws: Workspace, sense: int = 0) -> list[int]:
    hund: Headword = LoadHeadword(ws.config).execute("Hund", "noun").unwrap().unwrap()
    planned = PlanWordCards(ws.config).execute(hund, 0, [sense], []).unwrap()
    plan = CardPlan(planned.word_hint, tuple(c for c in planned.cards if c.card_type != "article"))
    return CreateWordCards(ws.config).execute(plan, T0).unwrap()


def _next(ws: Workspace, now: datetime) -> int | None:
    return NextCard(ws.config).execute(now).unwrap().map(lambda c: c.id).to_optional()


def test_every_card_type_has_a_scope_and_meaning_cards_share_one() -> None:
    assert CARD_SCOPE["meaning_de_en"] == CARD_SCOPE["meaning_en_de"] == CARD_SCOPE["meaning_de_de"]
    assert CARD_SCOPE["article"] != CARD_SCOPE["meaning_de_en"]


def test_schedulers_are_cached_per_scope_with_default_parameters() -> None:
    assert scheduler_for("meaning") is scheduler_for("meaning")
    assert scheduler_for("meaning") is not scheduler_for("article")
    assert scheduler_for("meaning").parameters == Scheduler().parameters


def test_new_cards_come_oldest_first_and_study_ends_when_none_are_left(built: Workspace) -> None:
    first, second = _add(built)

    assert _next(built, T0) == first
    # Easy graduates a new card straight to Review, days out
    Grade(built.config, enable_fuzzing=False).execute(first, 4, T0, "s1").unwrap()
    Grade(built.config, enable_fuzzing=False).execute(second, 4, T0, "s1").unwrap()

    assert _next(built, T0) is None


def test_due_cards_come_before_new_ones(built: Workspace) -> None:
    first, second = _add(built)
    Grade(built.config, enable_fuzzing=False).execute(second, GOOD, T0, "s1").unwrap()
    # Good on a new card enters the 10-minute step
    later = T0 + timedelta(minutes=11)

    assert _next(built, later) == second
    assert _next(built, T0 + timedelta(minutes=1)) == first


def test_again_card_returns_through_learn_ahead(built: Workspace) -> None:
    (first, second) = _add(built)
    grade = Grade(built.config, enable_fuzzing=False)
    grade.execute(first, GOOD, T0, "s1").unwrap()
    grade.execute(second, GOOD, T0, "s1").unwrap()
    t = T0 + timedelta(minutes=11)
    grade.execute(first, AGAIN, t, "s1").unwrap()

    assert _next(built, t) == second  # due a minute ago
    grade.execute(second, 4, t, "s1").unwrap()
    # the failed card is due in 10 minutes: not yet due, but inside the learn-ahead window
    assert _next(built, t) == first


def test_learn_ahead_does_not_reach_past_twenty_minutes(built: Workspace) -> None:
    (first,) = _add(built)[:1]
    with sqlite3.connect(built.config.learning_db) as db:
        db.execute("DELETE FROM card WHERE id != ?", (first,))
    Grade(built.config, enable_fuzzing=False).execute(first, GOOD, T0, "s1").unwrap()

    # Good on a new card is due in 10 minutes
    assert _next(built, T0 - timedelta(minutes=5)) == first
    assert _next(built, T0 - timedelta(minutes=15)) is None


def test_grade_updates_the_card_and_appends_a_review_row(built: Workspace) -> None:
    (first, _) = _add(built)

    Grade(built.config, enable_fuzzing=False).execute(
        first, GOOD, T0, "s1", duration_ms=1500
    ).unwrap()

    with sqlite3.connect(built.config.learning_db) as db:
        review = db.execute(
            "SELECT card_id, session_id, rating, scope, duration_ms, reviewed_at, "
            "state_before, state_after FROM review"
        ).fetchall()
        card = (
            db.execute("SELECT last_review, fsrs_state FROM card WHERE id = ?", (first,)).one
            if False
            else db.execute(
                "SELECT last_review, fsrs_state FROM card WHERE id = ?", (first,)
            ).fetchone()
        )
    assert len(review) == 1
    assert review[0][:5] == (first, "s1", 3, "meaning", 1500)
    assert review[0][5].startswith("2026-10-26 09:00:00")
    assert '"last_review": null' in review[0][6]
    assert '"last_review": "2026-10-26T09:00:00' in review[0][7]
    assert card[0].startswith("2026-10-26 09:00:00")


def test_grade_is_one_audit_group_with_a_review_and_a_card_update(built: Workspace) -> None:
    (first, _) = _add(built)
    Grade(built.config, enable_fuzzing=False).execute(first, GOOD, T0, "s1").unwrap()

    with sqlite3.connect(built.config.learning_db) as db:
        groups = db.execute("SELECT COUNT(*) FROM operation_groups").fetchone()[0]
        ops = db.execute(
            "SELECT entity_type, action, field, state FROM operations "
            "WHERE group_id = (SELECT MAX(id) FROM operation_groups) ORDER BY id"
        ).fetchall()
    assert groups == 2  # the add, then the grade
    assert [(t, a) for t, a, _, _ in ops] == [("review", "create"), ("card", "update")]
    assert ops[0][2:] == (None, None)
    assert ops[1][2] is not None and "due" in ops[1][2] and "last_review" in ops[1][2]
    assert ops[1][3] is not None and '"last_review": null' in ops[1][3]


def test_grade_of_a_missing_card_is_an_error_and_writes_nothing(built: Workspace) -> None:
    _add(built)

    result = Grade(built.config).execute(999, GOOD, T0, "s1")

    assert result.is_err
    with sqlite3.connect(built.config.learning_db) as db:
        assert db.execute("SELECT COUNT(*) FROM review").fetchone() == (0,)


def test_invalid_rating_rolls_back(built: Workspace) -> None:
    (first, _) = _add(built)

    result = Grade(built.config).execute(first, 7, T0, "s1")

    assert result.is_err
    with sqlite3.connect(built.config.learning_db) as db:
        assert db.execute("SELECT COUNT(*) FROM review").fetchone() == (0,)
        assert db.execute("SELECT last_review FROM card WHERE id = ?", (first,)).fetchone() == (
            None,
        )


def test_session_summary_counts_cards_and_first_grades(built: Workspace) -> None:
    first, second = _add(built)
    grade = Grade(built.config, enable_fuzzing=False)
    grade.execute(first, AGAIN, T0, "s1").unwrap()
    grade.execute(second, GOOD, T0, "s1").unwrap()
    # the repeat of a failed card does not count as answered correctly
    grade.execute(first, GOOD, T0 + timedelta(minutes=2), "s1").unwrap()
    grade.execute(first, GOOD, T0, "other").unwrap()

    summary = SessionSummary(built.config).execute("s1").unwrap()

    assert (summary.reviewed, summary.correct) == (2, 1)
    assert SessionSummary(built.config).execute("none").unwrap().reviewed == 0
