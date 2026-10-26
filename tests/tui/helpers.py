import io

from rich.console import Console
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Static


def static_lines(screen: Screen[None], selector: str) -> list[str]:
    static = screen.query_one(selector, Static)
    console = Console(width=static.size.width, file=io.StringIO(), record=True)
    console.print(static.content)
    return console.export_text().splitlines()


def assert_inside(screen: Screen[None], size: tuple[int, int]) -> None:
    for widget in screen.walk_children(Widget):
        if not widget.display or not widget.region.area:
            continue
        region = widget.region
        assert region.x >= 0 and region.right <= size[0], f"{widget} overflows the width"
