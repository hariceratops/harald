import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from fsrs import Rating

from harald.lexicon.fuzzy import osa_within
from harald.lexicon.model import PERSONS, KnownWord
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


Known = Callable[[str], tuple[KnownWord, ...]]
_Word = Literal["right", "slip", "other_case_word", "other_word", "wrong"]


def _had_wrong_article(content: dict[str, Any], previous: str | None, known: Known) -> bool:
    if not previous:
        return False
    article, word = _parse(content, previous.rsplit(" | ", 1)[-1])
    if _judge_word(content, word, known) not in ("right", "slip"):
        return False
    return _article_state(content, article) in ("wrong", "missing")


def _expected(content: dict[str, Any]) -> str:
    gender = content["gender"]
    if content["pos"] != "noun" or not gender:
        return str(content["lemma"])
    return f"{'/'.join(ARTICLES[g] for g in gender)} {content['lemma']}"


def _allowance(lemma: str) -> int:
    length = len(unicodedata.normalize("NFC", lemma))
    return 0 if length <= 4 else 1 if length <= 9 else 2


def _judge_word(content: dict[str, Any], word: str, known: Known) -> _Word:
    # `other_word` is the retry candidate (design 5.1 rule 6)
    lemma = content["lemma"]
    typed, wanted = normalise_answer(word), normalise_answer(lemma)
    if typed == wanted:
        return "right"
    if typed.casefold() == wanted.casefold():
        lemmas = (k.lemma for k in known(word) if not k.inflected)
        if any(normalise_answer(k) == typed for k in lemmas):
            return "other_case_word"
        return "slip"
    found = known(word)
    if any(k.pos == content["pos"] and not answer_matches(k.lemma, lemma) for k in found):
        return "other_word"
    if found:
        return "wrong"
    if osa_within(typed, wanted, _allowance(lemma)).is_some:
        return "slip"
    return "wrong"


def check_meaning(
    content: dict[str, Any],
    given: str,
    first_try: str | None,
    previous: str | None,
    known: Known,
) -> MeaningCheck:
    second_try = first_try is not None
    expected = _expected(content)

    def graded(
        rating: Rating,
        word: Literal["right", "slip", "other_case_word", "wrong", "empty"],
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
    verdict = _judge_word(content, word, known)
    if verdict == "other_word":
        if second_try:
            return graded(Rating.Again, "wrong")
        lemma = unicodedata.normalize("NFC", content["lemma"])
        return TryAgain(content["pos"], lemma[0], len(lemma))
    if verdict in ("other_case_word", "wrong"):
        return graded(Rating.Again, verdict)
    state = _article_state(content, article)
    if state in ("right", "not_asked"):
        return graded(Rating.Good, verdict, state)
    repeated = _had_wrong_article(content, previous, known)
    return graded(Rating.Again if repeated else Rating.Hard, verdict, state, repeated)
