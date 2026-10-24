from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Meta(Base):
    __tablename__ = "meta"
    __table_args__ = {"sqlite_with_rowid": False}

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]


class Headword(Base):
    __tablename__ = "headword"
    __table_args__ = (Index("headword_lemma_pos", "lemma", "pos", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lemma: Mapped[str]
    pos: Mapped[str]
    richness: Mapped[int]

    entries: Mapped[list["Entry"]] = relationship(lazy="raise", order_by="Entry.ord")


class Entry(Base):
    __tablename__ = "entry"
    __table_args__ = (Index("entry_headword_ord", "headword_id", "ord"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    headword_id: Mapped[int] = mapped_column(ForeignKey("headword.id"))
    ord: Mapped[int]
    gender: Mapped[str]
    plural: Mapped[str | None]
    ipa: Mapped[str | None]
    separable_prefix: Mapped[str | None]

    senses: Mapped[list["Sense"]] = relationship(lazy="raise", order_by="Sense.ord")
    verb_forms: Mapped[list["VerbForm"]] = relationship(lazy="raise", order_by="VerbForm.ord")


class Sense(Base):
    __tablename__ = "sense"
    __table_args__ = (Index("sense_entry_ord", "entry_id", "ord"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entry.id"))
    ord: Mapped[int]
    gloss: Mapped[str]
    labels: Mapped[str]  # JSON array of register and valency labels

    examples: Mapped[list["Example"]] = relationship(lazy="raise", order_by="Example.ord")


class Example(Base):
    __tablename__ = "example"
    __table_args__ = (
        Index("example_sense_ord", "sense_id", "ord"),
        CheckConstraint("kind IN ('example','quotation')"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sense_id: Mapped[int] = mapped_column(ForeignKey("sense.id"))
    ord: Mapped[int]
    text: Mapped[str]
    translation: Mapped[str | None]
    kind: Mapped[str]
    ref: Mapped[str | None]


class SearchKey(Base):
    __tablename__ = "search_key"
    __table_args__ = (Index("search_key_lang_key", "lang", "key", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lang: Mapped[str]
    key: Mapped[str]


class KeyHeadword(Base):
    __tablename__ = "key_headword"
    __table_args__ = {"sqlite_with_rowid": False}

    key_id: Mapped[int] = mapped_column(primary_key=True)
    headword_id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[int]  # 0 lemma, 1 inflected form


class FuzzyDelete(Base):
    __tablename__ = "fuzzy_delete"
    __table_args__ = {"sqlite_with_rowid": False}

    d: Mapped[str] = mapped_column(primary_key=True)
    key_id: Mapped[int] = mapped_column(primary_key=True)


class VerbForm(Base):
    __tablename__ = "verb_form"
    __table_args__ = {"sqlite_with_rowid": False}

    entry_id: Mapped[int] = mapped_column(ForeignKey("entry.id"), primary_key=True)
    slot: Mapped[str] = mapped_column(primary_key=True)
    ord: Mapped[int] = mapped_column(primary_key=True)
    form: Mapped[str]
    variant: Mapped[str]


class UnmappedTagset(Base):
    __tablename__ = "unmapped_tagset"
    __table_args__ = {"sqlite_with_rowid": False}

    pos: Mapped[str] = mapped_column(primary_key=True)
    tagset: Mapped[str] = mapped_column(primary_key=True)
    occurrences: Mapped[int]
    example_word: Mapped[str]
    example_form: Mapped[str]


class Source(Base):
    __tablename__ = "source"
    __table_args__ = {"sqlite_with_rowid": False}

    name: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    licence: Mapped[str]
    attribution: Mapped[str]


class SourceFile(Base):
    __tablename__ = "source_file"
    __table_args__ = {"sqlite_with_rowid": False}

    filename: Mapped[str] = mapped_column(primary_key=True)
    source: Mapped[str]
    source_date: Mapped[str]
    sha256: Mapped[str]


class BuildStat(Base):
    __tablename__ = "build_stat"
    __table_args__ = {"sqlite_with_rowid": False}

    metric: Mapped[str] = mapped_column(primary_key=True)
    numerator: Mapped[int]
    denominator: Mapped[int | None]
