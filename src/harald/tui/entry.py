from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from harald.lexicon.model import Headword
from harald.render import RenderHeadword


class EntryScreen(Screen[None]):
    BINDINGS = [
        Binding("c", "toggle_conjugation", "All tenses"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, headword: Headword) -> None:
        super().__init__()
        self._headword = headword
        self._full = False

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        with VerticalScroll(id="body"):
            yield Static(id="entry")
        yield Footer(compact=True)

    def on_mount(self) -> None:
        self.title = "Entry"
        self.sub_title = f"{self._headword.lemma} - {self._headword.pos}"
        self._show()

    def _show(self) -> None:
        self.query_one("#entry", Static).update(RenderHeadword(self._headword, self._full))

    def action_toggle_conjugation(self) -> None:
        self._full = not self._full
        self._show()
