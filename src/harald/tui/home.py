from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList
from textual.widgets.option_list import Option

from harald.config import Config
from harald.tui.info import InfoScreen
from harald.tui.lookup import LookupScreen


class HomeScreen(Screen[None]):
    TITLE = "Harald"
    BINDINGS = [
        Binding("l", "lookup", "Lookup", show=False),
        Binding("i", "info", "Info", show=False),
        Binding("q", "app.quit", "Quit"),
    ]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        yield OptionList(
            Option("l  Look up German", id="lookup"),
            Option("i  Info", id="info"),
            id="menu",
        )
        yield Footer(compact=True)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id == "lookup":
            self.action_lookup()
        else:
            self.action_info()

    def action_lookup(self) -> None:
        self.app.push_screen(LookupScreen(self._config))

    def action_info(self) -> None:
        self.app.push_screen(InfoScreen(self._config))
