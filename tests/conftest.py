# Remaining TODO for later slices: hand-cut laufen, anrufen, verschlimmbessern, use entries
# in fixtures/, a tmp learning.db factory and a pinned clock.
import gzip
from dataclasses import dataclass
from pathlib import Path

import pytest

from harald.build.sources import DE_FILENAME, EN_FILENAME
from harald.config import Config

FIXTURES = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class Workspace:
    root: Path
    config: Config
    config_file: Path


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    sources = tmp_path / "sources"
    sources.mkdir()
    with gzip.open(sources / EN_FILENAME, "wb") as f:
        f.write((FIXTURES / "en-edition.jsonl").read_bytes())
    with gzip.open(sources / DE_FILENAME, "wb") as f:
        f.write((FIXTURES / "de-edition.jsonl").read_bytes())
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        f'lexicon = "{tmp_path / "out" / "lexicon.db"}"\n'
        f'sources_dir = "{sources}"\n'
        f'staging_dir = "{tmp_path / "staging"}"\n'
        "build_min_entries = 0\n"
    )
    config = Config(
        lexicon=tmp_path / "out" / "lexicon.db",
        sources_dir=sources,
        staging_dir=tmp_path / "staging",
        build_min_entries=0,
    )
    return Workspace(tmp_path, config, config_file)


@pytest.fixture
def built(workspace: Workspace) -> Workspace:
    from harald.build.run import build

    assert build(workspace.config).is_ok
    return workspace
