from pathlib import Path

from harald.build.errors import SourceMissing
from harald.build.sources import EN_FILENAME
from harald.use_cases.build import BuildLexicon
from tests.conftest import Workspace


def test_build_lexicon_returns_the_report_and_the_info(workspace: Workspace) -> None:
    done = BuildLexicon(workspace.config).execute(fetch=False, force=False).unwrap()

    assert done.report.published
    assert [c.label for c in done.info.coverage] == [
        "verbs with complete Stammformen",
        "nouns with a gender",
        "senses with a translated example",
    ]
    names = [s.title for s in done.info.sources]
    assert names == sorted(names)


def test_build_lexicon_with_a_missing_source_opens_nothing(workspace: Workspace) -> None:
    (Path(workspace.config.sources_dir) / EN_FILENAME).unlink()

    res = BuildLexicon(workspace.config).execute(fetch=False, force=False)

    assert isinstance(res.unwrap_err(), SourceMissing)
    assert not workspace.config.lexicon.exists()
