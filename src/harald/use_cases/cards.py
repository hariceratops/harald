from collections.abc import Sequence
from datetime import datetime

from harald.config import Config
from harald.core.result import Result
from harald.learning.cards import create_word_cards, drop_live_duplicates
from harald.learning.content import CardPlan, plan_word_cards
from harald.learning.db import transact
from harald.learning.errors import LearningDbError
from harald.lexicon.model import Headword


class PlanWordCards:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(
        self,
        headword: Headword,
        entry_index: int | None,
        en_senses: Sequence[int],
        de_senses: Sequence[tuple[int, int]],
    ) -> Result[CardPlan, LearningDbError]:
        plan = plan_word_cards(headword, entry_index, en_senses, de_senses)

        def dedupe(ctx):  # type: ignore[no-untyped-def]
            return drop_live_duplicates(ctx, plan.word_hint, plan.cards).map(
                lambda cards: CardPlan(plan.word_hint, cards, plan.refusals)
            )

        return transact(self._config.learning_db, dedupe)


class CreateWordCards:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(self, plan: CardPlan, now: datetime) -> Result[list[int], LearningDbError]:
        return transact(self._config.learning_db, lambda ctx: create_word_cards(ctx, plan, now))
