import time
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from rich.console import Group, RenderableType
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from harald.config import Config
from harald.use_cases.study import (
    AnswerArticle,
    AnswerStammformen,
    Grade,
    NextCard,
    SessionSummary,
    StammformenCheck,
)

# A double tap on "Show answer" must not land on a grade button that appears under the thumb.
_TAP_GUARD_S = 0.3
_GRADES = ((1, "Again"), (2, "Hard"), (3, "Good"), (4, "Easy"))
_ARTICLES = {"m": "der", "f": "die", "n": "das"}
_ARTICLE_BUTTONS = ((1, "der"), (2, "die"), (3, "das"))
_STAMM_LABELS = ("er/sie/es", "Präteritum", "Perfekt")


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
    if card_type == "article":
        lemma = content["lemma"]
        plural = f"   (pl. {content['plural']})" if content.get("plural") else ""
        return "Article", [f"{lemma}{plural}", content["hint"]], []
    if card_type == "stammformen":
        front = [f"{content['infinitive']}  -  {content['hint']}"]
        prefix = content["separable_prefix"]
        if prefix:
            stem = content["infinitive"].removeprefix(prefix)
            front += [f"TRENNBAR  {prefix}|{stem}", "(answer with the split forms)"]
        return "Stammformen", front, []
    return card_type, [_word(content)], []


