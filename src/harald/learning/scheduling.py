from datetime import UTC, datetime
from functools import cache

from fsrs import Card as FsrsCard
from fsrs import Scheduler, State

from harald.learning.models import Card

# One scope per kind of recall, so a parameter set fitted later for one cannot skew another.
# Moving meaning_de_de to its own scope is the one-line change the spec promises.
CARD_SCOPE = {
    "meaning_de_en": "meaning",
    "meaning_en_de": "meaning",
    "meaning_de_de": "meaning",
    "article": "article",
    "stammformen": "conjugation",
    "conjugation": "conjugation",
    "phrase_en_de": "phrase",
}


@cache
def scheduler_for(scope: str, enable_fuzzing: bool = True) -> Scheduler:
    # fsrs_params is empty in v1, so every scope runs on the package defaults
    return Scheduler(enable_fuzzing=enable_fuzzing)


def to_aware(moment: datetime) -> datetime:
    return moment.replace(tzinfo=UTC)


def to_naive(moment: datetime) -> datetime:
    return moment.astimezone(UTC).replace(tzinfo=None)


def new_fsrs_state(now: datetime) -> FsrsCard:
    return FsrsCard(due=now)


def card_to_fsrs(card: Card) -> FsrsCard:
    return FsrsCard(
        card_id=card.id,
        state=State(card.fsrs_state),
        step=card.fsrs_step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=to_aware(card.due),
        last_review=to_aware(card.last_review) if card.last_review else None,
    )


def apply_fsrs(card: Card, scheduled: FsrsCard) -> None:
    card.fsrs_state = scheduled.state.value
    card.fsrs_step = scheduled.step
    card.stability = scheduled.stability
    card.difficulty = scheduled.difficulty
    card.due = to_naive(scheduled.due)
    card.last_review = to_naive(scheduled.last_review) if scheduled.last_review else None
