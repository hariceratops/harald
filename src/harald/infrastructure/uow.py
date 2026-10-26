from collections.abc import Callable

from sqlalchemy.orm import Session

from harald.core.result import Result
from harald.infrastructure.transaction_context import DbTransactionContext


class DbTransaction[T, E: Exception]:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.ctx = DbTransactionContext(session)

    # failure seam: an unanticipated exception must not leave a half-written transaction
    def execute(
        self, use_case: Callable[[DbTransactionContext], Result[T, E]]
    ) -> Result[T, Exception]:
        try:
            result = use_case(self.ctx)
            if result.is_err:
                self.session.rollback()
                return Result.err(result.unwrap_err())
            self.session.add_all(self.ctx.transaction_steps)
            self.session.commit()
            return Result.ok(result.unwrap())
        except Exception as e:  # noqa: BLE001
            self.session.rollback()
            return Result.err(e)
        finally:
            self.session.close()
