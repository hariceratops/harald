from sqlalchemy import ForeignKey, Index
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
