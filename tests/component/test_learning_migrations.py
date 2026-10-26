import shutil
import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

from harald.learning import migrate
from harald.learning.db import open_learning_db
from harald.learning.errors import LearningDbTooNew, MigrationFailed, NotALearningDb

EXPECTED_TABLES = {
    "alembic_version",
    "card",
    "deck",
    "deck_member",
    "fsrs_params",
    "operation_groups",
    "operations",
    "phrase",
    "review",
    "word",
}
EXPECTED_INDEXES = {
    "card_due",
    "card_word",
    "card_phrase",
    "review_card",
    "review_time",
    "review_session",
    "deck_member_word",
    "deck_member_phrase",
}


def _names(path: Path, kind: str) -> set[str]:
    with sqlite3.connect(path) as db:
        rows = db.execute(
            "SELECT name FROM sqlite_master WHERE type = ? AND name NOT LIKE 'sqlite_%'", (kind,)
        ).fetchall()
    return {r[0] for r in rows}


def _revision(path: Path) -> str | None:
    with sqlite3.connect(path) as db:
        row = db.execute("SELECT version_num FROM alembic_version").fetchone()
    return row[0] if row else None


def _alembic_config(path: Path) -> Iterator[AlembicConfig]:
    engine = migrate.migration_engine(path)
    try:
        with engine.connect() as conn:
            config = AlembicConfig()
            config.set_main_option("script_location", str(migrate.SCRIPT_LOCATION))
            config.attributes["connection"] = conn
            yield config
    finally:
        engine.dispose()


@pytest.fixture
def versions_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[str], Path]:
    """A copy of the script directory, which a test extends with its own revision 0002."""

    def make(body: str) -> Path:
        scripts = tmp_path / "scripts"
        shutil.copytree(
            migrate.SCRIPT_LOCATION, scripts, ignore=shutil.ignore_patterns("__pycache__")
        )
        (scripts / "versions" / "0002_extra.py").write_text(
            "from alembic import op\n"
            "import sqlalchemy as sa\n"
            "revision = '0002'\n"
            "down_revision = '0001'\n"
            "branch_labels = None\n"
            "depends_on = None\n"
            f"def upgrade():\n{body}\n"
            "def downgrade():\n    pass\n"
        )
        monkeypatch.setattr(migrate, "SCRIPT_LOCATION", scripts)
        monkeypatch.setattr(migrate, "HEAD", "0002")
        return scripts

    return make


def test_head_constant_matches_the_script_directory() -> None:
    config = AlembicConfig()
    config.set_main_option("script_location", str(migrate.SCRIPT_LOCATION))
    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == [migrate.HEAD]


def test_fresh_path_is_created_complete_without_a_backup(tmp_path: Path) -> None:
    path = tmp_path / "learning.db"

    opened = open_learning_db(path)

    assert opened.is_ok
    opened.unwrap().close()
    assert _names(path, "table") == EXPECTED_TABLES
    assert EXPECTED_INDEXES <= _names(path, "index")
    assert _revision(path) == migrate.HEAD
    assert not list(tmp_path.glob("*.bak"))


def test_runtime_connection_has_the_designed_pragmas(tmp_path: Path) -> None:
    db = open_learning_db(tmp_path / "learning.db").unwrap()

    with db.engine.connect() as conn:
        pragmas = {
            name: conn.exec_driver_sql(f"PRAGMA {name}").scalar()
            for name in ("foreign_keys", "journal_mode", "synchronous", "busy_timeout")
        }
    db.close()

    assert pragmas == {
        "foreign_keys": 1,
        "journal_mode": "wal",
        "synchronous": 2,
        "busy_timeout": 5000,
    }


def test_models_and_revisions_agree(tmp_path: Path) -> None:
    path = tmp_path / "learning.db"
    open_learning_db(path).unwrap().close()

    # raises CommandError when autogenerate would emit anything
    for config in _alembic_config(path):
        command.check(config)


def test_downgrade_to_base_and_upgrade_again(tmp_path: Path) -> None:
    path = tmp_path / "learning.db"
    open_learning_db(path).unwrap().close()

    for config in _alembic_config(path):
        command.downgrade(config, "base")
    assert _names(path, "table") == {"alembic_version"}
    for config in _alembic_config(path):
        command.upgrade(config, "head")

    assert _names(path, "table") == EXPECTED_TABLES


def test_older_revision_is_backed_up_then_upgraded(
    tmp_path: Path, versions_dir: Callable[[str], Path]
) -> None:
    path = tmp_path / "learning.db"
    open_learning_db(path).unwrap().close()
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO deck (name, created_at) VALUES ('kept', '2026-01-01 00:00:00')")
    versions_dir("    op.add_column('deck', sa.Column('extra', sa.Text()))")

    opened = open_learning_db(path)

    assert opened.is_ok
    opened.unwrap().close()
    backup = tmp_path / "learning.db.pre-0002.bak"
    assert _revision(backup) == "0001"
    assert _revision(path) == "0002"
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT name, extra FROM deck").fetchall() == [("kept", None)]


def test_failing_revision_returns_an_error_and_keeps_the_last_good_revision(
    tmp_path: Path, versions_dir: Callable[[str], Path]
) -> None:
    path = tmp_path / "learning.db"
    open_learning_db(path).unwrap().close()
    versions_dir(
        "    op.add_column('deck', sa.Column('extra', sa.Text()))\n    raise RuntimeError('boom')"
    )

    opened = open_learning_db(path)

    assert opened.is_err
    err = opened.unwrap_err()
    assert isinstance(err, MigrationFailed)
    assert err.stage == "upgrade"
    assert _revision(path) == "0001"
    with sqlite3.connect(path) as db:
        columns = [r[1] for r in db.execute("PRAGMA table_info(deck)")]
    assert "extra" not in columns
    assert (tmp_path / "learning.db.pre-0002.bak").exists()


def test_unknown_revision_is_refused_and_the_file_is_left_alone(tmp_path: Path) -> None:
    path = tmp_path / "learning.db"
    open_learning_db(path).unwrap().close()
    with sqlite3.connect(path) as db:
        db.execute("UPDATE alembic_version SET version_num = '9999'")
    before = path.read_bytes()

    opened = open_learning_db(path)

    err = opened.unwrap_err()
    assert isinstance(err, LearningDbTooNew)
    assert err.found == "9999"
    assert path.read_bytes() == before
    assert not list(tmp_path.glob("*.bak"))


def test_a_database_with_tables_but_no_revision_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "other.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE unrelated (x)")

    opened = open_learning_db(path)

    assert isinstance(opened.unwrap_err(), NotALearningDb)
