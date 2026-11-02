"""Interactive, read-only audit of the checked meaning answers (issue 027, design 7.14).

Usage: python dev/audit/checked_answers.py PATH_TO_LEARNING_DB_COPY

Point it at a copy of the newest phone backup, not the live file. The database is opened
read-only and nothing is stored: the marks live for the run only.
"""

import json
import sqlite3
import sys
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

CHECKED_TYPES = ("meaning_en_de", "meaning_de_de")
AGAIN = 1
REVIEW_THRESHOLD = 200
DAYS_THRESHOLD = 14
SHARE_LIMIT = 0.05
ARTICLES = {"m": "der", "f": "die", "n": "das"}


@dataclass(frozen=True)
class Review:
    card_type: str
    rating: int
    answer: str | None
    content: dict[str, Any]
    reviewed_at: datetime


def checked(reviews: list[Review]) -> list[Review]:
    # An old review has no stored answer; it was self-graded and cannot be audited.
    return [r for r in reviews if r.card_type in CHECKED_TYPES and r.answer is not None]


def is_empty(review: Review) -> bool:
    return not (review.answer or "").replace("|", "").strip()


def to_ask(checked_reviews: list[Review]) -> list[Review]:
    return [r for r in checked_reviews if r.rating == AGAIN and not is_empty(r)]


def share(marked: int, covered: int) -> float:
    return marked / covered if covered else 0.0


def expected(content: dict[str, Any]) -> str:
    article = "/".join(ARTICLES.get(g, "") for g in content.get("gender", ""))
    return f"{article} {content['lemma']}".strip()


def _load(db: sqlite3.Connection) -> list[Review]:
    rows = db.execute(
        "SELECT c.card_type, r.rating, r.answer, c.content, r.reviewed_at"
        " FROM review r JOIN card c ON c.id = r.card_id ORDER BY r.reviewed_at, r.id"
    ).fetchall()
    return [Review(t, g, a, json.loads(c), datetime.fromisoformat(at)) for t, g, a, c, at in rows]


def _trigger(covered: list[Review], now: datetime) -> str:
    if not covered:
        return "No checked reviews yet; neither threshold (200 reviews, two weeks) reached."
    reached = []
    if len(covered) >= REVIEW_THRESHOLD:
        reached.append(f"{REVIEW_THRESHOLD} reviews reached")
    if now - covered[0].reviewed_at >= timedelta(days=DAYS_THRESHOLD):
        reached.append("two weeks reached")
    if reached:
        return "Threshold: " + ", ".join(reached) + "."
    return "Threshold: neither threshold (200 reviews, two weeks) reached yet; running anyway."


def run(
    path: Path, read: Callable[[str], str], write: Callable[[str], object], now: datetime
) -> None:
    uri = f"file:{quote(str(path))}?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as db:
            reviews = _load(db)
    except sqlite3.Error as e:
        write(f"cannot open {path}: {e}")
        return
    covered = checked(reviews)
    asked = to_ask(covered)
    empty = sum(1 for r in covered if r.rating == AGAIN and is_empty(r))
    write(f"{len(covered)} checked reviews covered, {len(asked)} failed to ask, {empty} empty.")
    write(_trigger(covered, now))
    marked = 0
    for n, review in enumerate(asked, 1):
        write(f"\n[{n}/{len(asked)}] {review.card_type}")
        write(f"  typed:    {review.answer}")
        write(f"  expected: {expected(review.content)}")
        reply = read("Was I right? y / n (Enter) / q: ").strip().lower()
        if reply == "q":
            break
        marked += reply == "y"
    ratio = share(marked, len(covered))
    write(f"\n{marked} of {len(covered)} checked reviews marked y ({ratio:.0%}).")
    if ratio > SHARE_LIMIT:
        write("More than 5%: a way to claim a right answer should be reconsidered.")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    run(Path(argv[1]), _input, print, datetime.now())
    return 0


def _input(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return "q"


if __name__ == "__main__":
    sys.exit(main(sys.argv))
