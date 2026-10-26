import time
import uuid
from datetime import UTC, datetime
from typing import Any

from rich.console import Group, RenderableType
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from harald.config import Config
from harald.use_cases.study import Grade, NextCard, SessionSummary

# A double tap on "Show answer" must not land on a grade button that appears under the thumb.
_TAP_GUARD_S = 0.3
_GRADES = ((1, "Again"), (2, "Hard"), (3, "Good"), (4, "Easy"))
_ARTICLES = {"m": "der", "f": "die", "n": "das"}


def _word(content: dict[str, Any]) -> str:
    article = "/".join(_ARTICLES.get(g, "") for g in content.get("gender", ""))
    return f"{article} {content['lemma']}".strip()


def _card_faces(card_type: str, content: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    """Heading, front lines, back lines."""
    example = content.get("example") or {}
    if card_type == "meaning_de_en":
        gloss = content["gloss"]
        if content.get("labels"):
            gloss = f"[{', '.join(content['labels'])}] {gloss}"
        return (
            "German -> English",
            [_word(content), content["pos"], *([""] + [example["text"]] if example else [])],
            [gloss, *([example["translation"]] if example else [])],
        )
    if card_type == "meaning_en_de":
        return (
            "English -> German",
            [
                content["gloss"],
                content["pos"],
                *([""] + [example["translation"]] if example else []),
            ],
            [_word(content), *([example["text"]] if example else [])],
        )
    if card_type == "meaning_de_de":
        return "German -> German", [_word(content), content["pos"]], [content["definition"]]
    return card_type, [_word(content)], []


class StudyScreen(Screen[None]):
    TITLE = "Study"
    BINDINGS = [
        Binding("space", "reveal", "Show"),
        # the grade buttons already name their keys, and four more hints overflow 40 columns
        *(Binding(str(n), f"grade({n})", f"{n} {name}", show=False) for n, name in _GRADES),
        Binding("escape", "end", "End"),
    ]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._session_id = uuid.uuid4().hex
        self._card: tuple[int, str, dict[str, Any]] | None = None
        self._revealed = False
        self._graded = 0
        self._front_at = 0.0
        self._grades_at = 0.0

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        with VerticalScroll(id="body"):
            yield Static(id="card")
        with Horizontal(id="buttons"):
            yield self._button("Show answer", "reveal")
            for n, name in _GRADES:
                yield self._button(f"{n} {name}", f"grade{n}")
        yield Footer(compact=True)

    @staticmethod
    def _button(label: str, id: str) -> Button:
        button = Button(label, id=id)
        button.can_focus = False
        return button

    def on_mount(self) -> None:
        self._next()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "reveal":
            return self._card is not None and not self._revealed
        if action == "grade":
            return self._card is not None and self._revealed
        return True

    def _next(self) -> None:
        asked = NextCard(self._config).execute(datetime.now(UTC))
        if asked.is_err:
            self.notify(str(asked.unwrap_err()), severity="error")
            self.app.pop_screen()
            return
        found = asked.unwrap()
        if found.is_none:
            self._finish()
            return
        card = found.unwrap()
        self._card = (card.id, card.card_type, card.content)
        self._revealed = False
        self._front_at = time.monotonic()
        self._show()

    def _show(self) -> None:
        if self._card is None:
            return
        _, card_type, content = self._card
        heading, front, back = _card_faces(card_type, content)
        parts: list[RenderableType] = [
            Text(heading, style="dim", justify="center"),
            Text(""),
            Text("\n".join(front), justify="center"),
        ]
        if self._revealed:
            parts += [
                Text("-" * 20, style="dim", justify="center"),
                Text("\n".join(back), justify="center"),
            ]
        self.query_one("#card", Static).update(Group(*parts))
        self.sub_title = f"{self._graded} done"
        self.query_one("#reveal").display = not self._revealed
        self.query_one("#buttons").set_class(self._revealed, "-grading")
        for n, _ in _GRADES:
            self.query_one(f"#grade{n}").display = self._revealed
        self.refresh_bindings()

    def action_reveal(self) -> None:
        self._revealed = True
        self._grades_at = time.monotonic()
        self._show()

    def action_grade(self, rating: int) -> None:
        if self._card is None:
            return
        card_id = self._card[0]
        duration_ms = int((time.monotonic() - self._front_at) * 1000)
        graded = Grade(self._config).execute(
            card_id, rating, datetime.now(UTC), self._session_id, duration_ms
        )
        if graded.is_err:
            self.notify(str(graded.unwrap_err()), severity="error")
            return
        self._graded += 1
        self._next()

    def action_end(self) -> None:
        self._finish()

    def _finish(self) -> None:
        self.app.switch_screen(SummaryScreen(self._config, self._session_id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        button_id = event.button.id or ""
        if button_id == "reveal":
            self.action_reveal()
        elif time.monotonic() - self._grades_at >= _TAP_GUARD_S:
            self.action_grade(int(button_id.removeprefix("grade")))


class SummaryScreen(Screen[None]):
    TITLE = "Session finished"
    BINDINGS = [
        Binding("enter", "home", "Home"),
        Binding("escape", "home", "Home", show=False),
    ]

    def __init__(self, config: Config, session_id: str) -> None:
        super().__init__()
        self._config = config
        self._session_id = session_id

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        with VerticalScroll(id="body"):
            yield Static(id="summary")
        with Horizontal(id="buttons"):
            home = Button("Home (enter)", id="home")
            home.can_focus = False
            yield home
        yield Footer(compact=True)

    def on_mount(self) -> None:
        summed = SessionSummary(self._config).execute(self._session_id)
        if summed.is_err:
            self.notify(str(summed.unwrap_err()), severity="error")
            return
        counts = summed.unwrap()
        noun = "card" if counts.reviewed == 1 else "cards"
        self.query_one("#summary", Static).update(
            Text(
                f"\n{counts.reviewed} {noun} reviewed\n{counts.correct} answered correctly",
                justify="center",
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_home()

    def action_home(self) -> None:
        self.app.pop_screen()
