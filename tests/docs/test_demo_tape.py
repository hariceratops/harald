import re

from tests.docs.checker import collect
from tests.docs.sample import ROOT

TAPE = ROOT / "docs" / "demo" / "taste.tape"

_TYPE = re.compile(r'Type(?:@\S+)?\s+(?:"(?P<dq>[^"]*)"|`(?P<bt>[^`]*)`)')


def _typed_while_shown(tape: str) -> list[str]:
    shown = True
    typed: list[str] = []
    for line in tape.splitlines():
        word = line.strip()
        if word == "Hide":
            shown = False
        elif word == "Show":
            shown = True
        elif shown and (m := _TYPE.match(word)):
            typed.append(m["dq"] if m["dq"] is not None else m["bt"])
    return typed


def test_the_demo_tape_types_the_readme_taste_in_order() -> None:
    (taste,) = [e for e in collect(ROOT).examples if e.page == "README.md"]
    assert _typed_while_shown(TAPE.read_text()) == [c.text for c in taste.commands]


def test_typed_while_shown_skips_the_hidden_prelude() -> None:
    tape = 'Hide\nType "a" Enter\nShow\nType@50ms `b c` Enter\nType "d"\n'
    assert _typed_while_shown(tape) == ["b c", "d"]
