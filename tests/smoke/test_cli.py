import subprocess
import sys

import pytest

from harald.cli import main
from harald.use_cases.build import BuildLexicon
from tests.conftest import Workspace


def _harald(
    ws: Workspace, *args: str, env: dict[str, str] | None = None, config: bool = True
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "harald", *(["--config", str(ws.config_file)] if config else [])]
    return subprocess.run(
        [*cmd, *args],
        capture_output=True,
        text=True,
        env={"PATH": "", "HOME": str(ws.root), **(env or {})},
    )


def test_help_works_with_a_config_that_does_not_parse(workspace: Workspace) -> None:
    workspace.config_file.write_text("not = [valid toml")

    res = _harald(workspace, "lookup", "--help")

    assert res.returncode == 0
    assert "--conj" in res.stdout


def test_harald_config_is_honoured_without_the_flag(built: Workspace) -> None:
    res = _harald(
        built, "lookup", "Hund", config=False, env={"HARALD_CONFIG": str(built.config_file)}
    )

    assert res.returncode == 0, res.stderr
    assert "der Hund" in res.stdout


def test_unknown_subcommand_exits_2(workspace: Workspace) -> None:
    assert _harald(workspace, "nonsense").returncode == 2


def test_tui_refuses_a_missing_lexicon_before_starting(workspace: Workspace) -> None:
    res = subprocess.run(
        [sys.executable, "-m", "harald.tui", "--config", str(workspace.config_file)],
        capture_output=True,
        text=True,
        env={"PATH": "", "HOME": str(workspace.root)},
    )

    assert res.returncode == 2
    assert "harald-cli build" in res.stderr


def test_cli_without_a_command_shows_usage_and_not_the_tui(workspace: Workspace) -> None:
    res = _harald(workspace)

    assert "Usage:" in res.stdout + res.stderr
    assert "harald-cli" in res.stdout + res.stderr


def test_ctrl_c_exits_130(workspace: Workspace, monkeypatch: pytest.MonkeyPatch) -> None:
    def interrupted(self: BuildLexicon, fetch: bool, force: bool) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(BuildLexicon, "execute", interrupted)

    assert main(["--config", str(workspace.config_file), "build"]) == 130
