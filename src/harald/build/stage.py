# Shard stage tables carry (seq, local ids) and natural keys; the writer resolves them to
# final ids by rule. Plain DDL text, so workers never import the SQLAlchemy models.
SHARD_DDL = """
CREATE TABLE entry_stage (
    seq INTEGER, local_id INTEGER, lemma TEXT, pos TEXT, gender TEXT, plural TEXT,
    separable_prefix TEXT
);
CREATE TABLE sense_stage (
    seq INTEGER, local_id INTEGER, entry_local INTEGER, ord INTEGER, gloss TEXT
);
CREATE TABLE verb_form_stage (
    seq INTEGER, entry_local INTEGER, slot TEXT, ord INTEGER, form TEXT, variant TEXT
);
CREATE TABLE key_stage (seq INTEGER, key TEXT, lemma TEXT, pos TEXT, kind INTEGER);
CREATE TABLE fuzzy_stage (d TEXT, key_id INTEGER);
"""

# Staging-file-only tables, dropped by finalize so VACUUM INTO never sees them.
WRITER_DDL = """
CREATE TABLE offset_stage (seq INTEGER PRIMARY KEY, entry_off INTEGER, sense_off INTEGER);
CREATE TABLE hw_stage (lemma TEXT, pos TEXT);
CREATE TABLE keyall_stage (key TEXT, headword_id INTEGER, kind INTEGER);
"""

WRITER_TABLES = ("offset_stage", "hw_stage", "keyall_stage")
