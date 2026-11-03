import importlib.util
import json
import sqlite3
from collections.abc import Sequence
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).parents[2] / "dev" / "audit" / "checked_answers.py"
START = datetime(2026, 10, 20, 9, 0)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("checked_answers", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = _load()


def _seed(path: Path, reviews: Sequence[tuple[str, int, str | None]]) -> None:
    db = sqlite3.connect(path)
    db.executescript(
        "CREATE TABLE card (id INTEGER PRIMARY KEY, card_type TEXT, content TEXT);"
        "CREATE TABLE review (id INTEGER PRIMARY KEY, card_id INTEGER, reviewed_at TEXT,"
        " rating INTEGER, answer TEXT);"
    )
    contents = {
        "meaning_en_de": {"lemma": "Hund", "gender": "m", "gloss": "dog"},
        "meaning_de_de": {"lemma": "Katze", "gender": "f", "definition": "a pet"},
        "meaning_de_en": {"lemma": "Band", "gender": "nd", "gloss": "ribbon"},
    }
    for i, (card_type, content) in enumerate(contents.items(), 1):
        db.execute("INSERT INTO card VALUES (?,?,?)", (i, card_type, json.dumps(content)))
    ids = {t: i for i, t in enumerate(contents, 1)}
    for n, (card_type, rating, answer) in enumerate(reviews):
        at = (START + timedelta(hours=n)).isoformat(sep=" ")
        db.execute(
            "INSERT INTO review (card_id, reviewed_at, rating, answer) VALUES (?,?,?,?)",
            (ids[card_type], at, rating, answer),
        )
    db.commit()
    db.close()


def _run(path: Path, keys: list[str], now: datetime) -> tuple[list[str], str]:
    asked = iter(keys)
    prompts: list[str] = []

    def read(prompt: str) -> str:
        prompts.append(prompt)
        return next(asked, "q")

    lines: list[str] = []
    audit.run(path, read, lines.append, now)
    return prompts, "\n".join(lines)


SEED = [
    ("meaning_en_de", 3, "der Hund"),
    ("meaning_en_de", 2, "Hund"),
    ("meaning_en_de", 1, "die Hund"),
    ("meaning_de_de", 1, "Kater | Katz"),
    ("meaning_de_de", 1, ""),
    ("meaning_de_en", 1, None),
    ("meaning_en_de", 1, None),
]


def test_selection_keeps_failed_checked_reviews_only() -> None:
    rows = [
        audit.Review("meaning_en_de", 3, "a", {}, START),
        audit.Review("meaning_en_de", 1, "b", {}, START),
        audit.Review("meaning_de_de", 1, "", {}, START),
        audit.Review("meaning_de_en", 1, "c", {}, START),
        audit.Review("meaning_de_de", 1, None, {}, START),
    ]

    checked = audit.checked(rows)

    assert [r.answer for r in checked] == ["a", "b", ""]
    assert [r.answer for r in audit.to_ask(checked)] == ["b"]


def test_share_is_marked_over_checked_covered() -> None:
    assert audit.share(1, 20) == pytest.approx(0.05)
    assert audit.share(0, 0) == 0.0


def test_audit_asks_each_failed_answer_and_reports_the_share(tmp_path: Path) -> None:
    db = tmp_path / "learning.db"
    _seed(db, SEED)
    before = db.read_bytes()

    prompts, out = _run(db, ["y", "", "n"], START + timedelta(days=1))

    assert len(prompts) == 2
    assert "die Hund" in out
    assert "Kater | Katz" in out
    assert "der Hund" in out
    assert "Katze" in out
    assert "5 checked reviews" in out
    assert "1 empty" in out
    assert "neither threshold" in out
    assert "1 of 5" in out
    assert "20%" in out
    assert "reconsidered" in out
    assert db.read_bytes() == before


def test_quit_stops_asking_and_still_reports(tmp_path: Path) -> None:
    db = tmp_path / "learning.db"
    _seed(db, SEED)

    prompts, out = _run(db, ["q"], START + timedelta(days=1))

    assert len(prompts) == 1
    assert "0 of 5" in out
    assert "reconsidered" not in out


def test_share_at_or_below_five_percent_is_not_flagged(tmp_path: Path) -> None:
    db = tmp_path / "learning.db"
    _seed(db, [("meaning_en_de", 3, "der Hund")] * 19 + [("meaning_en_de", 1, "x")])

    _, out = _run(db, ["y"], START + timedelta(days=1))

    assert "5%" in out
    assert "reconsidered" not in out


def test_trigger_is_200_reviews_or_14_days(tmp_path: Path) -> None:
    db = tmp_path / "learning.db"
    _seed(db, [("meaning_en_de", 3, "der Hund")] * 200)
    _, by_count = _run(db, [], START + timedelta(days=1))
    _, by_time = _run(db, [], START + timedelta(days=14))

    assert "200 reviews reached" in by_count
    assert "two weeks reached" in by_time


def test_missing_database_is_reported_without_creating_it(tmp_path: Path) -> None:
    db = tmp_path / "nope.db"

    _, out = _run(db, [], START)

    assert "cannot open" in out
    assert not db.exists()
