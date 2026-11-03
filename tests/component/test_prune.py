from pathlib import Path

import pytest

from harald.build.errors import BuildLocked, PruneFailed
from harald.build.publish import build_lock
from harald.build.sources import DE_FILENAME, EN_FILENAME
from harald.lexicon.errors import LexiconError, LexiconMissing
from harald.use_cases.prune import PruneSources
from tests.conftest import Workspace


def _leftovers(sources: Path) -> None:
    (sources / f"{EN_FILENAME}.meta.json").write_text("{}")
    (sources / f"{EN_FILENAME}.part").write_bytes(b"half")
    (sources / f"{DE_FILENAME}.meta.json.part").write_text("{")


def test_prune_deletes_the_sources_their_sidecars_and_part_files(built: Workspace) -> None:
    sources = built.config.sources_dir
    _leftovers(sources)
    expected = sum(p.stat().st_size for p in sources.iterdir())

    freed = PruneSources(built.config).execute().unwrap()

    assert freed == expected
    assert list(sources.iterdir()) == []


def test_prune_keeps_files_it_does_not_know_and_both_databases(built: Workspace) -> None:
    stray = built.config.sources_dir / "notes.txt"
    stray.write_text("mine")
    built.config.learning_db.write_bytes(b"cards")
    lexicon_size = built.config.lexicon.stat().st_size

    PruneSources(built.config).execute().unwrap()

    assert stray.read_text() == "mine"
    assert built.config.learning_db.read_bytes() == b"cards"
    assert built.config.lexicon.stat().st_size == lexicon_size


def test_plan_lists_what_would_go_and_deletes_nothing(built: Workspace) -> None:
    sources = built.config.sources_dir
    before = sorted(p.name for p in sources.iterdir())

    planned = PruneSources(built.config).plan().unwrap()

    assert sorted(f.path.name for f in planned) == before
    assert sorted(p.name for p in sources.iterdir()) == before


def test_prune_refuses_without_a_lexicon_and_deletes_nothing(workspace: Workspace) -> None:
    before = sorted(p.name for p in workspace.config.sources_dir.iterdir())

    res = PruneSources(workspace.config).execute()

    assert isinstance(res.unwrap_err(), LexiconMissing)
    assert sorted(p.name for p in workspace.config.sources_dir.iterdir()) == before


def test_prune_refuses_while_a_build_holds_the_lock(built: Workspace) -> None:
    before = sorted(p.name for p in built.config.sources_dir.iterdir())
    built.config.staging_dir.mkdir(parents=True, exist_ok=True)

    with build_lock(built.config.staging_dir):
        res = PruneSources(built.config).execute()

    assert isinstance(res.unwrap_err(), BuildLocked)
    assert sorted(p.name for p in built.config.sources_dir.iterdir()) == before


def test_prune_with_nothing_to_delete_frees_nothing(built: Workspace) -> None:
    PruneSources(built.config).execute().unwrap()

    assert PruneSources(built.config).execute().unwrap() == 0
    assert PruneSources(built.config).plan().unwrap() == []


def test_prune_refuses_a_lexicon_that_does_not_open_and_deletes_nothing(
    workspace: Workspace,
) -> None:
    workspace.config.lexicon.parent.mkdir(parents=True)
    workspace.config.lexicon.write_bytes(b"not a database")
    before = sorted(p.name for p in workspace.config.sources_dir.iterdir())

    res = PruneSources(workspace.config).execute()

    assert isinstance(res.unwrap_err(), LexiconError)
    assert sorted(p.name for p in workspace.config.sources_dir.iterdir()) == before


def test_a_failed_delete_is_an_error_that_says_how_many_went(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = Path.unlink
    calls: list[Path] = []

    def flaky(self: Path, missing_ok: bool = False) -> None:
        calls.append(self)
        if len(calls) == 2:
            raise PermissionError(13, "Permission denied")
        real(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", flaky)

    err = PruneSources(built.config).execute().unwrap_err()

    assert isinstance(err, PruneFailed)
    assert err.deleted == 1
    assert "Permission denied" in str(err)
    assert "run 'harald-cli prune' again" in str(err)
