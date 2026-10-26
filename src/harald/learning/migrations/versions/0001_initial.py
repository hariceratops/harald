"""initial

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deck",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "fsrs_params",
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("parameters", sa.Text(), nullable=False),
        sa.Column("desired_retention", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("scope"),
    )
    op.create_table(
        "operation_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "phrase",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("en", sa.Text(), nullable=False),
        sa.Column("de", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), server_default="", nullable=False),
        sa.Column("tatoeba_de_id", sa.Integer(), nullable=True),
        sa.Column("tatoeba_en_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "word",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lemma", sa.Text(), nullable=False),
        sa.Column("pos", sa.Text(), nullable=False),
        sa.Column("discriminator", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lemma", "pos", "discriminator"),
    )
    op.create_table(
        "card",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=True),
        sa.Column("phrase_id", sa.Integer(), nullable=True),
        sa.Column("card_type", sa.Text(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("suspended", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("fsrs_state", sa.Integer(), nullable=False),
        sa.Column("fsrs_step", sa.Integer(), nullable=True),
        sa.Column("stability", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("due", sa.DateTime(), nullable=False),
        sa.Column("last_review", sa.DateTime(), nullable=True),
        sa.Column("link_state", sa.Text(), server_default="linked", nullable=False),
        sa.Column("check_ack", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "card_type IN ('meaning_de_en','meaning_en_de','meaning_de_de','article','stammformen','conjugation','phrase_en_de')",  # noqa: E501
            name="card_type_valid",
        ),
        sa.CheckConstraint("link_state IN ('linked','unlinked')", name="link_state_valid"),
        sa.CheckConstraint("(word_id IS NULL) <> (phrase_id IS NULL)", name="card_owner"),
        sa.ForeignKeyConstraint(
            ["phrase_id"],
            ["phrase.id"],
        ),
        sa.ForeignKeyConstraint(
            ["word_id"],
            ["word.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("card", schema=None) as batch_op:
        batch_op.create_index(
            "card_due",
            ["due"],
            unique=False,
            sqlite_where=sa.text("deleted_at IS NULL AND suspended = 0"),
        )
        batch_op.create_index("card_phrase", ["phrase_id"], unique=False)
        batch_op.create_index("card_word", ["word_id"], unique=False)

    op.create_table(
        "deck_member",
        sa.Column("deck_id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=True),
        sa.Column("phrase_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("(word_id IS NULL) <> (phrase_id IS NULL)", name="deck_member_owner"),
        sa.ForeignKeyConstraint(["deck_id"], ["deck.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["phrase_id"],
            ["phrase.id"],
        ),
        sa.ForeignKeyConstraint(
            ["word_id"],
            ["word.id"],
        ),
    )
    with op.batch_alter_table("deck_member", schema=None) as batch_op:
        batch_op.create_index(
            "deck_member_phrase",
            ["deck_id", "phrase_id"],
            unique=True,
            sqlite_where=sa.text("phrase_id IS NOT NULL"),
        )
        batch_op.create_index(
            "deck_member_word",
            ["deck_id", "word_id"],
            unique=True,
            sqlite_where=sa.text("word_id IS NOT NULL"),
        )

    op.create_table(
        "operations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("field", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["operation_groups.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "review",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("state_before", sa.Text(), nullable=False),
        sa.Column("state_after", sa.Text(), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 4", name="rating_valid"),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["card.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("review", schema=None) as batch_op:
        batch_op.create_index("review_card", ["card_id", "reviewed_at"], unique=False)
        batch_op.create_index("review_session", ["session_id"], unique=False)
        batch_op.create_index("review_time", ["reviewed_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("review", schema=None) as batch_op:
        batch_op.drop_index("review_time")
        batch_op.drop_index("review_session")
        batch_op.drop_index("review_card")

    op.drop_table("review")
    op.drop_table("operations")
    with op.batch_alter_table("deck_member", schema=None) as batch_op:
        batch_op.drop_index("deck_member_word", sqlite_where=sa.text("word_id IS NOT NULL"))
        batch_op.drop_index("deck_member_phrase", sqlite_where=sa.text("phrase_id IS NOT NULL"))

    op.drop_table("deck_member")
    with op.batch_alter_table("card", schema=None) as batch_op:
        batch_op.drop_index("card_word")
        batch_op.drop_index("card_phrase")
        batch_op.drop_index(
            "card_due", sqlite_where=sa.text("deleted_at IS NULL AND suspended = 0")
        )

    op.drop_table("card")
    op.drop_table("word")
    op.drop_table("phrase")
    op.drop_table("operation_groups")
    op.drop_table("fsrs_params")
    op.drop_table("deck")
