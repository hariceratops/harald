from collections.abc import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from harald.core.result import Result
from harald.infrastructure.infra_errors import InfrastructureError, UniqueViolation
from harald.learning.models import Operation, OperationGroup


class DbTransactionContext:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.transaction_group: OperationGroup | None = None
        self.transaction_steps: list[Operation] = []

    def record_transaction_step(self, op: Operation) -> None:
        # created on the first write, so a use case that only reads leaves no group behind
        if self.transaction_group is None:
            self.transaction_group = OperationGroup()
            self.session.add(self.transaction_group)
            self.session.flush()
        op.group_id = self.transaction_group.id
        self.transaction_steps.append(op)

    def run[T](self, op: Callable[[Session], T]) -> Result[T, InfrastructureError]:
        try:
            value = op(self.session)
            self.session.flush()
            return Result.ok(value)
        except IntegrityError as e:
            constraint = str(e.orig.args[0]) if e.orig and e.orig.args else str(e)
            return Result.err(UniqueViolation(constraint))
        except Exception as e:  # noqa: BLE001
            return Result.err(InfrastructureError(str(e)))
