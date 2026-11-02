from datetime import datetime

from harald.config import Config
from harald.core.option import Option
from harald.core.result import Result
from harald.learning.answers import FieldCheck as FieldCheck
from harald.learning.answers import MeaningCheck as MeaningCheck
from harald.learning.answers import MeaningGraded as MeaningGraded
from harald.learning.answers import NoArticleStored as NoArticleStored
from harald.learning.answers import StammformenCheck as StammformenCheck
from harald.learning.answers import TryAgain as TryAgain
from harald.learning.db import transact
from harald.learning.errors import LearningDbError
from harald.learning.models import Card
from harald.learning.scheduling import scheduler_for
from harald.learning.study import (
    SummaryCounts,
    answer_conjugation,
    answer_meaning,
    answer_stammformen,
    grade_card,
    next_card,
    session_summary,
)
from harald.lexicon.db import open_lexicon
from harald.lexicon.errors import LexiconError
from harald.lexicon.lookup import known_words


class NextCard:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(self, now: datetime) -> Result[Option[Card], LearningDbError]:
        return transact(self._config.learning_db, lambda ctx: next_card(ctx, now))


class Grade:
    def __init__(self, config: Config, enable_fuzzing: bool = True) -> None:
        self._config = config
        self._enable_fuzzing = enable_fuzzing

    def execute(
        self,
        card_id: int,
        rating: int,
        now: datetime,
        session_id: str,
        duration_ms: int | None = None,
        answer: str | None = None,
    ) -> Result[None, LearningDbError]:
        return transact(
            self._config.learning_db,
            lambda ctx: grade_card(
                ctx,
                card_id,
                rating,
                now,
                session_id,
                duration_ms,
                answer,
                lambda scope: scheduler_for(scope, self._enable_fuzzing),
            ),
        )


class AnswerStammformen:
    def __init__(self, config: Config, enable_fuzzing: bool = True) -> None:
        self._config = config
        self._enable_fuzzing = enable_fuzzing

    def execute(
        self,
        card_id: int,
        given: tuple[str, str, str],
        now: datetime,
        session_id: str,
        duration_ms: int | None = None,
    ) -> Result[StammformenCheck, LearningDbError]:
        return transact(
            self._config.learning_db,
            lambda ctx: answer_stammformen(
                ctx,
                card_id,
                given,
                now,
                session_id,
                duration_ms,
                lambda scope: scheduler_for(scope, self._enable_fuzzing),
            ),
        )


class AnswerConjugation:
    def __init__(self, config: Config, enable_fuzzing: bool = True) -> None:
        self._config = config
        self._enable_fuzzing = enable_fuzzing

    def execute(
        self,
        card_id: int,
        given: str,
        now: datetime,
        session_id: str,
        duration_ms: int | None = None,
    ) -> Result[FieldCheck, LearningDbError]:
        return transact(
            self._config.learning_db,
            lambda ctx: answer_conjugation(
                ctx,
                card_id,
                given,
                now,
                session_id,
                duration_ms,
                lambda scope: scheduler_for(scope, self._enable_fuzzing),
            ),
        )


class AnswerMeaning:
    def __init__(self, config: Config, enable_fuzzing: bool = True) -> None:
        self._config = config
        self._enable_fuzzing = enable_fuzzing

    def execute(
        self,
        card_id: int,
        given: str,
        first_try: str | None,
        now: datetime,
        session_id: str,
        duration_ms: int | None = None,
    ) -> Result[MeaningCheck, LearningDbError | LexiconError]:
        opened = open_lexicon(self._config.lexicon)
        if opened.is_err:
            return Result.err(opened.unwrap_err())
        lex = opened.unwrap()
        try:
            return transact(
                self._config.learning_db,
                lambda ctx: answer_meaning(
                    ctx,
                    card_id,
                    given,
                    first_try,
                    now,
                    session_id,
                    duration_ms,
                    lambda scope: scheduler_for(scope, self._enable_fuzzing),
                    lambda word: known_words(lex, word),
                ),
            ).map_err(lambda e: e)
        finally:
            lex.engine.dispose()


class SessionSummary:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(self, session_id: str) -> Result[SummaryCounts, LearningDbError]:
        return transact(self._config.learning_db, lambda ctx: session_summary(ctx, session_id))
