import io

import pytest
from rich.console import Console

from harald.lexicon.model import Entry, Headword, LookupResult
from harald.render import render_lookup

LONG = "a very long gloss with Aufenthaltsgenehmigungsverlängerungsantragsformular inside"
RESULT = LookupResult(
    "Hund",
    (
        Headword("Hund", "noun", (Entry("m", "Hunde", ("dog", LONG)),)),
        Headword("Berlin", "name", (Entry("n", None, ("Berlin",)),)),
    ),
    (("Hunde", "noun"), ("Hundi", "noun")),
)


@pytest.mark.parametrize("width", [40, 60, 80, 100])
def test_lookup_fits_width_and_loses_nothing(width: int) -> None:
    console = Console(width=width, record=True, file=io.StringIO())

    console.print(render_lookup(RESULT))
    text = console.export_text()

    assert all(len(line) <= width for line in text.splitlines())
    flat = "".join(text.split())
    for part in (
        "derHund",
        "Plural:Hunde",
        "1.dog",
        LONG.replace(" ", ""),
        "propernoun",
        "Also:Hunde,Hundi",
    ):
        assert part in flat


def test_narrow_stacks_labels_above_values() -> None:
    console = Console(width=40, record=True, file=io.StringIO())
    console.print(render_lookup(RESULT))

    assert "noun" in console.export_text().splitlines()[1]
