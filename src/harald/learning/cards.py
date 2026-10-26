import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from harald.core.result import Result
from harald.infrastructure.crud import crud_create
from harald.infrastructure.infra_errors import InfrastructureError
from harald.infrastructure.transaction_context import DbTransactionContext
from harald.learning.content import CardPlan, NewCard, WordHint
from harald.learning.errors import LearningDbError, StorageError
from harald.learning.models import Card, Word
from harald.learning.scheduling import new_fsrs_state, to_naive


def _storage(err: InfrastructureError) -> LearningDbError:
    return StorageError(str(err))


def _canonical(content: object) -> str:
    return json.dumps(content, sort_keys=True, ensure_ascii=False)


def _identity(card: NewCard) -> tuple[str, str]:
    return (card.card_type, "" if card.card_type == "article" else _canonical(card.content))


def drop_live_duplicates(
    ctx: DbTransactionContext, hint: WordHint, cards: tuple[NewCard, ...]
) -> Result[tuple[NewCard, ...], LearningDbError]:
    def live(session: Session) -> set[tuple[str, str]]:
        rows = session.execute(
            select(Card.card_type, Card.content)
            .join(Word, Card.word_id == Word.id)
            .where(
                Word.lemma == hint.lemma,
                Word.pos == hint.pos,
                Word.discriminator == hint.discriminator,
            )
        ).all()
        # the hint follows whichever sense was picked first, so an article card is "the same"
        # whatever its content: one per word
        return {(t, "" if t == "article" else _canonical(c)) for t, c in rows}

    found = ctx.run(live).map_err(_storage)
    if found.is_err:
        return Result.err(found.unwrap_err())
    existing = found.unwrap()
    return Result.ok(tuple(c for c in cards if _identity(c) not in existing))


def _find_word(ctx: DbTransactionContext, hint: WordHint) -> Result[Word | None, LearningDbError]:
    return ctx.run(
        lambda s: s.scalar(
            select(Word).where(
                Word.lemma == hint.lemma,
                Word.pos == hint.pos,
                Word.discriminator == hint.discriminator,
            )
        )
    ).map_err(_storage)


@crud_create
def _add_word(
    ctx: DbTransactionContext, hint: WordHint, now: datetime
) -> Result[Word, LearningDbError]:
    word = Word(
        lemma=hint.lemma, pos=hint.pos, discriminator=hint.discriminator, created_at=to_naive(now)
    )
    return ctx.run(lambda s: s.add(word)).map(lambda _: word).map_err(_storage)


@crud_create
def _add_card(
    ctx: DbTransactionContext, word_id: int, card: NewCard, now: datetime
) -> Result[Card, LearningDbError]:
    fresh = new_fsrs_state(now)
    row = Card(
        word_id=word_id,
        card_type=card.card_type,
        content=card.content,
        created_at=to_naive(now),
        fsrs_state=fresh.state.value,
        fsrs_step=fresh.step,
        stability=fresh.stability,
        difficulty=fresh.difficulty,
        due=to_naive(fresh.due),
        last_review=None,
    )
    return ctx.run(lambda s: s.add(row)).map(lambda _: row).map_err(_storage)


def create_word_cards(
    ctx: DbTransactionContext, plan: CardPlan, now: datetime
) -> Result[list[int], LearningDbError]:
    found = _find_word(ctx, plan.word_hint)
    if found.is_err:
        return Result.err(found.unwrap_err())
    word = found.unwrap()
    if word is None:
        added = _add_word(ctx, plan.word_hint, now)
        if added.is_err:
            return Result.err(added.unwrap_err())
        word = added.unwrap()
    ids: list[int] = []
    for card in plan.cards:
        made = _add_card(ctx, word.id, card, now)
        if made.is_err:
            return Result.err(made.unwrap_err())
        ids.append(made.unwrap().id)
    return Result.ok(ids)
