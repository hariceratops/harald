import unicodedata

_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue"})


def fold(s: str) -> str:
    return unicodedata.normalize("NFC", s).casefold().translate(_UMLAUTS)


_TO_DIGRAPHS = str.maketrans(
    {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}
)


def answer_matches(given: str, expected: str) -> bool:
    def normal(s: str) -> str:
        return " ".join(unicodedata.normalize("NFC", s).split()).translate(_TO_DIGRAPHS)

    return normal(given) == normal(expected)
