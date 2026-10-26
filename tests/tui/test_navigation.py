import asyncio
import io
from collections.abc import Awaitable, Callable

import pytest
from rich.console import Console
from textual.pilot import Pilot
from textual.widgets import Input, OptionList, Static

from harald.tui.app import HaraldApp
from harald.tui.entry import EntryScreen
from harald.tui.lookup import LookupScreen
from tests.conftest import Workspace

SIZES = [(40, 30), (40, 12), (100, 30)]


def _drive(
    ws: Workspace,
    size: tuple[int, int],
    script: Callable[[HaraldApp, Pilot[None]], Awaitable[None]],
) -> None:
    async def run() -> None:
        app = HaraldApp(ws.config)
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            await script(app, pilot)

    asyncio.run(run())


async def _search(app: HaraldApp, pilot: Pilot[None], word: str) -> None:
    await pilot.press("l")
    await pilot.pause()
    app.screen.query_one(Input).value = word
    await pilot.press("enter")
    await pilot.pause()


def _entry_lines(app: HaraldApp) -> list[str]:
    static = app.screen.query_one("#entry", Static)
    console = Console(width=static.size.width, file=io.StringIO(), record=True)
    console.print(static.content)
    return console.export_text().splitlines()


@pytest.mark.parametrize("size", SIZES)
def test_lookup_then_entry_shows_the_headword_within_the_width(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _search(app, pilot, "Hund")
        assert isinstance(app.screen, LookupScreen)
        assert app.screen.query_one(OptionList).has_focus
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, EntryScreen)
        lines = _entry_lines(app)
        assert any("der Hund" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, LookupScreen)

    _drive(built, size, script)


def test_short_layout_hides_the_header_and_keeps_the_footer(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        assert app.screen.has_class("-short")
        assert not app.screen.query_one("Header").display
        assert app.screen.query_one("Footer").display

    _drive(built, (40, 12), script)


def test_narrow_and_wide_classes_follow_the_width(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        assert app.screen.has_class("-narrow")

    _drive(built, (40, 30), script)

    async def wide(app: HaraldApp, pilot: Pilot[None]) -> None:
        assert app.screen.has_class("-wide")

    _drive(built, (100, 30), wide)


def test_a_form_result_names_the_form_typed(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _search(app, pilot, "lief")
        assert isinstance(app.screen, LookupScreen)
        first = app.screen.query_one(OptionList).get_option_at_index(0)
        assert "laufen" in str(first.prompt)
        assert "form: lief" in str(first.prompt)

    _drive(built, (40, 30), script)


def test_escape_from_results_returns_to_the_query_for_another_search(
    built: Workspace,
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _search(app, pilot, "Hund")
        assert app.screen.query_one(OptionList).has_focus
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, LookupScreen)
        query = app.screen.query_one("#query", Input)
        assert query.has_focus
        assert query.selected_text == "Hund"
        await pilot.press(*"Hund", "enter")
        await pilot.pause()
        assert app.screen.query_one(OptionList).has_focus
        await pilot.press("slash")
        await pilot.pause()
        assert query.has_focus
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, LookupScreen)

    _drive(built, (40, 30), script)


def test_no_match_stays_on_lookup(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _search(app, pilot, "Zzzzzz")
        assert isinstance(app.screen, LookupScreen)
        assert app.screen.query_one(OptionList).option_count == 0

    _drive(built, (40, 30), script)


def test_conjugation_key_shows_every_tense(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _search(app, pilot, "laufen")
        await pilot.press("enter")
        await pilot.pause()
        before = _entry_lines(app)
        await pilot.press("c")
        await pilot.pause()
        after = _entry_lines(app)
        assert len(after) > len(before)
        assert any("Konjunktiv II" in line for line in after)

    _drive(built, (40, 30), script)


def test_info_screen_lists_sources(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("i")
        await pilot.pause()
        static = app.screen.query_one("#info", Static)
        console = Console(width=static.size.width, file=io.StringIO(), record=True)
        console.print(static.content)
        assert "Sources" in console.export_text()

    _drive(built, (40, 30), script)
