from pathlib import Path

from alembic import context
from alembic.util import CommandError

from harald.learning.migrate import migration_engine
from harald.learning.models import Base

config = context.config

if context.is_offline_mode():
    raise CommandError("offline migrations are not supported; run against a database file")


def _run(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        transactional_ddl=True,
        transaction_per_migration=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


connection = config.attributes.get("connection")
if connection is not None:
    _run(connection)
else:
    # the developer command line: `alembic -x db=PATH ...`; there is no default database
    db = context.get_x_argument(as_dictionary=True).get("db")
    if db is None:
        raise CommandError("pass the database file with -x db=PATH")
    engine = migration_engine(Path(db))
    try:
        with engine.connect() as connection:
            _run(connection)
    finally:
        engine.dispose()
