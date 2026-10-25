from textual.app import App

from harald.config import Config
from harald.tui.home import HomeScreen


class HaraldApp(App[None]):
    CSS_PATH = "harald.tcss"
    ENABLE_COMMAND_PALETTE = False
    HORIZONTAL_BREAKPOINTS = [(0, "-narrow"), (60, "-wide")]
    VERTICAL_BREAKPOINTS = [(0, "-short"), (16, "-normal")]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config

    def on_mount(self) -> None:
        self.push_screen(HomeScreen(self.config))
