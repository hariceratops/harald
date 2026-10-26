from dataclasses import dataclass

ARTICLES = {"m": "der", "f": "die", "n": "das"}


@dataclass(frozen=True)
class ArticleCheck:
    correct: bool
    accepted: tuple[str, ...]


def check_article(gender: str, chosen: str) -> ArticleCheck:
    """Any of the word's genders is correct (Band, See, Leiter)."""
    accepted = tuple(ARTICLES[g] for g in gender if g in ARTICLES)
    return ArticleCheck(chosen in accepted, accepted)
