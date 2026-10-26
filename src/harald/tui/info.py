from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from harald.config import Config
from harald.render import render_info
from harald.use_cases.lexicon import QueryLexiconInfo


class InfoScreen(Screen[None]):
    TITLE = "Info"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        with VerticalScroll(id="body"):
            yield Static(id="info")
        yield Footer(compact=True)

    def on_mount(self) -> None:
        queried = QueryLexiconInfo(self._config).execute()
        if queried.is_err:
            self.notify(str(queried.unwrap_err()), severity="error")
            return
        self.query_one("#info", Static).update(render_info(queried.unwrap()))
