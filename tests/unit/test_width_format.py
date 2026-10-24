import io

import pytest
from rich.console import Console

from harald.lexicon.model import Entry, Example, Headword, LookupResult, Sense
from harald.render import render_lookup

LONG = "a very long gloss with Aufenthaltsgenehmigungsverlängerungsantragsformular inside"
RESULT = LookupResult(
    "Hund",
    (
        Headword(
            "Hund",
            "noun",
            (
                Entry(
                    "m",
                    "Hunde",
                    (
                        Sense(
                            "dog",
                            ("colloquial",),
                            (Example("Der Hund bellt.", "The dog barks.", False, None),),
                        ),
                        Sense(
                            LONG,
                            (),
                            (Example("Der  Hundt lief  daron.", None, True, "Anon., 1850"),),
                        ),
                    ),
                    ipa="/hʊnt/",
                ),
            ),
        ),
        Headword("Berlin", "name", (Entry("n", None, (Sense("Berlin", (), ()),)),)),
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
        LONG.replace(" ", ""),
        "/hʊnt/",
        "[colloquial]dog",
        "DerHundbellt.—Thedogbarks.",
        "DerHundtliefdaron.Anon.,1850",
        "propernoun",
        "Also:Hunde,Hundi",
    ):
        assert part in flat


def test_narrow_stacks_labels_above_values() -> None:
    console = Console(width=40, record=True, file=io.StringIO())
    console.print(render_lookup(RESULT))

    assert "noun" in console.export_text().splitlines()[1]
