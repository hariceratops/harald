import asyncio

from textual.widgets import Input, OptionList

from harald.tui.app import HaraldApp
from harald.tui.entry import EntryScreen
from tests.conftest import Workspace
from tests.smoke.test_cli import _harald


def test_tui_browses_a_lexicon_built_by_the_cli(workspace: Workspace) -> None:
    built = _harald(workspace, "build")
    assert built.returncode == 0, built.stderr

    async def run() -> None:
        app = HaraldApp(workspace.config)
        async with app.run_test(size=(40, 30)) as pilot:
            await pilot.press("l")
            await pilot.pause()
            app.screen.query_one(Input).value = "Hund"
            await pilot.press("enter")
            await pilot.pause()
            assert app.screen.query_one(OptionList).option_count > 0
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, EntryScreen)

    asyncio.run(run())