def _stammformen_feedback(check: StammformenCheck, content: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for f in check.fields:
        given = f.given or "(empty)"
        lines.append(f"{f.label:<11} {given}  {'ok' if f.correct else 'WRONG'}")
        if not f.correct:
            lines.append(f"{'':<11} -> {f.expected}")
    lines.append("")
    lines.append("RIGHT - graded Good" if check.correct else "WRONG - graded Again")
    if content["separable_prefix"]:
        lines.append(f"trennbar: the prefix {content['separable_prefix']} goes to the")
        lines.append("end in main clauses")
    return lines


class StudyScreen(Screen[None]):
    TITLE = "Study"
    BINDINGS = [
        # one binding for space: Textual stops at the first binding for a key even when its
        # check_action refuses, so a second "continue" binding on space is never reached
        Binding("space", "advance", "Show"),
        Binding("enter", "continue", "Next"),
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
        self._feedback: list[str] | None = None
        self._graded = 0
        self._front_at = 0.0
        self._grades_at = 0.0

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        with VerticalScroll(id="body"):
            yield Static(id="card")
            with Vertical(id="fields"):
                for i, label in enumerate(_STAMM_LABELS):
                    with Horizontal(classes="field"):
                        yield Static(label, classes="field-label")
                        yield Input(compact=True, id=f"sf{i}")
        with Horizontal(id="buttons"):
            yield self._button("Show answer", "reveal")
            for n, name in _GRADES:
                yield self._button(f"{n} {name}", f"grade{n}")
            for n, name in _ARTICLE_BUTTONS:
                yield self._button(f"{n} {name}", f"art{n}")
            yield self._button("Next  (enter)", "cont")
        yield Footer(compact=True)

    @staticmethod
    def _button(label: str, id: str) -> Button:
        button = Button(label, id=id)
        button.can_focus = False
        return button

    def on_mount(self) -> None:
        self._next()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if self._card is None:
            return action in ("end",)
        article = self._card[1] == "article"
        checked = article or self._card[1] == "stammformen"
        if action == "advance":
            return self._feedback is not None or (not checked and not self._revealed)
        if action == "reveal":
            return not checked and not self._revealed
        if action == "continue":
            return self._feedback is not None
        if action == "grade":
            number = parameters[0]
            if article:
                return self._feedback is None and number in (1, 2, 3)
            return self._revealed and self._card[1] != "stammformen"
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
        self._feedback = None
        self._grades_at = time.monotonic()
        self._front_at = time.monotonic()
        self._show()
        if card.card_type == "stammformen":
            self._focus_fields()
        else:
            self.set_focus(None)

    def _show(self) -> None:
        if self._card is None:
            return
        _, card_type, content = self._card
        typed = card_type == "stammformen"
        heading, front, back = _card_faces(card_type, content)
        parts: list[RenderableType] = [
            Text(heading, style="dim", justify="center"),
            Text(""),
            Text("\n".join(front), justify="center"),
        ]
        if self._feedback is not None:
            parts += [
                Text(""),
                Text("\n".join(self._feedback), justify="left" if typed else "center"),
            ]
        if self._revealed:
            parts += [
                Text("-" * 20, style="dim", justify="center"),
                Text("\n".join(back), justify="center"),
            ]
        self.query_one("#card", Static).update(Group(*parts))
        self.sub_title = f"{self._graded} done"
        article = card_type == "article"
        checked = article or typed
        asking = article and self._feedback is None
        self.query_one("#fields").display = typed and self._feedback is None
        self.query_one("#reveal").display = not checked and not self._revealed
        self.query_one("#buttons").set_class(self._revealed, "-grading")
        for n, _ in _GRADES:
            self.query_one(f"#grade{n}").display = self._revealed
        for n, _ in _ARTICLE_BUTTONS:
            self.query_one(f"#art{n}").display = asking
        self.query_one("#cont").display = self._feedback is not None
        self.refresh_bindings()

    def _focus_fields(self) -> None:
        for i in range(len(_STAMM_LABELS)):
            self.query_one(f"#sf{i}", Input).value = ""
        self.query_one("#sf0", Input).focus()

    def action_reveal(self) -> None:
        self._revealed = True
        self._grades_at = time.monotonic()
        self._show()

    def action_continue(self) -> None:
        self._next()

    def action_advance(self) -> None:
        if self._feedback is not None:
            self._next()
        else:
            self.action_reveal()

    def action_answer_article(self, number: int) -> None:
        if self._card is None:
            return
        card_id, _, content = self._card
        chosen = _ARTICLE_BUTTONS[number - 1][1]
        duration_ms = int((time.monotonic() - self._front_at) * 1000)
        answered = AnswerArticle(self._config).execute(
            card_id, chosen, datetime.now(UTC), self._session_id, duration_ms
        )
        if answered.is_err:
            self.notify(str(answered.unwrap_err()), severity="error")
            return
        check = answered.unwrap()
        shown = f"{'/'.join(check.accepted)} {content['lemma']}"
        self._feedback = (
            [f"RIGHT   {shown}"]
            if check.correct
            else [f"WRONG   {shown}", f"(you chose: {chosen})"]
        )
        self._graded += 1
        self._grades_at = time.monotonic()
        self._show()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        number = int(cast(str, event.input.id).removeprefix("sf"))
        if number < len(_STAMM_LABELS) - 1:
            self.query_one(f"#sf{number + 1}", Input).focus()
        else:
            self._answer_stammformen()

    def _answer_stammformen(self) -> None:
        if self._card is None or self._feedback is not None:
            return
        card_id, _, content = self._card
        a, b, c = (self.query_one(f"#sf{i}", Input).value for i in range(len(_STAMM_LABELS)))
        duration_ms = int((time.monotonic() - self._front_at) * 1000)
        answered = AnswerStammformen(self._config).execute(
            card_id, (a, b, c), datetime.now(UTC), self._session_id, duration_ms
        )
        if answered.is_err:
            self.notify(str(answered.unwrap_err()), severity="error")
            return
        self._feedback = _stammformen_feedback(answered.unwrap(), content)
        self._graded += 1
        self._grades_at = time.monotonic()
        self._show()
        self.set_focus(None)

    def action_grade(self, rating: int) -> None:
        if self._card is None:
            return
        if self._card[1] == "article":
            self.action_answer_article(rating)
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
        elif time.monotonic() - self._grades_at < _TAP_GUARD_S:
            return
        elif button_id == "cont":
            self.action_continue()
        elif button_id.startswith("art"):
            self.action_answer_article(int(button_id.removeprefix("art")))
        else:
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
