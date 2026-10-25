from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, OptionList
from textual.widgets.option_list import Option

from harald.config import Config
from harald.lexicon.model import Headword
from harald.tui.entry import EntryScreen
from harald.use_cases.lexicon import LoadHeadword, LookUpGerman


class LookupScreen(Screen[None]):
    TITLE = "Lookup"
    SUB_TITLE = "Deutsch"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._shown: tuple[Headword, ...] = ()
        self._also: tuple[tuple[str, str], ...] = ()

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        yield Input(placeholder="DE > ", compact=True, id="query")
        yield OptionList(id="results")
        yield Footer(compact=True)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        looked_up = LookUpGerman(self._config).execute(query)
        if looked_up.is_err:
            self.notify(str(looked_up.unwrap_err()), severity="error")
            return
        result = looked_up.unwrap()
        if not result.shown:
            self.notify(f"No match for {query!r}")
            return
        self._shown, self._also = result.shown, result.also
        results = self.query_one("#results", OptionList)
        results.clear_options()
        for hw in self._shown:
            label = f"{hw.lemma}  {_pos_label(hw.pos)}"
            if hw.via_form:
                label += f"  form: {hw.via_form}"
            results.add_option(Option(label))
        for lemma, pos in self._also:
            results.add_option(Option(f"{lemma}  {_pos_label(pos)}"))
        results.highlighted = 0
        results.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        index = event.option_index
        if index < len(self._shown):
            self.app.push_screen(EntryScreen(self._shown[index]))
            return
        lemma, pos = self._also[index - len(self._shown)]
        loaded = LoadHeadword(self._config).execute(lemma, pos)
        if loaded.is_err:
            self.notify(str(loaded.unwrap_err()), severity="error")
            return
        found = loaded.unwrap()
        if found.is_none:
            self.notify(f"{lemma} is no longer in the lexicon", severity="error")
            return
        self.app.push_screen(EntryScreen(found.unwrap()))


def _pos_label(pos: str) -> str:
    return "proper noun" if pos == "name" else pos
