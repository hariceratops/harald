from dataclasses import dataclass

EN_FILENAME = "raw-wiktextract-data.jsonl.gz"
DE_FILENAME = "de-extract.jsonl.gz"


@dataclass(frozen=True)
class Source:
    name: str
    title: str
    licence: str
    attribution: str


@dataclass(frozen=True)
class SourceFile:
    filename: str
    url: str
    source: str


_WIKTIONARY_ATTRIBUTION = "Wiktionary contributors, extracted by wiktextract (kaikki.org)"
_TATOEBA_EXPORTS = "https://downloads.tatoeba.org/exports/per_language"

# Tatoeba's "CC BY 2.0 FR" is the precise version it publishes; the spec abbreviates it to CC-BY.
SOURCES = (
    Source("wiktionary-en", "Wiktionary (en)", "CC BY-SA 4.0", _WIKTIONARY_ATTRIBUTION),
    Source("wiktionary-de", "Wiktionary (de)", "CC BY-SA 4.0", _WIKTIONARY_ATTRIBUTION),
    Source("tatoeba", "Tatoeba", "CC BY 2.0 FR", "Tatoeba contributors (tatoeba.org)"),
)

SOURCE_FILES = (
    SourceFile(
        EN_FILENAME, "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz", "wiktionary-en"
    ),
    SourceFile(
        DE_FILENAME,
        "https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz",
        "wiktionary-de",
    ),
    SourceFile("deu_sentences.tsv.bz2", f"{_TATOEBA_EXPORTS}/deu/deu_sentences.tsv.bz2", "tatoeba"),
    SourceFile("eng_sentences.tsv.bz2", f"{_TATOEBA_EXPORTS}/eng/eng_sentences.tsv.bz2", "tatoeba"),
    SourceFile("deu-eng_links.tsv.bz2", f"{_TATOEBA_EXPORTS}/deu/deu-eng_links.tsv.bz2", "tatoeba"),
)
