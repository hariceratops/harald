import json
import re
from typing import Any

from harald.build.forms import parse_forms
from harald.build.records import EntryRecord, ExampleRecord, FormOfRecord, SenseRecord

SKIPPED_POS = {"character", "symbol", "punct"}
GENDER_TAGS = {"masculine": "m", "feminine": "f", "neuter": "n"}
# the importer maps wiktextract tags to Harald's label vocabulary, so the runtime never sees
# wiktextract's; a tag outside this set is not shown
LABELS = frozenset({
    "colloquial", "informal", "formal", "slang", "vulgar", "derogatory", "offensive",
    "humorous", "euphemistic", "archaic", "obsolete", "dated", "rare", "poetic", "literary",
    "figuratively", "idiomatic", "regional", "dialectal", "nonstandard", "childish",
    "Austria", "Switzerland", "Southern-Germany", "Northern-Germany", "Central-Germany",
    "transitive", "intransitive", "reflexive", "impersonal",
})  # fmt: skip
_VARIANT_TAGS = {
    "formal", "rare", "nonstandard", "figuratively", "poetic",
    "error-unknown-tag", "error-unrecognized-form",
}  # fmt: skip


def parse_line(line: bytes) -> EntryRecord | FormOfRecord | None:
    """Raises json.JSONDecodeError on a bad line; the caller counts those."""
    rec = json.loads(line)
    if rec.get("lang_code") != "de" or rec.get("pos") in SKIPPED_POS:
        return None
    senses = rec.get("senses") or []
    if not senses:
        return None
    if all(_is_form_of(s) for s in senses):
        return _form_of(rec, senses)
    glossed = [s for s in senses if s.get("glosses")]
    if not glossed:
        return None
    lemma = rec["word"]
    is_noun = rec["pos"] in ("noun", "name")
    parsed = parse_forms(lemma, rec["pos"], rec.get("forms") or [])
    return EntryRecord(
        lemma=lemma,
        pos=rec["pos"],
        gender=_gender(rec, senses) if is_noun else "",
        plural=_plural(rec) if is_noun else None,
        ipa=_ipa(rec),
        senses=tuple(_sense(s) for s in glossed),
        translated_senses=sum(_has_translated_example(s) for s in glossed),
        separable_prefix=_separable_prefix(rec) if rec["pos"] == "verb" else None,
        verb_forms=parsed.verb_forms,
        index_forms=parsed.index_forms,
        unmapped=parsed.unmapped,
    )


def _sense(sense: dict[str, Any]) -> SenseRecord:
    labels = tuple(dict.fromkeys(t for t in sense.get("tags", ()) if t in LABELS))
    examples = tuple(
        ExampleRecord(
            ex["text"],
            ex.get("translation") or ex.get("english") or None,
            ex.get("type", "example"),
            ex.get("ref") or None,
        )
        for ex in sense.get("examples") or ()
        if ex.get("text")
    )
    return SenseRecord(sense["glosses"][-1], labels, examples)


def _ipa(rec: dict[str, Any]) -> str | None:
    found = [s["ipa"] for s in rec.get("sounds") or () if s.get("ipa")]
    phonemic = [i for i in found if i.startswith("/")]
    best: str | None = (phonemic or found or [None])[0]
    return best


def _has_translated_example(sense: dict[str, Any]) -> bool:
    return any(ex.get("translation") or ex.get("english") for ex in sense.get("examples") or ())


def _form_of(rec: dict[str, Any], senses: list[dict[str, Any]]) -> FormOfRecord | None:
    for sense in senses:
        for target in sense.get("form_of") or ():
            return FormOfRecord(rec["word"], target["word"], rec["pos"])
    return None


def _separable_prefix(rec: dict[str, Any]) -> str | None:
    templates = rec.get("head_templates") or []
    arg = str((templates[0].get("args") or {}).get("1", "")) if templates else ""
    match = re.match(r"([^.<]+)\.", arg)
    return match.group(1) if match else None


def _is_form_of(sense: dict[str, Any]) -> bool:
    return bool(sense.get("form_of")) or "form-of" in sense.get("tags", ())


def _gender(rec: dict[str, Any], senses: list[dict[str, Any]]) -> str:
    found = {GENDER_TAGS[t] for s in senses for t in s.get("tags", ()) if t in GENDER_TAGS}
    if not found:
        templates = rec.get("head_templates") or []
        expansion: str = templates[0].get("expansion", "") if templates else ""
        before_paren = expansion.removeprefix(rec["word"]).split("(")[0]
        found = set(re.findall(r"\b[mfn]\b", before_paren))
    return "".join(g for g in "mfn" if g in found)


def _plural(rec: dict[str, Any]) -> str | None:
    head_rows = [f for f in rec.get("forms") or [] if "source" not in f]
    exact = [f["form"] for f in head_rows if set(f.get("tags", ())) == {"plural"}]
    if exact:
        return str(exact[0])
    variant = [
        f["form"]
        for f in head_rows
        if "plural" in f.get("tags", ()) and set(f["tags"]) - {"plural"} <= _VARIANT_TAGS
    ]
    return str(variant[0]) if variant else None
