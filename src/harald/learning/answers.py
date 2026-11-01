from dataclasses import dataclass
from typing import Any, Literal

from fsrs import Rating

from harald.lexicon.model import PERSONS
from harald.text import answer_matches, normalise_answer

ARTICLES = {"m": "der", "f": "die", "n": "das"}
RECOGNISED_ARTICLES = frozenset("der die das ein eine einen einem einer eines den dem des".split())


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


def check_conjugation(content: dict[str, Any], given: str) -> FieldCheck:
    label = dict(PERSONS)[content["slot"].rsplit(".", 1)[1]]
    forms = content["forms"]
    return FieldCheck(label, given, any(answer_matches(given, f) for f in forms), "/".join(forms))


@dataclass(frozen=True)
class NoArticleStored:
    pass


@dataclass(frozen=True)
class TryAgain:
    pos: str
    first_letter: str
    length: int


@dataclass(frozen=True)
class MeaningGraded:
    rating: Rating
    word: Literal["right", "slip", "other_case_word", "wrong", "empty"]
    article: Literal["right", "wrong", "missing", "not_asked"]
    repeated_article: bool
    second_try: bool
    expected: str


MeaningCheck = NoArticleStored | TryAgain | MeaningGraded


def _parse(content: dict[str, Any], given: str) -> tuple[str, str]:
    """The typed article (lower-cased, or "") and the word that remains."""
    words = given.split()
    pos = content["pos"]
    if pos in ("noun", "name") and len(words) >= 2 and words[0].casefold() in RECOGNISED_ARTICLES:
        return words[0].casefold(), " ".join(words[1:])
    if pos == "verb" and len(words) >= 2 and words[0] == "sich":
        if not content["lemma"].startswith("sich "):
            return "", " ".join(words[1:])
    return "", " ".join(words)


def _article_state(
    content: dict[str, Any], article: str
) -> Literal["right", "wrong", "missing", "not_asked"]:
    gender = content["gender"]
    if content["pos"] != "noun" or not gender:
        return "not_asked"
    if not article:
        return "missing"
    return "right" if article in {ARTICLES[g] for g in gender} else "wrong"


def _had_wrong_article(content: dict[str, Any], previous: str | None) -> bool:
    if not previous:
        return False
    article, word = _parse(content, previous.rsplit(" | ", 1)[-1])
    if not answer_matches(word, content["lemma"]):
        return False
    return _article_state(content, article) in ("wrong", "missing")


def _expected(content: dict[str, Any]) -> str:
    gender = content["gender"]
    if content["pos"] != "noun" or not gender:
        return str(content["lemma"])
    return f"{'/'.join(ARTICLES[g] for g in gender)} {content['lemma']}"


def check_meaning(
    content: dict[str, Any], given: str, first_try: str | None, previous: str | None
) -> MeaningCheck:
    """Rules 1-3 and the article of design 5.1; the slip and known-word rules are issue 024."""
    second_try = first_try is not None
    expected = _expected(content)

    def graded(
        rating: Rating,
        word: Literal["right", "wrong", "empty"],
        article: Literal["right", "wrong", "missing", "not_asked"] = "not_asked",
        repeated: bool = False,
    ) -> MeaningGraded:
        if second_try and rating == Rating.Good:
            rating = Rating.Hard
        return MeaningGraded(rating, word, article, repeated, second_try, expected)

    if not given.strip():
        return graded(Rating.Again, "empty")
    article, word = _parse(content, given)
    if content["pos"] == "noun" and not content["gender"] and article:
        return NoArticleStored()
    if normalise_answer(word) != normalise_answer(content["lemma"]):
        return graded(Rating.Again, "wrong")
    state = _article_state(content, article)
    if state in ("right", "not_asked"):
        return graded(Rating.Good, "right", state)
    repeated = _had_wrong_article(content, previous)
    return graded(Rating.Again if repeated else Rating.Hard, "right", state, repeated)
