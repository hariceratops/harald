import json
from collections.abc import Callable
from datetime import datetime
from typing import Any, Concatenate, Protocol

from harald.core.result import Result
from harald.infrastructure.transaction_context import DbTransactionContext
from harald.learning.models import Operation


class _Entity(Protocol):
    __tablename__: str
    id: Any


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"cannot serialise {type(value).__name__}")


def _record[**P, E: _Entity, X: Exception](
    action: str, fn: Callable[Concatenate[DbTransactionContext, P], Result[E, X]]
) -> Callable[Concatenate[DbTransactionContext, P], Result[E, X]]:
    def wrapper(ctx: DbTransactionContext, /, *args: P.args, **kwargs: P.kwargs) -> Result[E, X]:
        result = fn(ctx, *args, **kwargs)
        if result.is_err:
            return result
        entity = result.unwrap()
        # captured by the before_flush listener (learning.db.audit_before_flush) while the
        # attribute history still existed; only updates and deletes have any
        before = ctx.session.info.get("audit_before", {}).pop(
            (entity.__tablename__, entity.id), None
        )
        ctx.record_transaction_step(
            Operation(
                entity_type=entity.__tablename__,
                entity_id=entity.id,
                action=action,
                field=",".join(sorted(before)) if before else None,
                state=json.dumps(before, default=_json_default) if before else None,
            )
        )
        return result

    return wrapper


def crud_create[**P, E: _Entity, X: Exception](
    fn: Callable[Concatenate[DbTransactionContext, P], Result[E, X]],
) -> Callable[Concatenate[DbTransactionContext, P], Result[E, X]]:
    return _record("create", fn)


def crud_update[**P, E: _Entity, X: Exception](
    fn: Callable[Concatenate[DbTransactionContext, P], Result[E, X]],
) -> Callable[Concatenate[DbTransactionContext, P], Result[E, X]]:
    return _record("update", fn)
