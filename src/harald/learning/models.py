from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

CARD_TYPES = (
    "meaning_de_en",
    "meaning_en_de",
    "meaning_de_de",
    "article",
    "stammformen",
    "conjugation",
    "phrase_en_de",
)


class Base(DeclarativeBase):
    pass


class Word(Base):
    __tablename__ = "word"
    __table_args__ = (UniqueConstraint("lemma", "pos", "discriminator"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lemma: Mapped[str] = mapped_column(Text)
    pos: Mapped[str] = mapped_column(Text)
    discriminator: Mapped[str] = mapped_column(Text)  # the hint key, §8.2
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Phrase(Base):
    __tablename__ = "phrase"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    en: Mapped[str] = mapped_column(Text)
    de: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text, server_default="")
    tatoeba_de_id: Mapped[int | None] = mapped_column(Integer)
    tatoeba_en_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Card(Base):
    __tablename__ = "card"
    __table_args__ = (
        CheckConstraint(
            "card_type IN (" + ",".join(f"'{t}'" for t in CARD_TYPES) + ")",
            name="card_type_valid",
        ),
        CheckConstraint("link_state IN ('linked','unlinked')", name="link_state_valid"),
        CheckConstraint("(word_id IS NULL) <> (phrase_id IS NULL)", name="card_owner"),
        Index(
            "card_due",
            "due",
            sqlite_where=text("deleted_at IS NULL AND suspended = 0"),
        ),
        Index("card_word", "word_id"),
        Index("card_phrase", "phrase_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word_id: Mapped[int | None] = mapped_column(ForeignKey("word.id"))
    phrase_id: Mapped[int | None] = mapped_column(ForeignKey("phrase.id"))
    card_type: Mapped[str] = mapped_column(Text)
    content: Mapped[dict[str, Any]] = mapped_column(JSON)  # the card's own copy, §7.2
    created_at: Mapped[datetime] = mapped_column(DateTime)
    suspended: Mapped[int] = mapped_column(Integer, server_default="0")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    fsrs_state: Mapped[int] = mapped_column(Integer)
    fsrs_step: Mapped[int | None] = mapped_column(Integer)
    stability: Mapped[float | None] = mapped_column(Float)
    difficulty: Mapped[float | None] = mapped_column(Float)
    due: Mapped[datetime] = mapped_column(DateTime)
    last_review: Mapped[datetime | None] = mapped_column(DateTime)  # NULL means new
    link_state: Mapped[str] = mapped_column(Text, server_default="linked")
    check_ack: Mapped[str | None] = mapped_column(Text)


class Review(Base):
    __tablename__ = "review"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 4", name="rating_valid"),
        Index("review_card", "card_id", "reviewed_at"),
        Index("review_time", "reviewed_at"),
        Index("review_session", "session_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("card.id"))
    session_id: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime)
    rating: Mapped[int] = mapped_column(Integer)
    scope: Mapped[str] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    answer: Mapped[str | None] = mapped_column(Text)  # typed answer, for checked cards
    state_before: Mapped[str] = mapped_column(Text)  # fsrs Card.to_dict() JSON
    state_after: Mapped[str] = mapped_column(Text)


class Deck(Base):
    __tablename__ = "deck"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class DeckMember(Base):
    __tablename__ = "deck_member"
    __table_args__ = (
        CheckConstraint("(word_id IS NULL) <> (phrase_id IS NULL)", name="deck_member_owner"),
        # two partial indexes, not UNIQUE(deck_id, word_id, phrase_id): SQLite treats NULLs as
        # distinct in UNIQUE constraints, so the single constraint would never fire
        Index(
            "deck_member_word",
            "deck_id",
            "word_id",
            unique=True,
            sqlite_where=text("word_id IS NOT NULL"),
        ),
        Index(
            "deck_member_phrase",
            "deck_id",
            "phrase_id",
            unique=True,
            sqlite_where=text("phrase_id IS NOT NULL"),
        ),
    )

    deck_id: Mapped[int] = mapped_column(ForeignKey("deck.id", ondelete="CASCADE"))
    word_id: Mapped[int | None] = mapped_column(ForeignKey("word.id"))
    phrase_id: Mapped[int | None] = mapped_column(ForeignKey("phrase.id"))

    # §7.1 gives the table no primary key; the mapper needs an identity, and this one is mapper-only
    __mapper_args__ = {"primary_key": [deck_id, word_id, phrase_id]}


class FsrsParams(Base):
    __tablename__ = "fsrs_params"

    scope: Mapped[str] = mapped_column(Text, primary_key=True)
    parameters: Mapped[str] = mapped_column(Text)
    desired_retention: Mapped[float] = mapped_column(Float)


class OperationGroup(Base):
    __tablename__ = "operation_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("operation_groups.id"))
    entity_type: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(Text)
    field: Mapped[str | None] = mapped_column(Text)  # changed attribute names
    state: Mapped[str | None] = mapped_column(Text)  # JSON of the old values
