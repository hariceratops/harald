import json
from typing import Any

from harald.build.records import DeEntryRecord, DeExampleRecord, DeSenseRecord
from harald.build.wiktextract_en import GENDER_TAGS, LABELS, SKIPPED_POS
from harald.core.option import Option

_ARTICLES = {"m": "der", "f": "die", "n": "das"}


def parse_line(line: bytes) -> Option[DeEntryRecord]:
    """Raises json.JSONDecodeError on a bad line; the caller counts those.

    Only definitions and examples are read from the German edition; the one other field is
    the display label.
    """
    rec = json.loads(line)
    if rec.get("lang_code") != "de" or rec.get("pos") in SKIPPED_POS:
        return Option.none()
    raw_senses = rec.get("senses") or []
    if not raw_senses or all(_is_form_of(s) for s in raw_senses):
        return Option.none()
    senses = tuple(_sense(s) for s in raw_senses if s.get("glosses"))
    if not senses:
        return Option.none()
    return Option.some(DeEntryRecord(rec["word"], rec["pos"], _label(rec), senses))


def _is_form_of(sense: dict[str, Any]) -> bool:
    return bool(sense.get("form_of")) or "form-of" in sense.get("tags", ())


def _sense(sense: dict[str, Any]) -> DeSenseRecord:
    labels = tuple(dict.fromkeys(t for t in sense.get("tags", ()) if t in LABELS))
    examples = tuple(
        DeExampleRecord(ex["text"], ex.get("ref") or None)
        for ex in sense.get("examples") or ()
        if ex.get("text")
    )
    return DeSenseRecord(
        sense.get("sense_index") or None, " ".join(sense["glosses"]), labels, examples
    )


def _label(rec: dict[str, Any]) -> str:
    if rec["pos"] != "noun":
        return str(rec["word"])
    genders = [GENDER_TAGS[t] for t in rec.get("tags", ()) if t in GENDER_TAGS]
    articles = "/".join(_ARTICLES[g] for g in "mfn" if g in genders)
    return f"{articles} {rec['word']}" if articles else str(rec["word"])
