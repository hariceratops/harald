from dataclasses import dataclass
from typing import Any

from harald.text import answer_matches

ARTICLES = {"m": "der", "f": "die", "n": "das"}


@dataclass(frozen=True)
class ArticleCheck:
    correct: bool
    accepted: tuple[str, ...]


def check_article(gender: str, chosen: str) -> ArticleCheck:
    """Any of the word's genders is correct (Band, See, Leiter)."""
    accepted = tuple(ARTICLES[g] for g in gender if g in ARTICLES)
    return ArticleCheck(chosen in accepted, accepted)


# German grammar, not source data: the auxiliary as it stands before the participle
AUXILIARY_3SG = {"haben": "hat", "sein": "ist"}


@dataclass(frozen=True)
class FieldCheck:
    label: str
    given: str
    correct: bool
    expected: str


@dataclass(frozen=True)
class StammformenCheck:
    correct: bool
    fields: tuple[FieldCheck, ...]


def check_stammformen(content: dict[str, Any], given: tuple[str, str, str]) -> StammformenCheck:
    """All three fields must match. A verb with two auxiliaries accepts either Perfekt."""
    perfect = [
        f"{AUXILIARY_3SG.get(aux, aux)} {content['participle']}" for aux in content["auxiliaries"]
    ]
    wanted = (
        ("er/sie/es", [content["pres3sg"]]),
        ("Präteritum", [content["preterite"]]),
        ("Perfekt", perfect),
    )
    fields = tuple(
        FieldCheck(
            label, typed, any(answer_matches(typed, e) for e in accepted), "/".join(accepted)
        )
        for (label, accepted), typed in zip(wanted, given, strict=True)
    )
    return StammformenCheck(all(f.correct for f in fields), fields)
