from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
from rich.text import Text

from harald.lexicon.model import Entry, Headword, LookupResult

_ARTICLES = {"m": "der", "f": "die", "n": "das"}
_NARROW_BELOW = 60


def _pos_label(pos: str) -> str:
    return "proper noun" if pos == "name" else pos


def _title(hw: Headword, entry: Entry) -> str:
    if hw.pos == "noun" and entry.gender:
        return f"{'/'.join(_ARTICLES[g] for g in entry.gender)} {hw.lemma}"
    return hw.lemma


class RenderHeadword:
    def __init__(self, hw: Headword) -> None:
        self.hw = hw

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        narrow = options.max_width < _NARROW_BELOW
        label = _pos_label(self.hw.pos)
        for entry in self.hw.entries:
            title = Text(_title(self.hw, entry), style="bold")
            if narrow:
                yield title
                yield Text(label, style="dim")
                if entry.plural:
                    yield Text(f"Plural: {entry.plural}")
            else:
                line = Text.assemble(title, f"  {label}", style="")
                if entry.plural:
                    line.append(f"  Plural: {entry.plural}")
                yield line
            senses = Table.grid(padding=(0, 1))
            senses.add_column(justify="right", no_wrap=True)
            senses.add_column(ratio=1, overflow="fold")
            for i, gloss in enumerate(entry.senses, 1):
                senses.add_row(f"{i}.", gloss)
            yield senses
            yield Text("")


class RenderLookup:
    def __init__(self, result: LookupResult) -> None:
        self.result = result

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        for hw in self.result.shown:
            yield RenderHeadword(hw)
        if self.result.also:
            names = ", ".join(lemma for lemma, _ in self.result.also)
            yield Text(f"Also: {names}", style="dim")


def render_lookup(result: LookupResult) -> RenderLookup:
    return RenderLookup(result)
