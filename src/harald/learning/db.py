from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, event, inspect
from sqlalchemy.orm import ORMExecuteState, Session, sessionmaker, with_loader_criteria

from harald.core.result import Result
from harald.db.connection import make_engine, make_session_factory
from harald.infrastructure.transaction_context import DbTransactionContext
from harald.infrastructure.uow import DbTransaction
from harald.learning import migrate
from harald.learning.errors import LearningDbError, as_learning_error
from harald.learning.models import Card

LEARNING_DB_PRAGMAS = {
    "foreign_keys": "ON",
    "journal_mode": "WAL",
    "synchronous": "FULL",
    "busy_timeout": "5000",
}


@dataclass(frozen=True)
class LearningDb:
    engine: Engine
    sessions: sessionmaker[Session]

    def session(self) -> Session:
        return self.sessions()

    def close(self) -> None:
        self.engine.dispose()


def _hide_deleted_cards(state: ORMExecuteState) -> None:
    if state.is_select and not state.execution_options.get("include_deleted", False):
        state.statement = state.statement.options(
            with_loader_criteria(Card, Card.deleted_at.is_(None), include_aliases=True)
        )


def _json_safe(value: Any) -> Any:
    return value.isoformat() if isinstance(value, datetime) else value


def _remember_old_values(session: Session, _ctx: Any, _instances: Any) -> None:
    # Has to run at flush time: DbTransactionContext.run flushes, which resets the history
    # that crud_update reads afterwards.
    audit: dict[tuple[str, int], dict[str, Any]] = session.info.setdefault("audit_before", {})
    for obj in session.dirty:
        state = inspect(obj)
        old: dict[str, Any] = {}
        for attr in state.mapper.column_attrs:
            history = state.attrs[attr.key].history
            if history.has_changes():
                old[attr.key] = _json_safe(history.deleted[0]) if history.deleted else None
        if old:
            audit[(state.mapper.local_table.name, state.identity[0])] = old
    for obj in session.deleted:
        state = inspect(obj)
        audit[(state.mapper.local_table.name, state.identity[0])] = {
            attr.key: _json_safe(getattr(obj, attr.key)) for attr in state.mapper.column_attrs
        }


def open_learning_db(path: Path) -> Result[LearningDb, LearningDbError]:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(path, pragmas=LEARNING_DB_PRAGMAS)
    sessions = make_session_factory(engine)
    event.listen(sessions, "do_orm_execute", _hide_deleted_cards)
    event.listen(sessions, "before_flush", _remember_old_values)
    # Alembic is imported only when the file is not already at HEAD
    found = migrate.stored_revision(engine)
    if found != migrate.HEAD:
        upgraded = migrate.upgrade(engine, path, found)
        if upgraded.is_err:
            engine.dispose()
            return Result.err(upgraded.unwrap_err())
    return Result.ok(LearningDb(engine, sessions))


def transact[T](
    path: Path, fn: Callable[[DbTransactionContext], Result[T, LearningDbError]]
) -> Result[T, LearningDbError]:
    opened = open_learning_db(path)
    if opened.is_err:
        return Result.err(opened.unwrap_err())
    db = opened.unwrap()
    try:
        return (
            DbTransaction[T, LearningDbError](db.session()).execute(fn).map_err(as_learning_error)
        )
    finally:
        db.close()
