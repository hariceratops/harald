import asyncio
import sqlite3
from datetime import UTC, datetime

import pytest
from textual.pilot import Pilot
from textual.widgets import Button

from harald.tui.app import HaraldApp
from harald.tui.home import HomeScreen
from harald.tui.study import StudyScreen, SummaryScreen
from harald.use_cases.cards import CreateWordCards, PlanWordCards
from harald.use_cases.lexicon import LoadHeadword
from tests.conftest import Workspace
from tests.tui.helpers import assert_inside, static_lines
from tests.tui.test_navigation import SIZES, _drive


def _seed(ws: Workspace) -> None:
    hund = LoadHeadword(ws.config).execute("Hund", "noun").unwrap().unwrap()
    plan = PlanWordCards(ws.config).execute(hund, 0, [0], []).unwrap()
    CreateWordCards(ws.config).execute(plan, datetime(2026, 1, 1, tzinfo=UTC)).unwrap()


def _reviews(ws: Workspace) -> list[tuple[int, str]]:
    with sqlite3.connect(ws.config.learning_db) as db:
        return db.execute("SELECT rating, session_id FROM review ORDER BY id").fetchall()


@pytest.mark.parametrize("size", SIZES)
def test_study_reveal_grade_and_summary(built: Workspace, size: tuple[int, int]) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, StudyScreen)
        assert any("der Hund" in line for line in static_lines(app.screen, "#card"))
        assert app.screen.query_one("#reveal", Button).display
        assert not app.screen.query_one("#grade4", Button).display
        assert_inside(app.screen, size)

        await pilot.press("space")
        await pilot.pause()
        assert app.screen.query_one("#grade4", Button).display
        assert_inside(app.screen, size)
        await pilot.press("4")
        await pilot.pause()
        assert len(_reviews(built)) == 1

        await pilot.press("space")
        await pilot.press("4")
        await pilot.pause()
        assert isinstance(app.screen, SummaryScreen)
        lines = static_lines(app.screen, "#summary")
        assert any("2 cards reviewed" in line for line in lines)
        assert any("2 answered correctly" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        sessions = {s for _, s in _reviews(built)}
        assert len(sessions) == 1

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, HomeScreen)

    _drive(built, size, script)


def test_a_grade_before_the_reveal_is_ignored(built: Workspace) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.press("3")
        await pilot.pause()
        assert _reviews(built) == []

    _drive(built, (40, 30), script)


def test_grade_buttons_ignore_a_tap_right_after_they_appear(built: Workspace) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await pilot.click("#reveal")
        await pilot.pause()
        await pilot.click("#grade4")
        await pilot.pause()
        assert _reviews(built) == []
        await asyncio.sleep(0.35)
        await pilot.click("#grade4")
        await pilot.pause()
        assert [r for r, _ in _reviews(built)] == [4]

    _drive(built, (40, 30), script)


def test_escape_ends_the_session_with_a_summary(built: Workspace) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SummaryScreen)
        assert any("0 cards reviewed" in line for line in static_lines(app.screen, "#summary"))

    _drive(built, (40, 30), script)


def test_no_cards_goes_straight_to_the_summary(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, SummaryScreen)

    _drive(built, (40, 30), script)


def test_a_learning_db_from_a_newer_harald_is_refused_with_a_message(built: Workspace) -> None:
    with sqlite3.connect(built.config.learning_db) as db:
        db.execute("CREATE TABLE alembic_version (version_num TEXT)")
        db.execute("INSERT INTO alembic_version VALUES ('9999')")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, HomeScreen)
        assert any("does not know" in n.message for n in app._notifications)

    _drive(built, (40, 30), script)
