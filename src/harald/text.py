import unicodedata

_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue"})


def fold(s: str) -> str:
    return unicodedata.normalize("NFC", s).casefold().translate(_UMLAUTS)
