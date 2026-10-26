import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fsrs import Card as FsrsCard
from fsrs import Rating, Scheduler
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from harald.core.option import Option
from harald.core.result import Result
from harald.infrastructure.crud import crud_create, crud_update
from harald.infrastructure.infra_errors import InfrastructureError
from harald.infrastructure.transaction_context import DbTransactionContext
from harald.learning.answers import ArticleCheck, check_article
from harald.learning.errors import CardNotFound, LearningDbError, StorageError
from harald.learning.models import Card, Review
from harald.learning.scheduling import (
    CARD_SCOPE,
    apply_fsrs,
    card_to_fsrs,
    to_naive,
)

LEARN_AHEAD = timedelta(minutes=20)
_LEARNING_STATES = (1, 3)  # fsrs State.Learning, State.Relearning


@dataclass(frozen=True)
class SummaryCounts:
    reviewed: int
    correct: int


def _storage(err: InfrastructureError) -> LearningDbError:
    return StorageError(str(err))


def next_card(ctx: DbTransactionContext, now: datetime) -> Result[Option[Card], LearningDbError]:
    moment = to_naive(now)
    reviewed = Card.last_review.is_not(None)
    queries = (
        select(Card).where(reviewed, Card.due <= moment).order_by(Card.due, Card.id),
        select(Card).where(Card.last_review.is_(None)).order_by(Card.created_at, Card.id),
        select(Card)
        .where(reviewed, Card.fsrs_state.in_(_LEARNING_STATES), Card.due <= moment + LEARN_AHEAD)
        .order_by(Card.due, Card.id),
    )

    def first(session: Session) -> Option[Card]:
        for query in queries:
            card = session.scalar(query.where(Card.suspended == 0).limit(1))
            if card is not None:
                return Option.some(card)
        return Option.none()

    return ctx.run(first).map_err(_storage)


@crud_create
def _add_review(ctx: DbTransactionContext, review: Review) -> Result[Review, LearningDbError]:
    return ctx.run(lambda s: s.add(review)).map(lambda _: review).map_err(_storage)


@crud_update
def _reschedule(
    ctx: DbTransactionContext, card: Card, scheduled: FsrsCard
) -> Result[Card, LearningDbError]:
    return ctx.run(lambda s: apply_fsrs(card, scheduled)).map(lambda _: card).map_err(_storage)


def grade_card(
    ctx: DbTransactionContext,
    card_id: int,
    rating: int,
    now: datetime,
    session_id: str,
    duration_ms: int | None,
    answer: str | None,
    scheduler_for: Callable[[str], Scheduler],
) -> Result[None, LearningDbError]:
    found = ctx.run(lambda s: s.get(Card, card_id)).map_err(_storage)
    if found.is_err:
        return Result.err(found.unwrap_err())
    card = found.unwrap()
    if card is None:
        return Result.err(CardNotFound(card_id))

    scope = CARD_SCOPE[card.card_type]
    before = card_to_fsrs(card)
    scheduled, _log = scheduler_for(scope).review_card(
        before, Rating(rating), review_datetime=now.astimezone(UTC), review_duration=duration_ms
    )
    review = Review(
        card_id=card.id,
        session_id=session_id,
        reviewed_at=to_naive(now),
        rating=rating,
        scope=scope,
        duration_ms=duration_ms,
        answer=answer,
        state_before=json.dumps(before.to_dict()),
        state_after=json.dumps(scheduled.to_dict()),
    )
    added = _add_review(ctx, review)
    if added.is_err:
        return Result.err(added.unwrap_err())
    updated = _reschedule(ctx, card, scheduled)
    if updated.is_err:
        return Result.err(updated.unwrap_err())
    return Result.ok(None)


def answer_article(
    ctx: DbTransactionContext,
    card_id: int,
    chosen: str,
    now: datetime,
    session_id: str,
    duration_ms: int | None,
    scheduler_for: Callable[[str], Scheduler],
) -> Result[ArticleCheck, LearningDbError]:
    found = ctx.run(lambda s: s.get(Card, card_id)).map_err(_storage)
    if found.is_err:
        return Result.err(found.unwrap_err())
    card = found.unwrap()
    if card is None:
        return Result.err(CardNotFound(card_id))
    checked = check_article(card.content["gender"], chosen)
    rating = Rating.Good if checked.correct else Rating.Again
    graded = grade_card(
        ctx, card_id, int(rating), now, session_id, duration_ms, chosen, scheduler_for
    )
    if graded.is_err:
        return Result.err(graded.unwrap_err())
    return Result.ok(checked)


def session_summary(
    ctx: DbTransactionContext, session_id: str
) -> Result[SummaryCounts, LearningDbError]:
    def count(session: Session) -> SummaryCounts:
        first = (
            select(func.min(Review.id).label("id"))
            .where(Review.session_id == session_id)
            .group_by(Review.card_id)
            .subquery()
        )
        ratings = session.scalars(select(Review.rating).join(first, Review.id == first.c.id)).all()
        return SummaryCounts(len(ratings), sum(1 for r in ratings if r != 1))

    return ctx.run(count).map_err(_storage)
