# Harald v1: design

Spec: `dev/specs/harald-v1.md` (frozen). Issues: `dev/issues/001`–`022`.
Background read: `dev/inbox/harald-data-and-modes.md`. `german_learning_app_design.md`
is superseded, and only its rejected ideas matter here (see §14.8).

**Names used here.** The databases are `lexicon.db` (Wiktionary entries, the
search indexes and the Tatoeba pairs; formerly `dictionary.db`) and
`learning.db` (cards, phrases, decks and the review log; formerly
`user.db`). Their packages are `harald/lexicon/` and `harald/learning/`. The
frozen spec, the issues and AGENTS.md still use the old names; §16 lists
where, for the user to update.

This document settles how v1 is built: module boundaries, both database
schemas, the build pipeline, lookup and search algorithms, the study loop, and
why each choice beat its alternatives. Where the spec leaves a question open,
the design says whether it is **blocked** (no answer is invented) or takes a
**provisional default** that the user can overturn cheaply. §16 collects
everything that needs the user's decision.

---

## 0. Verified facts this design rests on

These were checked against live data and package sources on 2026-10-18, not
assumed. The implementer can rely on them, and test fixtures should be cut
from the same records.

**kaikki / wiktextract, English edition** (`https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz`,
2.98 GB, `Last-Modified` and `ETag` headers present):
- One JSON object per line, serialised with `", "` / `": "` separators, so the
  bytes `"lang_code": "de"` appear verbatim. Some lines are redirect records
  (`{"title", "redirect", "pos"}`) with no `lang_code`.
- German verb `forms` come in two groups. Rows without `source` come from the
  head template: `läuft [present, singular, third-person]`, `lief [past]`,
  `gelaufen [participle, past]`, `sein [auxiliary]`. Rows with
  `source: "conjugation"` come from the full table, with tense tags
  `present`, `preterite`, `subjunctive-i`, `subjunctive-ii`, `perfect`,
  `pluperfect`, `future-i`, `future-ii`, `imperative`, plus
  `multiword-construction` on compound tenses (`ist gelaufen`), and
  `subordinate-clause` on separable verbs' dependent forms (`anrufe`).
- Separable verbs give main-clause forms already split: `ruft an`, `rief an`,
  with `angerufen` as the participle.
- Bookkeeping rows: `table-tags`, `inflection-template`, `class` (their `form`
  is not a word). Duplicate rows occur (`auxiliary` appears up to 4 times).
  Variant markers ride on real forms: `formal`, `rare` (on Konjunktiv II
  `riefe an`), `nonstandard`, `figuratively`, `poetic`. `error-unknown-tag`
  and `error-unrecognized-form` mark rows wiktextract could not fully tag.
- **There is no separate Sie row**, and the imperative has only 2sg (`lauf`,
  `laufe`) and 2pl (`lauft`). `formal` in this data is a register marker, not
  the Sie person. This matters for open question 5.
- Gender appears in every noun sense's `tags` (`masculine` / `feminine` /
  `neuter`) and in the head template (`de-noun`, arg `1` = `m,es:s,e`).
  Plural: head-template row tagged exactly `[plural]`, with variants carrying
  extra tags (`Hünde [error-unknown-tag, plural]`).
- Band has three English-edition noun entries (n `Bänder`, m `Bände`,
  f `Bands`), **two of which share `etymology_number` 1**. Gender plus plural
  is what tells them apart.
- Inflected forms also exist as their own entries (`lief`, a verb whose only
  sense has `form_of: [{word: laufen}]` and tag `form-of`): about 20% of
  German entries in a 40 MB sample.
- English entries carry German translations at the **entry level**
  (`translations[]` with `lang_code: "de"` and a `sense` string such as
  `"employ, apply"`), not per sense. In the sample, 3,950 English entries had
  German translations and none had them per sense.
- Examples: `{text, translation | english, type: example | quotation, ref?,
  bold_text_offsets}`.

**kaikki, German edition** (`https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz`,
309 MB. The spec's filename is right, but it lives under `/dictionary/downloads/de/`,
not `/dewiktionary/`):
- About 1.0M `lang_code == "de"` records, of which about two thirds are
  form-of pages (`senses[].form_of`). Content entries have `pos` names that
  match the English edition (`noun`, `verb`, `adj`), entry-level gender in
  `tags`, and senses with `sense_index` (`"1"`, `"1a"`).
- Some senses have no `sense_index` and are headings (`Plural »Bänder«:`).
- Examples are `{text, ref?}` and untranslated. Band has 4 German-edition
  noun entries, matching the spec.
- Streaming and fully parsing the whole file took 81 s on the desktop.

**Tatoeba** per-language exports (`downloads.tatoeba.org/exports/per_language/`):
`deu/deu_sentences.tsv.bz2` (12 MB), `eng/eng_sentences.tsv.bz2` (25 MB) and
`deu/deu-eng_links.tsv.bz2` (3.5 MB, 585,892 links). That gives 585,745 usable
pairs. Formats are `id\tlang\ttext` and `deu_id\teng_id`.

**fsrs 6.3.2** (pure Python, MIT): `Scheduler(parameters=DEFAULT_PARAMETERS,
desired_retention=0.9, learning_steps=(1m,10m), relearning_steps=(10m,),
enable_fuzzing=True)`. `review_card(card, rating, review_datetime: UTC-aware,
review_duration: ms) -> (Card, ReviewLog)`. `Card(card_id, state, step,
stability, difficulty, due, last_review)` has `to_dict`/`from_dict`.
`Optimizer` is lazily imported and needs torch, which is irrelevant to v1.

**Textual 8.2.8**: `App.suspend()` is a context manager that hands the
terminal to a child process (`with self.suspend(): subprocess.run(...)`) and
raises `SuspendNotSupported` only on Textual Web.

**Termux**: `libsqlite` 3.54.1 is built with `--enable-fts5`. rapidfuzz ships
no wheel Termux's bionic Python can install (only manylinux, musllinux, macOS
and Windows), so on the phone it would need a C++ build from source.

**Measurements** (desktop, 979k folded German keys; the phone is assumed to be
about 3–5× slower):

| Candidate generation for fuzzy lookup | Size | Query time |
|---|---|---|
| FTS5 trigram, OR of query trigrams, bm25 | 21 MB | 45–1,553 ms |
| Plain trigram table, count ranking | 177 MB | 28–376 ms |
| Symmetric delete, distance 1, full key | 313 MB | <0.5 ms, misses multi-edit |
| **Symmetric delete, first 7 chars only** | **130 MB** | **0.2–15 ms** |
| rapidfuzz over all keys in memory | – | 790 ms load + 190–280 ms |

Reranking with a pure-Python banded OSA (Damerau) distance at k ≤ 2 took
0.4–52 ms per query, worst case on a `verschl…` compound with 3,311
candidates.

| Phrase search on 585k pairs (FTS5, porter) | Time |
|---|---|
| `"repeats itself"` (phrase) / `repeats itself` (AND) | 0.7 / 0.2 ms, 9 hits, top = "History repeats itself." |
| OR over all words of "and the pattern then repeats itself" | 429 ms, 151,890 hits |
| OR over only the uncommon words (`pattern OR repeats OR itself`) | 2.5 ms, same top hit |

**Added with the Alembic, Result and parallel-build revisions** (checked
2026-10-18):
- **SQLAlchemy 2.1.5** publishes a pure-Python wheel (`py3-none-any`), and
  greenlet is only in its `asyncio` extra. **SQLAlchemy 2.0.x** (kohle pins
  2.0.46) still requires greenlet on `aarch64`, which has no wheel Termux can
  use. Harald therefore requires `SQLAlchemy>=2.1`.
- **Alembic 1.20 and Mako 1.4** ship pure-Python wheels. **MarkupSafe 3.0.4**,
  Mako's dependency, has no pure wheel, but its sdist's `setup.py` retries
  without the C speedups when compiling fails, so on Termux it installs as
  plain Python if there is no compiler.
- Alembic imports Mako as soon as `alembic` is imported (through
  `alembic.util.pyfiles`). It accepts `package:dir` script locations through
  `importlib.resources`, but its source notes there are no tests for that path.
- **`VACUUM INTO` output is canonical.** Three builds with identical content
  (explicit ids, FTS built in one fixed step) but different row orders and
  table interleavings gave three different files before `VACUUM INTO` and one
  byte-identical file after it, on SQLite 3.45.
- **The real English dump** (2.98 GB, 2026-10-03) decompresses to 25.6 GB of
  JSON in 10.9M lines. The byte prefilter keeps 459,333 lines (2.0 GB), which
  yield 92,651 German content entries. Build-stage timings on the desktop (4
  cores, WSL2, 15 GB RAM) are in §3.7. The English edition gives 448,346
  distinct folded keys, which make 3.47M fuzzy-delete rows (60 MB), far fewer
  than the 2M keys first assumed.
- **Runtime cost of SQLAlchemy.** Measured with SQLAlchemy 2.0.46 from kohle's
  venv, run read-only: installing 2.1 here was not permitted, and the two
  import alike. The C extensions were on, then off, which emulates Termux's
  pure-Python install.
  - Fresh-interpreter medians over a 21 ms Python baseline: `sqlite3` with
    open and query +6 ms; `rich` +59 ms; SQLAlchemy Core with engine and query
    +186 ms; SQLAlchemy ORM with a declarative model and a session query
    +241 ms; `alembic.command` +278–296 ms; `textual.app` +172–179 ms. Turning
    the C extensions off made no difference to import time.
  - Per query, on a synthetic lexicon-shaped database (442k keys, 3.4M
    delete rows, FTS5 over 300k rows):

    | Query | sqlite3 | Core | ORM |
    |---|---|---|---|
    | fuzzy candidates | 57 µs | 116–124 µs | – |
    | FTS5 `MATCH … LIMIT 50` | 1.35 ms | 1.41–1.43 ms | – |
    | 3,000-row read | 1.2 ms | 2.1 ms (3.2 ms without C extensions) | – |
    | headword load (33 rows) | 63 µs | 236 µs | 1.3 ms (selectin relationships) |
  - The phone is assumed to be 3–5× slower than the desktop. That factor is an
    estimate for issue 009 to measure.
- **ORM for both databases, measured after the user's decision.** Same
  interpreter, C extensions off. These runs came in a slower machine state:
  the bare-Python baseline measured 51 ms here against 21 ms earlier on the
  same desktop.
  - **Cold lookup-shaped flow** (fuzzy candidates plus one headword load,
    with `rich` imported; medians of 9): `sqlite3` 205 ms, Core `text()`
    571 ms, ORM with 19 read-only mapped classes 827 ms.
  - **In-process breakdown of the ORM flow:** `rich` 117–140 ms; importing
    `sqlalchemy.orm` 361–407 ms; defining 19 mapped classes 42–44 ms;
    `configure_mappers` 22–24 ms; engine plus first fuzzy query (compiling
    the statement) 21–22 ms; first headword load with `selectinload`
    (compiling) 35–50 ms; both repeated from SQLAlchemy's statement cache
    3.6–5 ms.
  - **ORM grade transaction** (card update plus review insert, WAL,
    `synchronous=FULL`, commit per grade): median 6.4 ms, p90 7.7 ms.
  - **3,000 rows:** ORM entities 37 ms; a column select through the session
    11 ms.
  - **Machine-state drift** between sessions is about 2×, so benchmark
    comparisons must be normalised (§14.9).
- **Audited grade** (kohle-style `OperationGroup` plus two `Operation` rows,
  one carrying the before-state; WAL, `synchronous=FULL`): median 8.2–8.5 ms,
  against 7.5–8.0 ms without the audit rows, in two runs. That is +0.2–0.9
  ms, with the same single fsync.
- **Proper nouns (`pos == name`), measured on the 2026-10-03 dumps:**
  - **Entries:** 10,004 in the English edition (11,470 senses, 709 examples,
    20.4 MB of JSON lines) and 17,711 in the German edition (20,418 senses,
    39,274 examples, 56.3 MB). Against 92,651 and 180,551 content entries,
    that is about 10% of entries. The 40 MB sample's "a quarter" was skewed.
  - **A lexicon-shaped build without and with names** (entries, senses,
    examples, search keys, fuzzy rows): 203.3 MB → 214.9 MB vacuumed
    (+11.6 MB, +5.7%). Headwords grow by 22,367, search keys by 26,287
    (+4.8%), fuzzy rows by 196,107 (+4.6%). Parsing costs about 1.1 s more,
    and write time shows no measurable change (14.3 s → 13.7 s, noise).
  - **Precision.** Of 29,520 random single-edit typos of the 3,000 richest
    common lemmas, 5.88% already spell another common word exactly. Only
    0.38% spell a proper-noun-only key exactly, the one case where a name
    would rank first. Fuzzy candidate sets grow 2% (90.7 → 92.5 per query),
    still 0.05 ms per query.

**Added with the click revision** (checked 2026-10-20 in kohle's venv, click
8.3.1 on Python 3.12; nothing was installed into Harald's):
- **click 8.3.1 is a pure-Python wheel** (`py3-none-any`). Its only
  dependency is `colorama`, and only on Windows, so it passes the phone rule
  of §2.
- **Import cost.** `python -X importtime` puts `click` at 10.5 ms cumulative
  when `rich.console`, `rich.table` and `sqlalchemy.orm` are already loaded,
  which is the one-shot `lookup` situation. On its own it costs 32–39 ms,
  because it pulls in `enum`, `gettext`, `shutil`, `locale` and `uuid`,
  which `rich` and SQLAlchemy load anyway. The bare-Python baseline was
  45 ms in this session, the slower machine state.
- **Wall clock** (fresh `-I` processes, interleaved): importing the lookup
  set with click instead of argparse moved the median from 628 to 640 ms
  (N = 15), and from 612 to 638 ms (N = 30). Both differences sit inside the
  run's own p10–p90 spread of about 70 ms.
- **Behaviour §11.1 relies on**, read in click 8.3.1's `Command.main` and
  checked with a probe script:
  - with `standalone_mode=False`, `main` returns the command's return value,
    returns the code of an `Exit` (so `--help` gives 0), and re-raises
    `ClickException` and `Abort`;
  - `KeyboardInterrupt` and `EOFError` become `Abort` in both modes. In
    standalone mode that prints "Aborted!" and exits 1;
  - a group called with no subcommand raises `NoArgsIsHelpError`, a
    `UsageError` (exit 2). Unknown commands and missing arguments are
    `UsageError`s too;
  - the group callback runs **before** the subcommand parses its arguments,
    so it also runs for `harald lookup --help`;
  - an `envvar` whose value is the empty string counts as unset, which is
    how `HARALD_CONFIG` is treated today;
  - `click.edit` starts the editor through `subprocess.Popen(...,
    shell=True)` and reports failure by raising `ClickException`.

**Added with the Option revision** (checked 2026-10-24 in Harald's venv,
Python 3.12; nothing was written to the project):
- **Per-call cost** of returning a value and checking it, with `timeit`
  (best of 5):

  | Shape | Some | none |
  |---|---|---|
  | `T \| None` | 0.17 µs | 0.15 µs |
  | kohle's `Option` (frozen dataclass, `object()` sentinel) | 0.82 µs | 0.77 µs |
  | frozen, slotted, `none()` returning one instance | 0.68 µs | 0.31 µs |

  A frozen, slotted variant with a `bool` flag and a single `none` instance
  measured 0.67 µs for Some and 0.07 µs for `none` in a leaner harness. So
  the flag costs nothing over the sentinel, and an `Option.some` costs about
  0.5 µs more than returning the value.
- **The hot call sites, for scale:**
  - `parse_line` took about 104 µs per line on the fixture's 14 parseable
    lines. Real kept lines average about 280 µs (128 s of parse CPU over
    459,333 lines, §3.7).
  - `_table_slot` took 2.6 µs per call.
  - `osa_within` averaged 63 µs over five test pairs, one of them 16
    characters long. §0's rerank figure (52 ms over 3,311 candidates) puts
    the real average nearer 16 µs.
- **Pickling.** kohle's `object()` sentinel loses its identity in a pickle
  round trip: an unpickled `none()` reads as Some. A `bool` flag survives
  it.
- **Typing.** mypy's optional `truthy-bool` error code passes on today's
  code unchanged (33 files in `src`, 54 with `tests`). A prototype of the
  §14.10 shape, with a typed `ok_or` returning Harald's `Result`, passes
  `mypy --strict`.

---

## 1. Shape of the solution

```
desktop                                              phone (Termux)
  sources/ (kept downloads) ──► harald build ──► staging/ ──atomic rename──►
  <synced>/lexicon.db ═══ Syncthing send-only ═══► <received>/lexicon.db (read-only)
                                                     ~/.local/share/harald/learning.db (only writer)
  <backup>/ ◄══ Syncthing send-only ══════════════ <backup>/learning-*.db (VACUUM INTO)
```

- One Python package, `harald`, with a `src/` layout, installed with uv and
  the console script `harald`.
- **The importer** (`harald.build`) is the only code that reads source files.
  Everything else reads `lexicon.db` through `harald.lexicon`. It runs
  as a task graph: worker processes parse sources into shard files, and one
  writer merges them, with byte-deterministic output (§3.5, §3.7).
- `harald.lexicon.schema` is the contract between the two: DDL,
  `SCHEMA_VERSION`, and the vocabularies both sides interpret (slot names,
  folding rules, the fuzzy key algorithm).
- `learning.db` is owned by `harald.learning`. Cards are self-contained copies. The
  link back to the lexicon is a re-resolvable hint, never a row id. It is
  accessed through SQLAlchemy with kohle's infrastructure (declarative models,
  `UnitOfWork`/`DbTransaction`, `DbTransactionContext`, and its audit trail,
  §7.8), in mirrored module paths so a later lift into a shared package stays
  cheap (§7.7, informational). Its schema
  evolves through Alembic revisions shipped inside the package (§7.6).
- `lexicon.db` is read through the SQLAlchemy ORM as well: one data-access
  style, the user's choice. It sits behind the `lexicon/` package
  interface, so callers never see a `Session` (§4.4). The startup cost is
  watched by a benchmark harness with explicit budgets and a per-path Core
  fallback (§14.9). The build, desktop-only, is the one place that writes
  through stdlib `sqlite3`, and its schema still comes from the same table
  definitions (§3.5).
- Operations that can fail return `Result[T, E]` with `Exception` subclasses
  as error values. Only six named seams turn arbitrary exceptions into `Err`
  (§14.2). A value that may be absent is an `Option[T]` wherever a public
  function or a use case returns it (§14.10).
- The CLI (click) and the TUI are thin front-ends over the same use cases
  (`harald.use_cases`, §11.2). This is kohle's layering: front-ends call use
  cases, use cases compose the per-database packages (`lexicon/`,
  `learning/`, `build/`), and only those packages touch a session, a
  connection or a file. Both front-ends display lookups through one concrete
  Rich rendering (`harald.render`). That is not a Renderer abstraction: Rich
  is Textual's own rendering type, so there is nothing to swap.

---

## 2. Package layout

```
pyproject.toml          name = "harald", scripts: harald = "harald.cli:main",
                        deps: textual>=8.2,<9 ; fsrs>=6.3,<7 ; rich>=14 ;
                              alembic>=1.18 ; SQLAlchemy>=2.1,<2.2 ; click>=8.3,<9
                        (nothing else at runtime;
                        rich comes with textual, declared because render.py imports it;
                        SQLAlchemy is pinned to 2.1+ because 2.0 pulls greenlet on aarch64, §0)
alembic.ini             dev only, not in the wheel: script_location = src/harald/learning/migrations
src/harald/
  __init__.py
  __main__.py           python -m harald
  cli.py                click group; each command loads config, opens handles, calls one
                        use case and renders; use-case modules imported lazily (§11.1)
  config.py             Config dataclass, XDG paths, TOML loading
  text.py               fold(), answer_matches(), tokenize(): shared normalisation
  render.py             model dataclasses -> Rich renderables (CLI and TUI)
  editor.py             $EDITOR key/value template loop (phrase entry, card edit)
  core/result.py        Result[T, E] (mirrors kohle/core/result.py; shared candidate, §7.7)
  core/option.py        Option[T] (mirrors kohle/core/option.py; typed, picklable flag; §14.10)
  db/connection.py      make_engine(path, pragmas), make_session_factory(engine), PRAGMA
                        connect hook (mirrors kohle/db/connection.py, as a factory; §7.7)
  infrastructure/       mirrors kohle/infrastructure/, including its audit trail (§7.8)
    crud.py             crud_create / crud_update / crud_delete / crud_retrieve (kohle's)
    infra_errors.py     InfrastructureError, UniqueViolation, check_if_unique_constraint_failed
    transaction_context.py   DbTransactionContext: run(op), record_transaction_step()
    uow.py              DbTransaction.execute(use_case), UnitOfWork[T, E]
  use_cases/            what front-ends call (§11.2); one module per area; __init__ empty;
                        every use case a class, called as X(handles).execute(values)
    lexicon.py          LookUpGerman, QueryLexiconInfo; later LookUpEnglish, LoadHeadword,
                        FindPhrases
    build.py            BuildLexicon: the build, then the info report; BuildDone
    cards.py            PlanWordCards; CreateWordCards, SavePhrase, EditCard, SetSuspended,
                        DeleteCard (UnitOfWork subclasses; all from issue 010)
    study.py            NextCard, Grade, SessionSummary
    decks.py            CreateDeck, DeleteDeck, SetDeckMembership
    check.py            the check listing and its three repairs (§8)
    backup.py           BackUp
  build/                IMPORTER: the only package that reads source files
    errors.py           BuildError family (§14.2)
    graph.py            task graph, process pool, job wrapper run_job (§3.7)
    sources.py          registry: name, url, filename, licence, attribution
    fetch.py            --fetch: conditional GET, .part + sidecar, atomic replace
    records.py          plain dataclasses produced by parse jobs
    forms.py            wiktextract tag sets -> slots; unmapped-tagset tally
    reader.py           gzip source -> decompress thread -> block scan -> 4 MB chunks
    wiktextract_en.py   en.parse job: German entries + English->German translations
    wiktextract_de.py   de.parse job: definitions + examples
    tatoeba.py          tatoeba.parse job, tatoeba.lemmas
    writer.py           merge nodes: ATTACH shards, id offsets, keys, FTS, finalize, VACUUM
    publish.py          fingerprint, lock, byte compare, atomic replace
    run.py              build(config, fetch, force) -> Result[BuildReport, BuildError]
  lexicon/              runtime, read-only access to lexicon.db
    schema.py           SCHEMA_VERSION, slot vocabulary
    models.py           Base(DeclarativeBase) + read-only mapped classes (lazy="raise") + FTS5 DDL
                        on Base.metadata: THE lexicon schema; package-private (§4.4)
    errors.py           LexiconError family
    db.py               open_lexicon(path) -> Result[Lexicon, LexiconError];
                        Lexicon = read-only engine + session factory
    model.py            public result dataclasses: Headword, Entry, Sense, Example, ...
    fuzzy.py            fuzzy_deletes(key), osa_within(a, b, k)   (also used by build)
    lookup.py           lookup_de(), lookup_en(), load_headword()
    phrases.py          search_phrases(), de_lemma_tokens()     (also used by build)
  learning/             learning.db
    errors.py           LearningDbError family
    models.py           Base(DeclarativeBase): Word, Phrase, Card, Review, Deck, DeckMember, FsrsParams
    db.py               open_learning_db(path) -> Result[LearningDb, LearningDbError]; learning.db PRAGMAs;
                        deleted-card global criteria
    migrate.py          HEAD revision constant; fast-path check; programmatic upgrade (§7.6)
    migrations/         Alembic script directory, shipped in the package
      env.py            online only; target_metadata = Base.metadata; connection from attributes
      script.py.mako    template for `alembic revision` (dev only)
      versions/0001_initial.py    reviewed autogenerate output for the models
    content.py          per-card-type content dataclasses (JSON in card.content)
    cards.py            card services: *_service(ctx, …) over DbTransactionContext (§7.7)
    answers.py          check_article(), check_stammformen(): pure
    study.py            study services; FSRS scopes
    decks.py            deck services
    check.py            re-resolution for `harald check` (§8.1)
    backup.py           VACUUM INTO a temp file, rename, prune (§10)
  tui/
    app.py              HaraldApp; holds Lexicon + LearningDb opened by cli;
                        screens call use_cases/ (§11.2)
    home.py lookup.py entry.py add_word.py study.py phrases.py cards.py decks.py info.py
    harald.tcss
tests/                  (layers settled by the tdd step)
dev/bench/              benchmark harness: bench.py, queries.toml, budgets.toml and the two
                        baselines committed; results/ gitignored (§14.9)
```

`main.py` is deleted. pyproject's `name = "german"` becomes `harald`. The
build backend is uv's default (`uv_build`). Dev tools go in a
`[dependency-groups] dev` group.

**Phone-side dependencies must be pure Python, or build as plain Python when
no compiler is present.** This is a design constraint, not a preference:
Termux's Python cannot use manylinux wheels, so every compiled-only dependency
becomes a C/C++ build on the phone. It is the reason rapidfuzz is not used
(§14.6). The current set (§0): textual and its tree, fsrs, SQLAlchemy 2.1
(pure wheel; greenlet only in the `asyncio` extra; the runtime ORM for
both databases, where the pure-Python build cost nothing measurable at
Harald's query sizes), Alembic, Mako and click (pure wheels), and MarkupSafe, which has no pure wheel but whose source build falls
back to plain Python when its C speedups can't compile. A new phone-side
dependency must be checked against this rule before it is added.

---

## 3. `lexicon.db`

### 3.1 Schema (`harald/lexicon/models.py`; version in `schema.py`)

```sql
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
  -- 'schema_version' only. No build time and no Harald version: see §3.5.
CREATE TABLE source (name TEXT PRIMARY KEY, title TEXT NOT NULL,
  licence TEXT NOT NULL, attribution TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE source_file (filename TEXT PRIMARY KEY, source TEXT NOT NULL,
  source_date TEXT NOT NULL, sha256 TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE build_stat (metric TEXT PRIMARY KEY, numerator INTEGER NOT NULL,
  denominator INTEGER) WITHOUT ROWID;         -- coverage.*, bad_lines.*
CREATE TABLE unmapped_tagset (pos TEXT NOT NULL, tagset TEXT NOT NULL,
  occurrences INTEGER NOT NULL, example_word TEXT NOT NULL, example_form TEXT NOT NULL,
  PRIMARY KEY (pos, tagset)) WITHOUT ROWID;

CREATE TABLE headword (id INTEGER PRIMARY KEY, lemma TEXT NOT NULL, pos TEXT NOT NULL,
  richness INTEGER NOT NULL, UNIQUE (lemma, pos));   -- one row per (word, pos), either edition

CREATE TABLE entry (id INTEGER PRIMARY KEY,           -- English edition, content entries only
  headword_id INTEGER NOT NULL, ord INTEGER NOT NULL,
  gender TEXT NOT NULL,          -- '' or a subset of 'mfn' in that order, e.g. 'mn'
  plural TEXT, genitive TEXT, ipa TEXT,
  discriminator TEXT NOT NULL,   -- hint-key part, §8.2
  separable_prefix TEXT);        -- verbs: 'an' for an.rufen, else NULL (§3.3)
CREATE TABLE sense (id INTEGER PRIMARY KEY, entry_id INTEGER NOT NULL, ord INTEGER NOT NULL,
  gloss TEXT NOT NULL, context TEXT, labels TEXT NOT NULL /*JSON array*/, qualifier TEXT);
CREATE TABLE example (id INTEGER PRIMARY KEY, sense_id INTEGER NOT NULL, ord INTEGER NOT NULL,
  text TEXT NOT NULL, translation TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('example','quotation')), ref TEXT);
CREATE TABLE verb_form (entry_id INTEGER NOT NULL, slot TEXT NOT NULL, ord INTEGER NOT NULL,
  form TEXT NOT NULL, variant TEXT NOT NULL, PRIMARY KEY (entry_id, slot, ord)) WITHOUT ROWID;

CREATE TABLE de_entry (id INTEGER PRIMARY KEY, headword_id INTEGER NOT NULL,
  ord INTEGER NOT NULL, label TEXT NOT NULL);        -- display label, e.g. 'das Band'
CREATE TABLE de_sense (id INTEGER PRIMARY KEY, de_entry_id INTEGER NOT NULL, ord INTEGER NOT NULL,
  sense_index TEXT /*NULL = heading*/, gloss TEXT NOT NULL, labels TEXT NOT NULL);
CREATE TABLE de_example (id INTEGER PRIMARY KEY, de_sense_id INTEGER NOT NULL,
  ord INTEGER NOT NULL, text TEXT NOT NULL, ref TEXT);

CREATE TABLE en_word (id INTEGER PRIMARY KEY, word TEXT NOT NULL, pos TEXT NOT NULL, ord INTEGER NOT NULL);
CREATE TABLE en_translation (en_word_id INTEGER NOT NULL, ord INTEGER NOT NULL,
  sense TEXT NOT NULL, german TEXT NOT NULL, gender TEXT NOT NULL, note TEXT,
  PRIMARY KEY (en_word_id, ord)) WITHOUT ROWID;

CREATE TABLE search_key (id INTEGER PRIMARY KEY, lang TEXT NOT NULL CHECK (lang IN ('de','en')),
  key TEXT NOT NULL, UNIQUE (lang, key));
CREATE TABLE key_headword (key_id INTEGER NOT NULL, headword_id INTEGER NOT NULL,
  kind INTEGER NOT NULL /*0 lemma, 1 inflected form*/, PRIMARY KEY (key_id, headword_id)) WITHOUT ROWID;
CREATE TABLE key_en_word (key_id INTEGER NOT NULL, en_word_id INTEGER NOT NULL,
  PRIMARY KEY (key_id, en_word_id)) WITHOUT ROWID;
CREATE TABLE fuzzy_delete (d TEXT NOT NULL, key_id INTEGER NOT NULL,
  PRIMARY KEY (d, key_id)) WITHOUT ROWID;

CREATE TABLE tatoeba_pair (id INTEGER PRIMARY KEY, de_id INTEGER NOT NULL, en_id INTEGER NOT NULL,
  de TEXT NOT NULL, en TEXT NOT NULL, UNIQUE (de_id, en_id));
CREATE VIRTUAL TABLE tatoeba_en_fts USING fts5(en, content='tatoeba_pair', content_rowid='id',
  tokenize='porter unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE tatoeba_de_fts USING fts5(lemmas, content='',
  tokenize='unicode61 remove_diacritics 0');
CREATE TABLE phrase_common_token (lang TEXT NOT NULL, token TEXT NOT NULL,
  PRIMARY KEY (lang, token)) WITHOUT ROWID;
```

Secondary indexes (`entry(headword_id, ord)`, `sense(entry_id, ord)`,
`example(sense_id, ord)`, `de_entry(headword_id, ord)`,
`de_sense(de_entry_id, ord)`, `de_example(de_sense_id, ord)`) are created
after the bulk load.

**The `headword` table exists because of a spec requirement.** German-edition
definitions must be grouped once per (word, pos) across all entries. Lookup
results are grouped the same way: Band (noun) is one result containing three
English entries and one German block. English entries, German entries and
search keys all hang off `headword`.

**Defined once.** The DDL above is what `lexicon/models.py` produces: the
declarative models, their `Index` objects in `__table_args__`, and the FTS5
statements attached as `DDL` to `Base.metadata` (§4.4).
- The build creates the staging file with `Base.metadata.create_all`, which
  emits the FTS5 DDL through the metadata's `after_create` hook (§3.5).
- The runtime reads through the same classes.
- The build's shard stage tables are derived from the same models (§3.5),
  so no column list is written twice.
- **Drift check:** build the fixture lexicon, then run
  `alembic.autogenerate.compare_metadata` against `Base.metadata`, excluding
  the FTS5 virtual and shadow tables; it must report nothing. Since
  `create_all` makes the tables, this catches the build altering the schema
  on its own, such as an extra index or column changed in `finalize`, or
  stage tables leaking into the output.

**`SCHEMA_VERSION`** (an integer) covers everything both sides interpret: the
table definitions, `fold()`, `fuzzy_deletes()`, the slot vocabulary, the label vocabulary,
and `de_lemma_tokens()`. Changing any of them means bumping the version,
because a mismatched pair returns wrong answers silently rather than failing.

### 3.2 Slot vocabulary (Harald's own, written by the importer, read by runtime)

| wiktextract tags (after removing variant markers) | slot |
|---|---|
| head row `present singular third-person` / `past` / `participle past` / `auxiliary` | `pp.pres3sg` / `pp.pret` / `pp.part2` / `pp.aux` |
| `indicative present` | `ind.pres.<p>` |
| `indicative preterite` | `ind.pret.<p>` |
| `indicative perfect multiword-construction` | `ind.perf.<p>` |
| `indicative pluperfect …` | `ind.plup.<p>` |
| `indicative future future-i …` / `future-ii` | `ind.fut1.<p>` / `ind.fut2.<p>` |
| `subjunctive subjunctive-i` (no perfect or future) | `subj1.pres.<p>` |
| `subjunctive perfect …` | `subj1.perf.<p>` |
| `subjunctive-i future-i` / `future-ii` | `subj1.fut1.<p>` / `subj1.fut2.<p>` |
| `subjunctive subjunctive-ii` (no future) | `subj2.pret.<p>` |
| `subjunctive pluperfect …` | `subj2.plup.<p>` |
| `subjunctive-ii future-i` / `future-ii` | `subj2.fut1.<p>` / `subj2.fut2.<p>` |
| `imperative` | `imp.2sg` / `imp.2pl` |
| `infinitive` / `infinitive infinitive-zu` / `participle present` / `participle past` / `auxiliary` | `inf` / `inf.zu` / `part1` / `part2` / `aux` |
| `infinitive future future-i/-ii multiword-construction` | `inf.fut1` / `inf.fut2` |

`<p>` is one of `1sg 2sg 3sg 1pl 2pl 3pl`. A `subordinate-clause` tag adds a
`.sub` suffix. `variant` holds the variant-marker tags in sorted order, or
`''`. Rows with the same slot keep their source order in `ord`, and the first
row with `variant == ''` is the primary form.

### 3.3 Importer rules (`harald/build/`)

**Streaming.** Nothing is ever decompressed to disk. Each gzip source is
decompressed in a thread and scanned in blocks for the bytes
`b'"lang_code": "de"'`. Only matching lines are cut into chunks for the parse
jobs (§3.7). On the English edition that keeps German entries and English
entries holding German translations: 459,333 of 10.9M lines, or 2.0 GB of
25.6 GB (§0). After parsing, only records with `lang_code` `de` or `en` are
kept.
Lines that fail to decode are counted (`build_stat` `bad_lines.<source>`), not
fatal.

**Guard against format drift.** If the byte prefilter stops matching (say, the
serialisation changes), the build would quietly publish a near-empty
lexicon straight to the phone. So the build refuses to publish when it
finds fewer than `build_min_entries` German English-edition entries. That is a
config key defaulting to 50,000 (the 2026-10-03 dump has 92,651); tests set it
to 0.

**What becomes an entry.**
- English edition, `lang_code == "de"`. Skip form-of entries (every sense has
  `form_of` or the `form-of` tag). Their `word → form_of.word` pairs feed the
  search index as inflected forms instead.
- Skip `pos` in `{character, symbol, punct}`.
- **Proper nouns (`pos == "name"`) are imported**, by the user's decision, so
  that lookups of Deutschland, Berlin, Rhein and Müller work.
  - **Cost, measured (§0):** 10,004 English-edition and 17,711
    German-edition entries (about 10%), +11.6 MB (+5.7%), about 1 s more
    parsing.
  - **Kept quiet by ranking and labelling** (§4.1), not by exclusion. They
    stay in the fuzzy index because measurement showed no real harm: only
    0.38% of single-edit typos spell a name exactly, and candidate sets grow
    2%.
  - **Cards:** meaning cards only (German → English, English → German, and
    German → German when the German edition defines the name). The article
    and Stammformen rules apply to `noun` and `verb`, so they never trigger.
- German edition, `lang_code == "de"`: the same form-of and pos rules.

**Per English-edition entry:**
- **Gender**: ordered union of `masculine`/`feminine`/`neuter` across sense
  tags. If that is empty, fall back to the `m`/`f`/`n` tokens after the lemma
  in `head_templates[0].expansion` (`"Band n (strong, …"`). Stored as a subset
  of `mfn`.
- **Plural**: the first head-template row (no `source`) whose tags are exactly
  `{plural}`. If there is none, the first such row with variant markers.
  Otherwise `NULL`. The genitive follows the same rule with `{genitive}`.
- **IPA**: the first `sounds[].ipa` starting with `/` (phonemic), else the
  first `ipa`.
- **Senses**: `gloss` = the last element of `glosses`. Earlier elements (the
  parent gloss of a nested sense) go into `context`. `labels` = sense tags
  mapped through `REGISTER_LABELS` (`colloquial`, `informal`, `formal`,
  `slang`, `vulgar`, `derogatory`, `offensive`, `humorous`, `euphemistic`,
  `archaic`, `obsolete`, `dated`, `rare`, `poetic`, `literary`, `figuratively`,
  `idiomatic`, `regional`, `dialectal`, `nonstandard`, `childish`, regional
  tags such as `Austria`, `Switzerland`, `Southern-Germany`) plus
  `transitive`/`intransitive`/`reflexive`/`impersonal`. `qualifier` =
  `raw_tags` joined with `", "` (`of a fluid`). The importer maps tags to
  labels, so the runtime never sees wiktextract vocabulary.
- **Examples**: `text` stored verbatim (quotations keep their typos, and no
  whitespace or Unicode normalisation is applied), `translation` from
  `translation` or else `english`, `kind` from `type` (default `example`),
  plus `ref`.
- **Forms** (`forms.py`):
  - Bookkeeping rows (`table-tags`, `inflection-template`, `class`) are
    dropped.
  - Derivational rows are dropped: `diminutive`, a bare gender counterpart
    (`Hündin [feminine]`), `alternative`, `abbreviation`, `canonical`. These
    are separate words with their own entries, not inflections.
  - Every other row's surface form goes into the search index, as long as it
    is a single token, or is a separable split form like `ruft an` (contains a
    space, has no `multiword-construction`). Strip a trailing `!`.
  - Verb rows also go through the slot table. Noun and adjective declension
    rows are index-only, since declension display is a non-goal.
- **Unmapped tag sets.** A row is recorded in `unmapped_tagset` (sorted tag
  set, count, first example word and form) when it contains a tag outside
  `KNOWN_TAGS`, carries an `error-*` tag, or is a verb row whose known tags
  fit no slot. `KNOWN_TAGS` is the union of the slot tags, variant markers,
  bookkeeping tags, derivational tags and declension tags (cases, numbers,
  `definite`/`indefinite`, `strong`/`weak`/`mixed`, `with-article`,
  `includes-article`, `without-article`, `predicative`, `comparative`,
  `superlative`, genders). Recorded rows are still indexed. They just never
  fill a display slot.
- **Principal parts**: head rows first. If one is missing, fall back to the
  primary `ind.pres.3sg`, `ind.pret.3sg`, `part2` and `aux` table slots.
- **Separable prefix** (verbs): taken from the head template's first
  argument, where a dot marks the separable prefix: `an.rufen<rief,gerufen>`
  gives `an` (seen in the anrufen record, §0). If there is no dot it is
  `NULL`. Inseparable homographs such as umfahren (drive around) have no dot,
  and their separable twins (`um.fahren`) do, so the two entries differ here
  as well as in their discriminators.
- **Discriminator** (§8.2): nouns `"<gender>|<plural or ''>"`, verbs the
  primary `pp.part2`, everything else `''`.

**English → German** (from `lang_code == "en"` records): German translations
come from the top-level `translations` and also from `senses[].translations`
(cheap robustness if wiktextract moves them). Keep those with
`lang_code == "de"`. Each one stores `sense` (or `''`), `german` = `word`,
`gender` from `tags`, and `note` = the `english` qualifier. Order is source
order. An `en_word` row is written only if it has at least one German
translation.

**German edition**:
- One `de_entry` per content entry, under the `headword` (lemma, pos).
  `headword` is created if missing: German-edition-only words exist and are
  searchable.
- `label` = article plus lemma for nouns, using entry `tags` gender
  (`das Band`), otherwise the lemma.
- `de_sense` comes from senses in order: `sense_index` as given (`NULL` for
  headings), `gloss` = glosses joined with `" "`, `labels` mapped like the
  English edition.
- `de_example` comes from `examples[]`: `text`, `ref`.
- **Nothing else is read from the German edition.** Gender, plural,
  conjugation and IPA come only from the English edition, as the spec scopes
  the German edition to definitions and examples. The one exception is the
  display label.

**Tatoeba**:
- Read the links first. Load only the German and English sentences they
  reference.
- Pairs are inserted sorted by `(de_id, eng_id)`. Direct links only, with no
  indirect chains through a third language.
- `tatoeba_de_fts.lemmas` = `de_lemma_tokens(de, lemma_of)`, with
  `lemma_of` backed by the staging connection (the
  `tatoeba.lemmas` node, §3.7), cached per
  `de_id`.
- `phrase_common_token`: per language, tokens whose document frequency is
  above 1% of pairs, counted in Python with `text.tokenize()` (English tokens
  lowercased, German tokens as lemma tokens).

**Keys and fuzzy index** (`fuzzy.py`, shared with runtime):
- `fold(s)` = NFC, then `casefold()` (which already turns ß into ss), then
  ä→ae, ö→oe, ü→ue.
- German search keys: folded lemmas from both editions (kind 0) and folded
  index forms (kind 1). Kind 0 wins when a key is both. English search keys:
  folded `en_word.word`.
- `fuzzy_deletes(key)` = `{p} ∪ {p minus one char}` with `p = key[:7]`. Every
  search key gets rows in `fuzzy_delete`.

**Richness** = senses across both editions for the headword. It is the
tie-break proxy for how common a word is, since wiktextract carries no
frequency data.

### 3.4 Coverage (informational, never gates the build)

Written to `build_stat`, printed at the end of the build, and shown by
`harald info`:
- `coverage.stammformen`: verb entries with all four principal parts, out of
  all verb entries.
- `coverage.noun_gender`: noun entries with non-empty gender, out of all noun
  entries.
- `coverage.translated_example`: English-edition senses with at least one
  example that has a translation, out of all senses.
- All three exclude proper nouns, so the figures stay comparable with the
  first report.

### 3.5 Build, publish, determinism (issues 004a and 004b)

`build(config, fetch, force) -> Result[BuildReport, BuildError]`:

1. Take an exclusive `fcntl.flock` on `staging_dir/.lock`. A second
   concurrent build returns `Err(BuildLocked(lock))` at once.
2. Delete leftover `staging_dir/*.db` files (staging and shard files from
   crashed runs). The staging directory belongs to Harald.
3. Check that `staging_dir` and the published path share a filesystem
   (`st_dev`). If not, return `Err(StagingNotSameFilesystem(staging, target))`.
4. If `fetch` is set, run `fetch_all(config.sources_dir)` (§3.6). Files are
   fetched one at a time in `SOURCE_FILES` order. The first failure stops
   the fetch and aborts the build, so nothing is published.
   - **The failed file keeps its previous copy.** Files fetched before it
     in the same run have already been replaced by their new copies, and
     they stay replaced. Files after it are not attempted.
   - An earlier wording said the previous source copies all stay in place.
     `fetch_all` never did that (corrected 2026-10-20).
   - *Why that is acceptable:* each copy is complete and has its own
     sidecar, so a later build records each file's own date. The next
     `--fetch` gets a 304 for the files already current and retries the
     rest.
   - No test pins this yet. One belongs with issue 005's review fixes: two
     `SourceFile`s on the local server, with the second failing, should
     leave the first at its new copy with its sidecar, and the second at
     its previous copy.
5. **Fingerprint** = sha256 over:
   - `SCHEMA_VERSION`;
   - every `.py` file of the installed `harald` package, as sorted
     (relative path, bytes) pairs;
   - the sha256 of each source file, read in full on every build (seconds
     against a build of minutes).
6. **Fast path**: if `staging_dir/last_build.json` holds the same fingerprint
   *and* the sha256 of the published `lexicon.db`, report "unchanged" and
   stop. The file is never opened for writing. `--force` skips this step.
7. **Run the task graph** (§3.7) into `staging_dir/lexicon.<pid>.db`
   (`journal_mode=OFF`, `synchronous=OFF`; atomicity comes from step 10, so
   the staging file needs no journal). It starts by creating the schema with
   `lexicon.models.Base.metadata.create_all(engine)` on a short-lived
   SQLAlchemy engine (the FTS5 virtual tables come from the same call), then
   disposes of that engine. The build is desktop-only, so importing the ORM
   there costs nothing that matters. Worker processes write their own shard
   files beside it, and the main process is the only writer of the staging
   file. The graph ends with the `finalize` node: `meta`,
   `source`, `source_file`, `build_stat` and `unmapped_tagset`, dropping the
   stage tables, the minimum-entries guard, and
   `VACUUM INTO staging_dir/lexicon.final.<pid>.db`. VACUUM INTO writes in
   rollback-journal mode with page size 4096.
8. Delete the shard files and the unvacuumed staging file.
9. **Byte compare** the final staging file with the published file. If they
   are identical, delete the staging file. The published file is untouched,
   with the same mtime and hash.
10. Otherwise `fsync` the staging file, `os.replace()` it onto the published
    path, and `fsync` the directory.
11. Write `last_build.json` (fingerprint, sha256 of the published file)
    atomically (temp file plus replace).

**The build is the one place that writes through stdlib `sqlite3`.**
- **What it does:** workers write shard files, and the main process merges
  with `executemany`, `ATTACH`, `INSERT … SELECT` and `VACUUM INTO`.
- **Why not SQLAlchemy:**
  - it's bulk SQL on the desktop, never on the phone;
  - routing rows through the ORM's unit of work, or even Core's
    statement layer, adds per-row cost exactly where §3.7 measured the
    bottleneck: one writer doing `executemany` already plateaued at 16 s;
  - nothing in it benefits from mapped classes.
- **What keeps the schema defined once:**
  - the output schema comes from `Base.metadata.create_all` (step 7);
  - the drift check (§3.1) guards it;
  - the shard **stage tables** are not a second definition.
    `build/stage.py` derives each one from its model's `__table__` columns,
    adding `stream`, `seq` and `local_id` and swapping foreign-key ids for the
    natural keys the merge resolves.
- **What workers receive:** the derived DDL and the merge's column lists, as
  text. Workers stay plain `sqlite3`, and the main process alone imports the
  models.
- **If index upkeep shows up in issue 004b's per-node timings,** create the
  secondary indexes in `finalize` instead of in `create_all`. Use the same
  `Index` objects from the models, so it is still one definition.

**Failure and interruption.** Any task failure, a worker killed outright
(`BrokenProcessPool`), Ctrl-C, or disk full stops the graph:
- pending tasks are cancelled and the pool is shut down;
- staging and shard files are deleted in `finally`;
- `build` returns `Err` (for Ctrl-C, the `KeyboardInterrupt` propagates after
  cleanup).

The published file can only change in step 10, which is a single rename, so
nothing partial is ever published.

**Staging lives outside the synced folder.** A temp file inside the Syncthing
folder would be synced as a partial file, under a temp name, which breaks
"a partial file never reaches the phone". `os.replace` is only atomic within
one filesystem, hence step 3. It never falls back to copying.

**Rules the implementer must hold for determinism.** The output must be
byte-identical whatever the worker count and whatever order tasks complete
in.
- **Every row gets its final id from a rule, never from completion order:**
  - source order, through per-chunk offsets (§3.7);
  - sorted natural keys, for `headword` and `search_key`;
  - `(de_id, en_id)` order, for Tatoeba pairs.
- **FTS tables are filled by the writer in one fixed step** from complete
  content, then `optimize`d. They are never filled incrementally as results
  arrive.
- **`VACUUM INTO` is the last step.** Measured (§0): identical content
  inserted in three different row orders and table interleavings gives three
  different files before `VACUUM INTO` and one identical file after it. With
  rule 1 holding, how the writer interleaves tables does not reach the output.
- **Aggregates returned by tasks** (unmapped-tagset tallies, coverage
  counters) are merged by key and inserted in sorted order.
- **Never iterate a `set` or `dict` built from strings into an insert or an
  output without sorting first.** Python randomises string hashing per
  process (and now per worker), so an unsorted set produces a different file
  on every run. Example: the `KNOWN_TAGS` check is fine, but writing the
  `unmapped_tagset` rows needs `sorted()`.
- No timestamps, no random numbers, no `ANALYZE`.
- Tag sets are stored sorted and labels in mapping order.
- The same SQLite library across runs. A different SQLite version may change
  bytes. The file is then republished once, which is acceptable.

**Tests that hold these rules:**
- issue 004a (single process): `--force` twice from the same fixtures gives
  byte equality and an unchanged mtime; Ctrl-C leaves the previous file
  intact; a schema mismatch is refused, naming both versions;
- issue 004b (parallel graph):
  - `build_workers = 0` (inline) and `build_workers = 3` give identical
    bytes;
  - a test hook that delays tasks in reverse order gives the same bytes;
  - a task made to fail returns `Err`, leaves no staging or shard file, and
    leaves the published file untouched;
  - per-node timings are printed.

**Why the fingerprint is not stored inside `lexicon.db`.** If it were, any
code change would change the file's bytes even when its content didn't, and
Syncthing would resend 1 GB. The rule is simple: **the file changes if and
only if its content changes**. For the same reason `meta` holds no Harald
version and no build time.

**Version check**, `open_lexicon(path) -> Result[Lexicon,
LexiconError]`:
- Open with `file:<path>?mode=ro&immutable=1` (`&uri=true` in the SQLAlchemy
  URL). That means no locking and no
  `-wal`/`-shm` files, which is safe because the file is replaced by rename
  and never modified in place.
- Read `meta.schema_version`. If it differs from `SCHEMA_VERSION`, return
  `Err(SchemaMismatch(found=…, expected=…, harald_version=…))`. Its message
  reads, for example, "lexicon.db has schema 3, but Harald 0.5.0 needs
  schema 4. Rebuild on the desktop or update Harald." The CLI prints it and
  exits with code 2 before Textual is imported.
- A missing file returns `Err(LexiconMissing(path))`, and a file that
  isn't SQLite returns `Err(NotALexicon(path, detail))`
  (`sqlalchemy.exc.DatabaseError`, caught by type).
- It opens through `make_engine(path, read_only=True)`, and reads the version
  with the ORM (§4.4).

An open `immutable` connection on the phone keeps reading the old inode when
Syncthing renames a new file over it. The new file is picked up at the next
start.

### 3.6 Fetch (issue 005)

- `sources.py` lists five files under three sources:
  - `raw-wiktextract-data.jsonl.gz` (wiktionary-en);
  - `de-extract.jsonl.gz` (wiktionary-de);
  - `deu_sentences.tsv.bz2`, `eng_sentences.tsv.bz2` and
    `deu-eng_links.tsv.bz2` (tatoeba).
- Each download uses `urllib.request` with `If-None-Match`/`If-Modified-Since`
  taken from the sidecar. A 304 means "already current" and nothing is
  downloaded.
- **The conditional headers are sent only if the sidecar can be read and
  the data file's size equals the sidecar's `size`** (decided in issue
  005). Each header is added only if the sidecar recorded a value for it
  (`etag`, `last_modified`). Every other case gets an unconditional
  download: no sidecar, an unreadable or malformed one, a missing data
  file, or a size mismatch.
  - *Why size and not sha256:* checking the hash would read the whole
    file on every fetch, 2.98 GB for the English dump (§0), and §3.5
    step 5 reads it again for the fingerprint straight afterwards. The
    size check costs one `stat`.
  - *What it gives up:* a file altered without changing its size still
    gets a conditional request, and a 304 leaves the altered copy in
    place. The build still catches it: step 5's sha256 no longer matches
    the sidecar, so the date becomes `unknown` and the build warns.
    Deleting the data file or its sidecar forces a full download on the
    next `--fetch`.
- The response is streamed to `<file>.part`, hashing as it goes. Then the
  sidecar `<file>.meta.json` (`url`, `etag`, `last_modified`, `sha256`,
  `size`) is written to `.part`, followed by `os.replace` of the data file and
  then of the sidecar. Only the most recent copy exists.
- Any exception during one file's download deletes its `.part` file and
  returns `Err(FetchFailed(file, detail))`. This is one of the broad-catch
  seams (§14.2): network failures arrive as many unrelated exception types
  (`URLError`, `HTTPError`, `TimeoutError`, `ssl.SSLError`,
  `http.client.IncompleteRead`, `OSError`), and the one thing that matters is
  that the previous copy survives.
- **`fetch_all(sources_dir, files=SOURCE_FILES)`** takes the directory and
  an optional sequence of `SourceFile`s, instead of reading `Config` and
  the registry itself (decided in issue 005). The build passes only
  `config.sources_dir`. Tests pass a temporary directory and a
  `SourceFile` whose URL points at a stdlib `http.server` on `127.0.0.1`.
  The download, the 304, a truncated body and the `.part` cleanup all run
  without the network. The cost: those tests never touch the real URLs in
  `SOURCE_FILES` (issue 005's review, 2026-10-20).
- The source date is the `Last-Modified` date (`YYYY-MM-DD`) from the sidecar,
  used only if the sidecar's sha256 matches the file. Otherwise it is
  `unknown` and the build warns. File mtimes are never used, because they
  would make the build nondeterministic.
- **One date per source**, which `harald info` and the Info screens show,
  is the **newest trusted date** among that source's `source_file` rows.
  - It is `unknown` only when none of the source's files has a trusted
    date. That includes a source none of whose files the build has used
    yet: Wiktionary (de) and Tatoeba until issues 007 and 018.
  - `load_info` has computed it this way since issue 005. This section
    didn't state the rule until 2026-10-20.
  - *What it hides:* a source whose files disagree shows only its newest
    date. That happens when one file's date is `unknown`, which the build
    warns about file by file. It also happens after a fetch that failed
    partway (§3.5 step 4), which can leave a new `deu_sentences.tsv.bz2`
    beside an older `deu-eng_links.tsv.bz2`, for example. The per-file
    truth stays in `source_file`.
  - *Why newest:* it answers the question `info` is read for, which is
    whether the last fetch and build picked up the new dumps. An untrusted
    file is already reported by the build's per-file warning.
  - *Alternatives:* `unknown` whenever any file is untrusted, or the oldest
    date. Each is a one-line change in `load_info`. The user kept newest
    (2026-10-24, §16).
  - A component test pins the rule (§11.3).
- **`UNKNOWN_DATE` is part of the contract between the build and the
  runtime**, so it belongs in `lexicon/schema.py` next to `SCHEMA_VERSION`.
  `build/fetch.py` and `lexicon/info.py` import it from there. Issue 005's
  review found it defined in both of them.
- Before issue 005 lands, issue 001 relies on the user placing the English
  dump in `sources_dir` by hand, so its date shows as `unknown`.

Attribution as displayed:
- Wiktionary: "Wiktionary contributors, extracted by wiktextract (kaikki.org)",
  CC BY-SA 4.0.
- Tatoeba: "Tatoeba contributors (tatoeba.org)", CC BY 2.0 FR. The spec says
  "CC-BY"; 2.0 FR is the precise version Tatoeba publishes.

**Sources are listed in name order** (decided in issue 005): tatoeba,
wiktionary-de, wiktionary-en, shown as Tatoeba, Wiktionary (de), Wiktionary
(en). `load_info` reads them with `ORDER BY source.name`.
- *Why:* the order is fixed by the query. It does not depend on the order
  of `SOURCES` in `sources.py`, which is also the order `finalize` inserts
  the rows. Without an `ORDER BY`, SQLite promises no order at all.
- The Info wireframes (§12.3, §12.8) follow this order.

Harald never uploads the built database anywhere.

### 3.7 Build task graph (issue 004b onwards)

The user has asked for a parallel build: populating `lexicon.db` is a
graph of tasks with explicit dependencies, and unrelated tables populate in
parallel with multiprocessing. This section designs it around SQLite's single
writer, and keeps every guarantee of §3.5.

**Shape: workers parse and write shards, one writer merges.**
- The main process runs the scheduler, the source readers, and the **only
  connection that writes the staging file**.
- A `concurrent.futures.ProcessPoolExecutor` with `build_workers` processes
  runs the CPU-heavy jobs. Each worker opens its own shard file
  (`staging_dir/shard-<pid>.db`, stage tables only, created from the DDL the
  main process derived from the models, §3.5) in the pool initializer,
  writes every job's rows into it, and commits at the end of each job.
- A job returns only a small `Result[JobOutput, TaskFailed]` to the main
  process: row counts, tallies, timing.
- The writer later `ATTACH`es the shards and merges them with
  `INSERT … SELECT` at C speed, assigning final ids by rule.
- No row data ever crosses the process boundary by pickling.

This shape was chosen on measurements (§0):
- Returning rows to the writer plateaued at **16 s for the English parse at
  any worker count above 2**, because unpickling plus `executemany` in the
  single writer became the ceiling.
- For the fuzzy index on the real English keys, shards plus an ATTACH merge
  took **4 s, against 8 s returning rows and 14 s sequentially**.

**Sources are read in the main process, overlapped.** For each gzip source:
- one thread decompresses into a bounded queue of 16 MB blocks (zlib releases
  the GIL);
- a second thread scans the blocks with `bytes.find` for the prefilter needle
  and cuts the matching lines into **4 MB chunks**, each tagged with a
  sequence number;
- the main thread submits each chunk as a parse job.

Measured on the English dump, this reading costs **45 s**, against 63 s for
the same block scan without the thread and 72 s for Python line iteration.
Decompression alone is 33 s, so 45 s is near the floor for a single gzip
stream. Chunk boundaries come from the reader, not the worker count, and
they don't affect the output anyway (rule 1 of §3.5).

**The graph.** Nodes, what they depend on, and where they run:

| Node | Runs in | Depends on | Produces |
|---|---|---|---|
| `en.read` | main (2 threads) | source file | 4 MB chunks of matching lines |
| `en.parse` (one job per chunk) | pool | its chunk | in the shard: `entry_stage`, `sense_stage`, `example_stage`, `verb_form_stage`, `key_stage` (folded keys with lemma, pos, kind; includes form-of pairs), `en_word_stage`, `en_translation_stage`; returns counts per stage table, unmapped tallies, coverage counters |
| `de.read`, `de.parse` (per chunk) | main / pool | source file | in the shard: `de_entry_stage`, `de_sense_stage`, `de_example_stage`, `key_stage` (German-edition lemmas) |
| `tatoeba.parse` (one job) | pool | the three source files | in the shard: `tatoeba_pair_stage` with final ids (sorted by `(de_id, en_id)` inside the job); returns English token counts |
| `lexicon.merge` | writer | every `en.parse` and `de.parse` | `headword` (ids in sorted `(lemma, pos)` order), `entry`, `sense`, `example`, `verb_form`, `de_entry`, `de_sense`, `de_example`, `en_word`, `en_translation`, `richness` |
| `keys.merge` | writer | `lexicon.merge` | `search_key` (ids in sorted `(lang, key)` order), `key_headword`, `key_en_word` |
| `fuzzy` (`build_workers` jobs) | pool | `keys.merge` | in the shard: `fuzzy_stage(d, key_id)` for a contiguous key-id range passed as a list |
| `tatoeba.lemmas` | main, while `fuzzy` runs | `keys.merge`, `tatoeba.parse` | lemma-token documents and German common tokens, through the same `de_lemma_tokens(text, lemma_of)` the runtime uses (§4.3), with `lemma_of` querying the merged staging file through `sqlite3` with a per-token cache |
| `tatoeba.merge` | writer | `tatoeba.parse`, `tatoeba.lemmas` | `tatoeba_pair`; `tatoeba_en_fts` rebuild and `tatoeba_de_fts` insert in one step each, then `optimize`; `phrase_common_token` |
| `fuzzy.merge` | writer | every `fuzzy` job | `fuzzy_delete` (`INSERT … SELECT … ORDER BY d, key_id` over the attached shards) |
| `finalize` | writer | everything | §3.5 step 7 |

What runs in parallel:
- **Phase 1:** `en.*`, `de.*` and `tatoeba.parse` all at once. The English
  stream is the critical path.
- **Phase 2:** the `fuzzy` jobs alongside `tatoeba.lemmas` in the main
  process.

The writer works through its merge nodes in the fixed order shown. Because of
§3.5's id rules and `VACUUM INTO`, that order is for readable logs and
timings, not for correctness.

**Ids from offsets.**
- Every stage row carries `(stream, seq, local_id)`, where `local_id` counts
  from 1 within its chunk.
- When phase 1 ends, the main process knows each chunk's row counts from the
  job results. It computes `offset[stream, seq]` as the running sum in `seq`
  order, then stores the offsets in a small table in the staging file.
- The merge then inserts `offset + local_id AS id` with
  `ORDER BY seq, local_id`. Child rows (`sense` → `entry`) resolve their
  parent with the same arithmetic.
- The result is source-order ids, whichever worker parsed which chunk and
  whenever it finished.

**Worker count.** Config key `build_workers`, default `os.cpu_count() - 1`,
minimum 1. That gives 3 on the user's 4-core desktop, because the main
process keeps about one core busy reading and merging. `build_workers = 0`
runs every job inline in the main process through the same shard-and-merge
path. Tests use it and it helps debugging, and its output is byte-identical
to the parallel build. Above 2–3 workers the English stream is bound by
reading, not parsing (measured in issue 004b, see Timings).

**Start method: `forkserver`**, passed explicitly as the pool's
`mp_context`. The main process already runs reader threads when the pool
starts, and forking a threaded process can deadlock. Python 3.14 makes
forkserver the Linux default anyway. Jobs get their data only through
arguments, never through inherited state.

**Memory bound.**
- Each stream allows at most `2 × build_workers` chunks in flight: about
  24 MB of input at 3 workers, plus about 10× that while a worker holds a
  chunk's parsed JSON.
- The decompression queue holds at most 8 blocks (128 MB).
- `tatoeba.parse` holds the sentences it needs (about 950k, a few hundred
  MB). `tatoeba.lemmas` holds a per-token cache (one entry per distinct
  German token).
- Nothing holds a whole source, and stage rows go straight to disk.
- The expected peak is well under 2 GB across all processes, on a 15 GB
  desktop.

**SQLite's attach limit** (10 by default). The writer attaches at most 8
shards at a time and loops for larger pools. It detaches after each merge
node, so no shard is attached while workers write to it.

**Failure propagation, all through `Result`:**
- `run_job` is a broad-catch seam (§14.2). Inside each worker it turns any
  exception into `Err(TaskFailed(task, detail))`.
- Reader threads catch decompression errors by type (`EOFError`,
  `zlib.error`, `OSError`) and post `Err(SourceUnreadable(file, detail))`
  into a slot the scheduler polls.
- On the first `Err`, or on a `BrokenProcessPool`, the scheduler:
  1. sets a stop event that readers check between blocks;
  2. calls `executor.shutdown(wait=True, cancel_futures=True)`;
  3. deletes staging and shard files;
  4. returns `Err(BuildFailed(stage, detail))`.
- Nothing publishes, because publishing comes after the graph.

**Timings.**

| Measured (desktop, 4 cores, real 2026-10-03 English dump) | |
|---|---|
| English: decompress only, 25.6 GB of JSON | 33 s |
| English: decompress + line iteration + byte prefilter (459,333 of 10.9M lines kept, 2.0 GB) | 72 s |
| English: block scan with `find` / plus decompression thread | 63 s / **45 s** |
| English: parse + write of the kept lines (emulated mapping; 92,651 entries, 3.83M form rows, 162k translations), inline / 2 / 3 / 4 workers, rows returned to the writer | 29 / 18 / 17 / 16 s |
| German edition: decompress only / prefilter (1.11M of 1.33M lines) | 7 s / 38 s, including writing the kept lines to disk |
| German edition: parse + write, inline / 3 workers (emulation also wrote 8.9M form rows, which the design doesn't store) | 59 / 38 s |
| Fuzzy index, 448,346 English keys → 3.47M rows (60 MB): sequential / rows to writer, 4 workers / shards + merge, 4 workers | 14 / 8 / **4** s |
| Tatoeba: three bz2 files to 585,745 pairs | 18 s |
| `VACUUM INTO` canonicalisation (§0) | verified |

**End to end (estimated before issue 004b):**
- Sequential: about 63 + 29 (English) + 45 (German, upper bound) + 18
  (Tatoeba) + 14 (fuzzy) s, plus merges, FTS and `VACUUM`. Roughly 3½–4
  minutes.
- Graph: phase 1 bound by the English read (about 45–50 s), then 30–40 s of
  merges, fuzzy, FTS and `VACUUM`. Roughly 1½ minutes, about **2.5× faster**.

**Measured in issue 004b (English stream only, `--force`, desktop with 4
cores).** The dump used was 2.98 GB gzipped and gave 102,635 entries and a
253.6 MB `lexicon.db`. Output is byte-identical between 0 and 3 workers.

| Build | Wall time |
|---|---|
| Issue 004a code, single process, everything in memory | 369 s |
| Task graph, `build_workers = 0` | 270 s |
| Task graph, `build_workers = 3` | 168 s |

Speedup over `build_workers = 0` is **1.61×**, not 2.5×. Per-node wall time,
workers 0 / 3, in seconds:

| Node | 0 workers | 3 workers |
|---|---|---|
| `en.read+parse` | 202 | 115 |
| `lexicon.merge` | 4.7 | 4.8 |
| `keys.merge` | 14.8 | 14.6 |
| `fuzzy` | 21 | 10 |
| `fuzzy.merge` | 12 | 14.7 |
| `finalize` | 3.5 | 4.0 |

What this says:
- Parse CPU time is about 128 s in both runs, so at 3 workers parsing alone
  would take about 43 s. `en.read+parse` takes 115 s, so it is bound by
  decompress and scan on the main process, not by parsing.
- The 45 s read figure above does not hold for this dump and machine.
- The three serial merges add about 35 s that nothing can overlap.
- The next optimisation target is the read, not the worker count.

The graph built so far has only the English German-entries stream:
`en.read`, `en.parse`, `lexicon.merge`, `keys.merge`, `fuzzy`, `fuzzy.merge`,
`finalize`. The `de.*` and `tatoeba.*` nodes arrive with their own slices, so
the full-build figure will change.

**The phone.** The build runs only on the desktop. `harald.build` is never
imported on the phone's code paths (lazy imports, §11). The pool, `fork`
semantics and Termux therefore never meet, and none of this affects the
pure-Python rule.

---

## 4. Lookup

### 4.1 German (issues 001–003)

`lookup_de(dic, query) -> LookupResult`. With `k = fold(query.strip())`, with
internal whitespace collapsed:

1. **Exact.** `search_key(lang='de', key=k)` joined to `key_headword` gives
   distance 0, kind 0 or 1.
2. **Fuzzy, always run.** `fuzzy_delete.d IN fuzzy_deletes(k)` gives candidate
   keys. Keep those with `osa_within(k, cand, K) is not None`, where `K = 1`
   when `len(k) ≤ 4` and `K = 2` otherwise. Join them to `key_headword`.
3. **Merge** by headword, keeping the best (distance, kind). Sort by
   `(distance, is_name, kind, -richness, lemma, pos)` and cap at 20.
   Proper nouns rank after every common word at the same distance, including
   inflected-form matches: for `band`, Band (noun) and binden (form: band)
   come before Band (name). A name still ranks first when it is the only
   exact match (`Berlin`).

`osa_within` is a banded restricted-Damerau (OSA) distance that stops early
once a row's minimum exceeds `K`, so transpositions count as 1 (`bnad` →
Band). It is a pure function, which makes it the natural first target for the
anticipated Rust rewrite.

The result records how each headword matched: lemma, form (and which form,
e.g. `lief → laufen`), or fuzzy.

**Display policy.** Every headword in the best (distance, kind) tier is shown
in full, up to 3; for example `essen` (verb) and `Essen` (noun). A proper
noun is shown in full only when no common-word headword shares that tier.
Otherwise it goes in the "Also" line. Proper nouns always carry the label
`proper noun`, in results, in the Pick-entry modal and in the entry header.
Pick-entry lists the entries of one headword, which share their pos, so Band
the surname never appears among Band the noun's entries.

Tests for this:
- `lookup Deutschland` and `lookup Berlin` find the proper noun, labelled;
- `lookup band` lists Band (noun) and binden (form: band) before Band
  (name);
- a typo of a common word that is also a name's exact spelling still lists
  the common word in the same result. The rest go
on one line, "Also: Bande, Bank, …", up to 8. When the top match came through
an inflected form, a header line names it: `lief → laufen (verb)`.

**Headword display order:**
1. Each English entry: article + lemma, plural, IPA, principal parts for
   verbs, then numbered senses with `[labels] (qualifier) gloss` and their
   examples (`text — translation`; quotations verbatim with their `ref`).
2. The verb conjugation (§6).
3. A block headed "German definitions (de.wiktionary)": one sub-block per
   `de_entry` label, with senses numbered by their own `sense_index` and
   headings unnumbered.
4. A block headed "German examples (untranslated)": per `de_entry` label,
   each example prefixed with the German-edition sense index it came from.
   That is the German edition's own numbering, never matched to English
   senses.

### 4.2 English → German (issue 008)

`lookup_en(dic, word) -> EnLookupResult`: an exact match on the English
`search_key`, plus fuzzy matching by the same mechanism (confirmed by the user; formerly open
question 7). Each `en_word` is shown as `word (pos)`, then one line per
`sense` group: `employ, apply: benutzen, verwenden, gebrauchen, nutzen`. Nouns
carry their article (`die Benutzung`). In the TUI, choosing a German word runs
`lookup_de` on it.

Decisions made while implementing 008, where the design above was silent:

- **Rendering.** The sense is a line of its own with the German words one per
  line beneath it, rather than `sense: w1, w2` on one line, so long glosses
  wrap at 40 columns. Translations with an empty sense (the per-sense case in
  the source) form a group with `sense == ''`, printed directly under the
  `word (pos)` line without a sense header. Notes are dimmed in parentheses.
- **Ranking and cap.** `en_word` has no richness, so results are ordered by
  `(distance, id)`. Only the best-distance tier is shown, capped at 20
  (`_RESULT_CAP`). There is no "also" list.
- **Fuzzy mechanism.** `_key_distances(session, lang, key)` is shared with
  `lookup_de`; English keys are `search_key` rows with `lang='en'`, linked by
  `key_en_word`.
- **`en_word.ord`.** The ordinal among `en_word` rows with the same word, in
  source order. `en_word` ids come from chunk offsets (`en_word_off` in
  `offset_stage`).
- **Which translations are kept.** Top-level `translations` and
  `senses[].translations` from `lang_code == "en"` entries, only
  `lang_code == "de"` with a word. An entry with none is skipped. Gender comes
  from the translation's tags; the `english` field is kept as the note.
- **No dedupe.** Duplicate translations are kept as the source gives them.
- **Schema.** `SCHEMA_VERSION` 6 → 7 (`en_word`, `en_translation`,
  `key_en_word`). A lexicon at version 6 is refused until `harald build`.
- **Not measured.** Build time and lexicon size at the full 25.6 GB scale.

### 4.3 Phrase search (issue 018)

`search_phrases(dic, text) -> list[PhrasePair]`. The input language is not
detected; both indexes are searched.

- **English tokens**: `text.tokenize()` lowercased.
- **German tokens**: `de_lemma_tokens(text, lemma_of)`. Per token: if the
  folded token is itself a lemma key, keep it. Otherwise map it to the lemma
  of the richest headword it is an inflected form of. Otherwise keep it as
  is. Exactly one token per position, so phrase queries keep working.
  - `lemma_of(folded_token) -> str | None` is supplied by the caller. At
    runtime it is an ORM query through the call's session; in the build it
    is a `sqlite3` query on the staging file with a per-token cache.
  - The parameter exists because the build is the `sqlite3` exception
    (§3.5). Tokenising, folding and choosing the lemma stay in one function,
    so indexing and querying can't drift apart; only the key lookup
    differs.
- **Tiers, per index, deduplicated across tiers, capped at 50 in total:**
  1. phrase (`"t1 t2 …"`; English only, since German lemma order is less
     meaningful);
  2. all terms (implicit AND);
  3. any term (`OR`) over tokens **not** in `phrase_common_token`. Skipped if
     none remain.
  Within each tier, results are ordered by bm25.
- **User input never reaches `MATCH` raw.** Tokens come from a
  `\w+` regex and are each wrapped in double quotes, so `-`, `AND`, `*` and
  quotes cannot become FTS syntax.

This meets the testable criterion: `repeats itself` hits the AND tier and
returns "History repeats itself. / Geschichte wiederholt sich." first. It also
handles the case the spec describes, where exact wording misses: "and the
pattern then repeats itself" falls through to the OR tier over
`pattern repeats itself` (2.5 ms measured). The tiers matter because porter
stems `use` to `us`, so without the phrase tier "make use of" ranks
"That makes two of us." first (measured).

**Known limitation.** A separable verb split across a sentence
(`ruft … an`) is indexed as `rufen … an`, so the query `anrufen` misses it,
while `ruft an` matches. This is accepted for v1.

### 4.4 Data access to `lexicon.db`: ORM, with a mechanical Core fallback

The user has chosen the SQLAlchemy ORM for both databases, for readability in
review and one data-access style. The startup cost (§0) is accepted under the
budgets of §14.9.

**Package boundary.** Everything SQLAlchemy stays inside `harald/lexicon/`.
- The public functions (`open_lexicon`, `lookup_de`, `lookup_en`,
  `load_headword`, `search_phrases`) take a `Lexicon` and return the frozen
  dataclasses of `lexicon/model.py`.
- Callers never see a `Session`, a mapped class or a `Row`. Results are
  converted inside the package before the session closes.
- So a later swap to Core, or to a Rust extension, stays local to the package.

**Declarative models, in the same style as `learning.db`.**
`lexicon/models.py` defines `class Base(DeclarativeBase)` and read-only
mapped classes: `Headword`, `Entry`, `Sense`, `Example`, `VerbForm`,
`DeEntry`, `DeSense`, `DeExample`, `EnWord`, `EnTranslation`, `SearchKey`,
`KeyHeadword`, `FuzzyDelete`, `TatoebaPair`, `Meta`, `Source`, `SourceFile`,
`BuildStat`, `UnmappedTagset`.
- They use typed `Mapped[...] = mapped_column(...)` columns, as kohle and
  `learning/models.py` do.
- Indexes live in `__table_args__`.
- Every relationship is `lazy="raise"`.
- The two FTS5 `CREATE VIRTUAL TABLE` statements are `DDL` attached to
  `Base.metadata`'s `after_create` event, so `create_all` makes the whole
  schema.

`lexicon` has its own `Base`, separate from `learning`'s. Each database
keeps its own metadata, and `lookup` never configures `learning`'s mappers.

This is the single definition of `lexicon.db`'s schema: the build creates
from it (§3.5), the runtime reads through it, and the drift check compares
a built fixture against it (§3.1).

**Query shapes**, the ones benchmarked in §0. Each fallback is a mechanical
swap inside the package:

| Path | ORM form (default) | Core fallback |
|---|---|---|
| exact and fuzzy candidates | 2.0-style `select(SearchKey.key, KeyHeadword.headword_id).distinct().join(…).where(FuzzyDelete.d.in_(deletes))` through `session.execute` | the same `select()` over `Model.__table__.c` columns through `connection.execute`; identical SQL |
| headword load (entries, senses, examples, verb forms, German block) | `select(Headword)…options(selectinload(…))` with explicit loaders, since `lazy="raise"` forbids accidental N+1 lazy loads | column `select()`s per `__table__`, the same few statements selectin loading emits, assembled into the same dataclasses |
| English → German | `select(EnWord)….options(selectinload(EnWord.translations))` | column selects, assembled |
| FTS5 phrase tiers | `session.execute(text("SELECT rowid FROM tatoeba_en_fts WHERE tatoeba_en_fts MATCH :q ORDER BY rank LIMIT :n"), …)`, then `select(TatoebaPair).where(TatoebaPair.id.in_(ids))` | the same `text()` through `connection.execute`; pairs by a column select |
| version check | `select(Meta.value).where(Meta.key == "schema_version")` | a column select |

FTS5 goes through `text()` because `MATCH`, `rank`, `bm25()` and virtual
tables have no ORM expression. Mapping a virtual table would buy nothing
when the query only needs rowids, and its DDL can't come from a mapped
class. That is why the DDL rides on `Base.metadata` as `DDL`. Everything else stays ORM-native, which is
the point of the user's choice. User input still never reaches `MATCH` raw:
the quoted token string travels as the `:q` bind parameter (§4.3).

**Engine and sessions.**
- `make_engine(path, read_only=True)` (§7.7) builds
  `sqlite+pysqlite:///file:<path>?mode=ro&immutable=1&uri=true`, with no
  PRAGMAs, since the file is immutable.
- `make_session_factory(engine)` is the same factory `learning.db` uses.
- `Lexicon` holds the engine and the factory. Each public function opens
  one short session and closes it after conversion, so no identity map grows
  across lookups in a long TUI session.
- `open_lexicon` returns `Err(NotALexicon(…))` on
  `sqlalchemy.exc.DatabaseError`, caught by type.

---

## 5. Normalisation and answer checking (`harald/text.py`)

- `fold(s)` (§3.3) is used only for lookup and search keys. It is part of
  `SCHEMA_VERSION`.
- `answer_matches(given, expected) -> bool`:
  - NFC, strip, collapse internal whitespace;
  - map ä→ae, ö→oe, ü→ue, ß→ss and the capital forms on **both** sides;
  - then compare exactly, **case-sensitive**.

  This is the spec's "checked exactly, except that ae/oe/ue/ss are always
  accepted for ä/ö/ü/ß". Folding both sides in one direction means a typed
  `ae` is accepted for `ä`, and so is `ä` itself. The only over-acceptance is
  something like `daürt` for `dauert`, which is harmless.
- `tokenize(s)` = `re.findall(r"\w+", s)`.

---

## 6. Width-adaptive rendering (`harald/render.py`)

The phone runs the TUI in **portrait**, the user's decision (§12.8):
**40 columns is the minimum width**, and desktop or SSH use keeps 80 or
more. Rendering is therefore width-adaptive, and the CLI and the TUI still
share it.

- **Shared renderables.** `render_lookup()`, `render_headword()`,
  `render_conjugation(conj, full)`, `render_en_lookup()`,
  `render_phrase_pairs()`, `render_info()` and `render_check()` return
  small renderable classes that implement Rich's
  `__rich_console__(console, options)`. Each picks its layout from
  `options.max_width` at render time.
  - In the CLI, `rich.console.Console()` passes the terminal width (80 and
    no colour when piped).
  - In the TUI, the `Static` widget passes its own width.

  So the same object lays itself out for a 40-column portrait phone, a
  60-column landscape-ish window and a 100-column desktop. The CLI never
  imports Textual.
- **The wrap rule.** Text wraps at the available width. There is no
  80-column floor any more. Below 40 columns nothing is designed: Rich still
  folds, but layouts may degrade. Quotations still render verbatim; wrapping
  never alters their characters.
- **Layout switches, one rule for all renderables:**
  - `narrow` below 60 columns: one column, labels above values, tables
    stacked;
  - `wide` from 60 columns up.
- **Conjugation.** The principal-parts line is always shown
  (`läuft / lief / ist gelaufen`). Tenses are laid side by side, as many as
  fit: `tenses_per_row = max(1, (width - 11) // 23)`. That is 1 at 40
  columns, 2 at about 60 and 3 at 80. At 40, each tense is its own stacked
  block: a heading, then six "person form" rows, each 11 + about 28 columns.
  - The default set (Präsens, Präteritum, Perfekt, Imperativ) and the full
    set (`--conj`, `c`) are unchanged. In portrait they simply stack and
    scroll; no paging keys are needed.
  - Separable verbs show the data's split forms (`rufe an`), and the entry
    header carries the **TRENNBAR an|rufen** badge (§7.2).
  - Subordinate-clause forms are stored but not shown.
- **Width-parametrised test hook**, replacing the 80-column hook.
  - Render each function into `Console(width=w, record=True,
    file=io.StringIO())` for `w` in 40, 60, 80 and 100.
  - Assert two things: every line of `export_text()` is at most `w`
    characters; and nothing is lost — every form, gloss and example of the
    fixture appears in the text.
  - Fixtures: Band, laufen, anrufen, verschlimmbessern and Deutschland (a
    proper noun).

---

## 7. `learning.db`

### 7.1 Schema v1 (created complete in issue 010)

```sql
-- The schema the models in learning/models.py express (§7.7); created by Alembic revision 0001
-- (§7.6), which alembic_version records. Timestamp columns are SQLAlchemy DateTime and
-- card.content is sqlalchemy.JSON, so the emitted DDL names those types; affinities match.
CREATE TABLE word (id INTEGER PRIMARY KEY,
  lemma TEXT NOT NULL, pos TEXT NOT NULL, discriminator TEXT NOT NULL,   -- the hint key
  created_at TEXT NOT NULL, UNIQUE (lemma, pos, discriminator));
CREATE TABLE phrase (id INTEGER PRIMARY KEY,
  en TEXT NOT NULL, de TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
  tatoeba_de_id INTEGER, tatoeba_en_id INTEGER,      -- provenance; NULL when hand-written
  created_at TEXT NOT NULL);
CREATE TABLE card (id INTEGER PRIMARY KEY,
  word_id INTEGER REFERENCES word(id), phrase_id INTEGER REFERENCES phrase(id),
  card_type TEXT NOT NULL CHECK (card_type IN ('meaning_de_en','meaning_en_de','meaning_de_de',
     'article','stammformen','conjugation','phrase_en_de')),
  content TEXT NOT NULL,                 -- JSON, §7.2: the card's own copy
  created_at TEXT NOT NULL,
  suspended INTEGER NOT NULL DEFAULT 0, deleted_at TEXT,
  fsrs_state INTEGER NOT NULL, fsrs_step INTEGER, stability REAL, difficulty REAL,
  due TEXT NOT NULL, last_review TEXT,   -- last_review IS NULL means new
  link_state TEXT NOT NULL DEFAULT 'linked' CHECK (link_state IN ('linked','unlinked')),
  check_ack TEXT,                        -- fingerprint of a dismissed check flag (§8.3)
  CHECK ((word_id IS NULL) <> (phrase_id IS NULL)));
CREATE INDEX card_due ON card(due) WHERE deleted_at IS NULL AND suspended = 0;
CREATE INDEX card_word ON card(word_id);
CREATE INDEX card_phrase ON card(phrase_id);
-- Deleted cards are hidden by the session's global criteria (§7.7), not by a view.
CREATE TABLE review (id INTEGER PRIMARY KEY, card_id INTEGER NOT NULL REFERENCES card(id),
  session_id TEXT NOT NULL, reviewed_at TEXT NOT NULL,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 4), scope TEXT NOT NULL,
  duration_ms INTEGER, answer TEXT,      -- typed answer, for checked cards
  state_before TEXT NOT NULL, state_after TEXT NOT NULL);   -- fsrs Card.to_dict() JSON
CREATE INDEX review_card ON review(card_id, reviewed_at);
CREATE INDEX review_time ON review(reviewed_at);
CREATE INDEX review_session ON review(session_id);
CREATE TABLE deck (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
CREATE TABLE deck_member (deck_id INTEGER NOT NULL REFERENCES deck(id) ON DELETE CASCADE,
  word_id INTEGER REFERENCES word(id), phrase_id INTEGER REFERENCES phrase(id),
  CHECK ((word_id IS NULL) <> (phrase_id IS NULL)));
CREATE UNIQUE INDEX deck_member_word ON deck_member(deck_id, word_id) WHERE word_id IS NOT NULL;
CREATE UNIQUE INDEX deck_member_phrase ON deck_member(deck_id, phrase_id) WHERE phrase_id IS NOT NULL;
CREATE TABLE fsrs_params (scope TEXT PRIMARY KEY, parameters TEXT NOT NULL,
  desired_retention REAL NOT NULL);      -- empty in v1, so defaults; a future optimiser writes here
CREATE TABLE operation_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at DATETIME NOT NULL);
CREATE TABLE operations (id INTEGER PRIMARY KEY AUTOINCREMENT,      -- kohle's columns (§7.8)
  group_id INTEGER NOT NULL REFERENCES operation_groups(id),
  entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL, action TEXT NOT NULL,
  field TEXT,                            -- changed attribute names (Harald fills it)
  state TEXT);                           -- JSON of the old values (Harald fills it)
```

- **Two partial unique indexes, not `UNIQUE(deck_id, word_id, phrase_id)`**,
  because SQLite treats NULLs as distinct in UNIQUE constraints, so the
  single constraint would never fire.
- **The whole v1 schema is created in issue 010**, by Alembic revision
  `0001`, rather than grown slice by slice. It is fully designed here, and the user will study on the phone
  between slices. Per-slice migrations would mean shipping and testing schema
  changes against real data with no benefit. `conjugation` is in the
  `card_type` CHECK now because changing a CHECK later means rebuilding the
  table.
- **Connection settings**, set by the engine's connect hook (§7.7):
  `foreign_keys=ON`, `journal_mode=WAL`, `synchronous=FULL`,
  `busy_timeout=5000`. WAL lets `harald backup` read
  while the TUI writes. FULL means a grade survives an OS crash or power loss,
  not only a process kill, at the cost of one fsync per grade, which is
  negligible.
- **Timestamps**: naive-UTC `DateTime` columns, as in kohle. SQLAlchemy
  stores them as fixed-width ISO text, so string order is time order. They
  are converted to aware UTC at the fsrs boundary.
- **Migrations**: Alembic, with `target_metadata` from the models, a
  pre-migration backup, and a fast path that skips importing Alembic (§7.6).
- **All access goes through kohle's `UnitOfWork` / `DbTransaction.execute`**
  (§7.7): commit on `Ok`, roll back on `Err` or on any exception. Services do
  their persistence through `DbTransactionContext.run`, which maps
  `IntegrityError` to `UniqueViolation`. Both are broad-catch seams, with
  kohle's Override (§14.2). The runtime engine keeps kohle's default pysqlite
  transaction handling. The earlier draft's explicit `BEGIN IMMEDIATE` was
  dropped: the TUI is the only writer, and `busy_timeout` covers a concurrent
  `harald backup` reader.

### 7.2 Card content (`learning/content.py`): the card's own copy

| card_type | content JSON | FSRS scope | answer |
|---|---|---|---|
| `meaning_de_en` | `lemma, pos, gender, gloss, labels, example?` | meaning | self-graded; front: article + lemma (+ German example as context), back: gloss (+ translation) |
| `meaning_en_de` | same | meaning | self-graded; front: gloss, labels, pos; back: article + lemma (+ example) |
| `meaning_de_de` | `lemma, pos, gender, definition` | meaning | self-graded; front: German definition; back: article + lemma |
| `article` | `lemma, gender` (one or more of m/f/n), `plural`, `hint` | article | front: lemma, plural, hint; one keypress: `1` der, `2` die, `3` das; any listed gender is correct |
| `stammformen` | `infinitive, hint, pres3sg, preterite, participle, auxiliaries, separable_prefix` | conjugation | front: infinitive, hint, and the **TRENNBAR** badge when `separable_prefix` is set; three typed fields: er/sie/es Präsens, Präteritum, Perfekt (`ruft an` / `rief an` / `hat angerufen`); all must match |
| `conjugation` | persons still blocked (§16); carries `separable_prefix` like Stammformen | conjugation | typed |
| `phrase_en_de` | `{}`: the `phrase` row is the copy | phrase | self-graded; front: English (+ note), back: German |

- `CARD_SCOPE` is a single dict from card type to scope. Moving
  `meaning_de_de` to its own scope is the one-line change the spec promises.
- `example` is the sense's first translated `kind == 'example'` example,
  copied at creation. It exists because several German → English cards of
  one word would otherwise show identical fronts with nothing to say which
  sense is being asked for.
- `hint` (article and Stammformen) is the word's first chosen English gloss,
  or its first chosen German definition when only German senses were picked,
  copied at creation. `plural` is copied for article cards. Without them,
  homographs show identical fronts while expecting different answers: Band
  n/m/f, See, Leiter for articles, and umfahren (`fährt um` vs `umfährt`) for
  Stammformen. Found while laying out the study screens (§12.6).
- **Separable verbs** (open question 5 part 2, resolved by the user):
  - the answers are the data's main-clause split forms (`ruft an`,
    `rief an`, `hat angerufen`);
  - the card shows that the verb is separable, through `separable_prefix`
    (`"an"`), copied at creation from the entry (§3.3), so the highlight is
    data-driven;
  - the front and the feedback render **TRENNBAR an|rufen**, a short label
    that fits 40 columns (§12.8). The feedback adds that the prefix moves to
    the end in main clauses;
  - `check` compares `separable_prefix` like the forms (§8.1).
- The Perfekt field expects `<aux 3sg> <participle>`, using
  `{"haben": "hat", "sein": "ist"}`. That mapping is German grammar, not
  source knowledge. Verbs with two auxiliaries accept either.

### 7.3 Adding a word (issues 010–014)

`PlanWordCards(dic).execute(headword, entry | None, en_sense_ids, de_sense_ids) -> CardPlan`
(issue 013 adds a tenses argument once open question 5 is settled)
returns `CardPlan(word_hint, cards: list[NewCard], refusals: list[Refusal(card_type, missing: list[str])])`.
- `PlanWordCards` is a plain use-case class in `use_cases/cards.py`
  (§11.2), because as designed here it reads only the lexicon.
- If issue 010 puts the dedupe against live cards (below) in the planner
  rather than in `CreateWordCards`, the planner reads `learning.db`. It
  then becomes a `UnitOfWork` subclass, with the lexicon passed to
  `execute`.

- Every chosen English-edition sense gives one `meaning_de_en` and one
  `meaning_en_de` card. Every chosen German-edition sense (only those with a
  `sense_index`; headings can't be picked) gives one `meaning_de_de` card.
- Article (nouns) and Stammformen (verbs) cards are added **once per word**,
  whenever any sense is added. They are refused with the missing items named:
  `missing: gender`; `missing: Präteritum, auxiliary`. German labels are used
  for forms, because that is what the learner sees on the card.
- The two pickers are separate: English-edition senses of the chosen English
  entry, and German-edition senses of the whole (lemma, pos) group, grouped
  under each `de_entry` label. German-edition-only headwords (no English
  entry) can be added. They get `meaning_de_de` cards only, with hint
  `(lemma, pos, '')`.
- **Dedupe**: a planned card identical in `(word, card_type, content)` to a
  live card is dropped. The pickers mark senses that already have cards.
- `CreateWordCards(session).execute(plan, deck_ids) -> Result[list[int],
  LearningDbError]` runs in **one transaction** (`DbTransaction.execute`, §7.7):
  upsert the `word` row by hint key, insert the cards (fsrs state from a
  fresh `Card(card_id=<new id>)`), insert deck memberships. Refusals are
  shown before the user confirms, and they never block the other cards.

### 7.4 Study (issues 010, 011, 012, 015, 016)

`NextCard(session).execute(now, session_id, deck_id | None) ->
Result[Option[StudyCard], LearningDbError]` (§14.10). Like every `learning.db` access it runs through
`DbTransaction` (§7.7). Eligible
cards are live, not suspended, in the deck if a filter is set, and **not
sibling-buried**.
1. Cards that have been reviewed before and have `due ≤ now`, earliest due
   first. This includes learning-step re-shows.
2. Otherwise a new card (`last_review IS NULL`), oldest first, if fewer than
   `new_cards_per_day` cards had their first review today.
3. Otherwise a Learning or Relearning card due within the next 20 minutes
   (learn-ahead), so a card just graded Again still comes back before the
   session ends.
4. Otherwise return `Option.none()`, which ends the session and shows the summary.

- **Day**: local time, starting at `day_starts_at` (default 04:00). "Today"
  means `reviewed_at ≥` the start of the current study day, converted to UTC.
- **Sibling burying is computed, never stored**: a card is excluded if any
  *other* card with the same `word_id` or `phrase_id` has a review today.
  That leaves nothing to clean up, it survives a kill, and burying across
  deck filters follows automatically.
- `Grade(session).execute(card_id, rating, now, session_id, duration_ms,
  answer) -> Result[None, LearningDbError]` runs in **one transaction**
  (`DbTransaction.execute`): read the card's fsrs state, call
  `scheduler_for(scope).review_card(card, rating, review_datetime=now_utc,
  review_duration=duration_ms)`, update the card's fsrs columns, and insert
  the `review` row with both state snapshots. On commit, the grade is
  durable. On `Err` nothing was written: the TUI shows the error and keeps
  the card on screen, so "loses at most the card on screen" still holds.
- **Checked cards grade themselves**: correct → `Rating.Good`, wrong →
  `Rating.Again`. The article card stays a single keypress, and a failed
  conjugation check is a lapse. Hard and Easy are reserved for self-graded
  cards.
- **Session summary** = `SessionSummary(session).execute(session_id)`, computed from the
  review log. "Reviewed" counts distinct cards. "Answered correctly" counts
  cards whose first grade in the session was not Again. Because it comes from
  durable rows, a summary is exact even when the session ran across learning
  steps.
- **Schedulers**: one `fsrs.Scheduler` per scope, built from the
  `fsrs_params` row or the package defaults and cached per process. Fuzzing
  stays on. Tests pass `enable_fuzzing=False` through a factory argument.
- `now` is always a parameter. Nothing in `learning/` calls `datetime.now()`
  itself, so day boundaries, caps and burying can be tested.

### 7.5 Card management (issues 016, 017)

- **Edit**: the card's content fields, plus the `phrase` row for phrase
  cards, open in the `$EDITOR` template (§9). Validation is per type: no
  empty required field, gender drawn from `mfn`. FSRS state is kept, since an
  edit is a correction, not a new card.
- **Suspend and unsuspend**: a flag.
- **Delete**: set `deleted_at`. The session's global criteria (§7.7) hide
  deleted cards from every ORM query unless it opts in with `include_deleted`,
  so "removed from every listing" lives in one place. Review rows remain,
  with their foreign keys intact.
- **Decks**: create and delete (membership rows cascade, cards are
  untouched), and toggle an item's membership from the add screen or the
  cards screen. The scheduler never reads deck tables. Only `NextCard`'s
  filter does.

### 7.6 Migrations (Alembic)

Alembic is the user's choice, as in kohle. It replaces the hand-rolled
`MIGRATIONS` list and `PRAGMA user_version` of the earlier draft.

**Scope: `learning.db` only.** `lexicon.db` stays on `SCHEMA_VERSION` (§3.5).
It is rebuilt from scratch by every build and never upgraded in place, so
there is no chain of revisions to apply. Its only compatibility question is
exact equality with the running code. An `alembic_version` table would just
add bytes to a file that must change only when its content does.

**Models are the source of truth.** `learning.db` is accessed through SQLAlchemy
at runtime with kohle's infrastructure (§7.7). So, as in kohle's `env.py`,
`target_metadata = Base.metadata`, where `Base` is Harald's
`DeclarativeBase` in `learning/models.py`.
- **Revisions are drafted with `alembic revision --autogenerate`** and then
  reviewed by hand. Autogenerate misses some SQLite details (partial-index
  `WHERE` clauses, CHECK changes), and a revision ships to the only copy of
  the user's data.
- **A drift test** runs `alembic.command.check` against a database upgraded
  to head. It fails if the models and the revisions disagree.

**Layout.** The script directory ships *inside* the package, because Harald
runs installed on a phone, not from a checkout.

```
src/harald/learning/models.py                Base(DeclarativeBase) and the §7.1 tables
src/harald/learning/migrate.py               HEAD = "0001"; fast-path check; programmatic upgrade
src/harald/learning/migrations/env.py        online only; target_metadata = Base.metadata;
                                         connection from config.attributes
src/harald/learning/migrations/script.py.mako   template for `alembic revision` (dev only)
src/harald/learning/migrations/versions/0001_initial.py
alembic.ini (repo root, dev only)        script_location = src/harald/learning/migrations
```

- **Revision ids** are sequential four-digit strings (`alembic revision
  --rev-id 0002 --autogenerate -m …`) in one linear history. A test asserts a
  single head.
- **`0001_initial.py`** is the reviewed autogenerate output for the §7.1
  models. Later revisions use `op.add_column` or `op.batch_alter_table`.
  `batch_alter_table` performs SQLite's copy-and-rename table rebuild, which
  is the main thing Alembic buys on SQLite: changing a CHECK or dropping a
  column needs it.
- **Runtime `Config`, built in code with no ini file.** `script_location` is
  the absolute path `Path(migrate.__file__).parent / "migrations"`, rather than
  the `harald.learning:migrations` resource form, whose code path Alembic's own
  source marks as untested.
- **Packaging.** `env.py` and `versions/*.py` are Python files and land in the
  wheel. `script.py.mako` is only needed by `alembic revision`, which runs
  from the source tree.

**Open-time sequence**, `open_learning_db(path) -> Result[LearningDb, LearningDbError]`
(`learning/db.py`):
1. **Build the engine.** Call `make_engine(path, pragmas=LEARNING_DB_PRAGMAS)`
   (§7.7) and `make_session_factory(engine)`. That imports SQLAlchemy and its
   ORM, which a TUI start pays for anyway, but not Alembic.
2. **Fast path.** On a plain engine connection, read `SELECT version_num FROM
   alembic_version`. A missing table counts as no revision
   (`sqlalchemy.exc.OperationalError`, caught by type).
   - If the revision equals `HEAD`, return `Ok(LearningDb(engine,
     session_factory))`. Alembic, and Mako with it, is not imported, which
     saves the part of the 278–296 ms `alembic.command` import (§0) that comes
     on top of SQLAlchemy.
   - A test keeps `HEAD` equal to Alembic's computed head, so the constant
     cannot drift.
3. **Check the revision.** Otherwise import Alembic lazily and load the script
   directory.
   - A revision this Harald doesn't know comes from a newer Harald, so return
     `Err(LearningDbTooNew(found, HEAD))` and touch nothing. Harald never
     downgrades at runtime.
   - A file with tables but no `alembic_version` returns
     `Err(NotALearningDb(path))`.
4. **Backup.** If the file holds a revision, write the pre-migration backup
   first: `VACUUM INTO 'learning.db.pre-<HEAD>.bak'` next to it, run through
   `engine.connect().execution_options(isolation_level="AUTOCOMMIT")` with
   `exec_driver_sql`, because VACUUM cannot run inside a transaction. If that
   fails, return `Err(MigrationFailed("backup", …))` without migrating. A
   brand-new file needs no backup.
5. **Upgrade.**
   - Use a separate migration engine, `make_engine(path)` plus SQLAlchemy's
     documented pysqlite recipe for transactional DDL: set the DBAPI
     connection's `isolation_level = None` on connect, and emit `BEGIN` on the
     engine's `begin` event.
   - Put the open connection into `config.attributes["connection"]` and call
     `command.upgrade(config, "head")`.
   - `env.py` configures `transactional_ddl=True` and
     `transaction_per_migration=True`, so each revision commits or rolls back
     whole. A failure in revision 3 leaves the database consistently at
     revision 2, with the backup beside it.
   - This step is a broad-catch seam (§14.2): any exception becomes
     `Err(MigrationFailed("upgrade", …))`.
   - The recipe lives only on the migration engine. The runtime engine keeps
     kohle's default pysqlite transaction handling, so that `DbTransaction`
     behaves exactly as in kohle.
6. **Return.** Dispose of the migration engine and return `Ok` with the
   runtime engine from step 1.

Further details:
- **Foreign keys.** The migration engine leaves `PRAGMA foreign_keys` off
  (SQLite's default), which `batch_alter_table` rebuilds require. The runtime
  engine's connect hook turns it on, as kohle's does.
- **No offline mode.** `env.py` refuses `alembic upgrade --sql`. Migrations
  only ever run against a real file, and SQLite batch migrations can't render
  offline without hand-kept table snapshots (`copy_from`) in every batch
  revision.
- **Dev CLI path.** `uv run alembic -x db=PATH upgrade head` (and `revision
  --autogenerate`) works on an explicitly named file. There is no default URL,
  so nothing is migrated by accident.

**Testing migrations** (all on the desktop, against temporary files):
- **Round trip.** Upgrade base → head, then check the result: `sqlite_master`
  holds the §7.1 objects and `alembic check` reports no drift. Downgrade to
  base and upgrade again. kohle has `test_migration_downgrade.py` because a
  broken downgrade went unnoticed there.
- **Data preservation, from `0002` on.** Build the database at the previous
  revision, insert representative rows, upgrade, and check that they survive
  in the expected shape.
- **Head.** `HEAD == ScriptDirectory.get_current_head()`, and there is exactly
  one head.
- **`open_learning_db`:**
  - a fresh path ends at head with no backup;
  - an older revision gets `learning.db.pre-<HEAD>.bak` and is upgraded;
  - an unknown revision returns `LearningDbTooNew` and leaves the file
    byte-identical;
  - a revision that raises (from a test-only script directory) returns
    `MigrationFailed` and leaves the database at the last good revision.
- **Unit tests** build the schema from `Base.metadata.create_all` on an
  in-memory engine, as kohle's `conftest.py` does. Only the migration tests
  drive Alembic.
- **Rehearsal on real data before releasing a revision.** Copy the newest
  phone backup out of the desktop's backup folder (§10) and run
  `uv run alembic -x db=<copy> upgrade head` on the copy, never on the backup
  itself.
- **On the phone.** Issue 009's checklist covers installing the stack on
  Termux and running one upgrade there (§15).

### 7.7 kohle's database infrastructure, and the future shared package

The user plans to converge Harald and kohle on one shared db-handling package.
So `learning.db` uses **kohle's infrastructure, with kohle's names and shapes**,
in mirrored module paths. Lifting it out later becomes a package rename, not a
rewrite. Mirrored paths:

| Harald module | kohle original | Contents |
|---|---|---|
| `harald/core/result.py` | `kohle/core/result.py` | `Result[T, E]`, unchanged API; `E` bound to `Exception` |
| `harald/core/option.py` | `kohle/core/option.py` | `Option[T]`, kohle's API, typed; a picklable `bool` flag instead of kohle's sentinel; `from_optional` added (§14.10) |
| `harald/db/connection.py` | `kohle/db/connection.py` | `make_engine(path, *, pragmas=None, read_only=False)`, `make_session_factory(engine)`, the PRAGMA connect hook; used for both databases |
| `harald/infrastructure/infra_errors.py` | same path | `InfrastructureError`, `UniqueViolation(constraint)`, `check_if_unique_constraint_failed(err, column)` |
| `harald/infrastructure/transaction_context.py` | same path | `DbTransactionContext(session)` with `run(op) -> Result[T, InfrastructureError]` (flush; `IntegrityError` → `UniqueViolation`; any other `Exception` → `InfrastructureError(str(e))`), plus kohle's audit state: `transaction_group`, `transaction_steps`, `record_transaction_step()` |
| `harald/infrastructure/uow.py` | same path | `DbTransaction(session).execute(use_case)`: on `Ok`, add the recorded `Operation` rows and commit; roll back on `Err` or exception (→ `Err(e)`); close the session in `finally`. `UnitOfWork[T, E]` with `_run` |
| `harald/infrastructure/crud.py` | same path | `crud_create` / `crud_update` / `crud_delete` / `crud_retrieve` (§7.8) |

**How Harald uses it** (kohle's pattern, Harald's domain modules):
- `learning/models.py`: `class Base(DeclarativeBase)` and mapped classes `Word`,
  `Phrase`, `Card`, `Review`, `Deck`, `DeckMember`, `FsrsParams`.
  - CHECK constraints and the two partial unique indexes go in
    `__table_args__` (`CheckConstraint`; `Index(..., unique=True,
    sqlite_where=...)`).
  - `Card.content` is `sqlalchemy.JSON`.
  - Types are `Integer`, `Text`, `Float`, `DateTime`, so the emitted DDL keeps
    §7.1's affinities.
- **Service functions** take a `DbTransactionContext`, do persistence through
  `ctx.run(op)`, and map infrastructure errors into Harald's families with
  `map_err`, as kohle's services do. For example `DeckNameTaken(name) if
  check_if_unique_constraint_failed(err, "deck.name") else StorageError(str(err))`.
- **Use cases are `UnitOfWork` subclasses with `execute(...)`, in
  `harald/use_cases/` (§11.2):**
  - `CreateWordCards`, `SavePhrase`, `EditCard`, `SetSuspended`,
    `DeleteCard` (`use_cases/cards.py`);
  - `NextCard`, `Grade`, `SessionSummary` (`use_cases/study.py`);
  - `CreateDeck`, `DeleteDeck`, `SetDeckMembership` (`use_cases/decks.py`).

  Front-ends construct one with a fresh session, as kohle's CLI does:
  `Grade(ldb.session()).execute(card_id, rating, now, …)`.
- **Code layout: kohle's layers on Harald's packages** (revised 2026-10-20,
  §11.2).
  - Use cases live in `harald/use_cases/`, as in kohle. The earlier
    revision kept them inside the domain modules; the user chose kohle's
    `use_cases/` layer instead (confirmed 2026-10-24).
  - Their services stay in `harald/learning/<area>.py`, next to the models
    and errors of the database they write, rather than in a separate
    `services/` folder. `lexicon/` and `build/` already play that role for
    their side, and keeping one tree per database keeps each database's
    code together.
  - Only the infrastructure has to match kohle for the lift.
- **Session settings are kohle's:** `autoflush=False`,
  `expire_on_commit=False`. `DbTransaction.execute` closes the session after
  each use case, so a use case is single-shot, and returned objects stay
  usable because they don't expire.
- **Deleted cards are hidden in one place**, replacing the earlier
  `live_card` view. `learning/db.py` registers SQLAlchemy's documented global-
  criteria recipe on the session factory: a `do_orm_execute` listener adds
  `with_loader_criteria(Card, Card.deleted_at.is_(None))` unless a query sets
  `execution_options(include_deleted=True)`. Only the history-keeping code
  opts out. An ORM query that forgets a filter cannot list deleted cards.
- **Timestamps follow kohle:** naive-UTC `DateTime` columns, which SQLAlchemy
  stores as fixed-width ISO text, so string order is time order. They are
  converted to aware UTC only at the fsrs boundary, because fsrs rejects naive
  datetimes.

**What Harald deliberately does differently**, each one a thing a future
shared package would have to resolve:
1. **An engine factory, not a module-global engine.**
   - kohle's `connection.py` builds `engine` at import time from a hardcoded
     `sqlite:///kohle.db`, plus a module-level `session_local` and `base`.
   - Harald has two databases and a configurable path, and building an engine
     at import time would also put SQLAlchemy on the lazy-import path of
     every command.
   - So: `make_engine(path, *, pragmas=None, read_only=False)` and
     `make_session_factory(engine)`. `read_only` builds the `mode=ro`
     `immutable` URI that `lexicon.db` uses.
     kohle would become `engine = make_engine(Path("kohle.db"),
     pragmas={"foreign_keys": "ON"})`.
   - **This is the main fix a shared package would need.**
2. **The connect hook takes a PRAGMA map** instead of hardcoding
   `foreign_keys=ON`. Harald's `learning.db` needs `foreign_keys=ON`,
   `journal_mode=WAL`, `synchronous=FULL` (a grade survives power loss) and
   `busy_timeout=5000`. kohle passes only `foreign_keys`.
3. **No declarative base in the infrastructure.** kohle's `connection.py`
   owns `base = declarative_base()` (the legacy API). Harald's `Base` lives
   in `learning/models.py`. A future shared package should not own an application's
   metadata.
4. **The audit trail is kohle's, retained (§7.8), with one usage
   difference.** Harald fills `Operation.state` and `Operation.field`, which
   kohle defines but never writes, with the old values of changed attributes,
   captured by a `before_flush` listener. That is what makes undo possible.
   The schema and the decorator API are kohle's. A future shared package
   would carry the audit (models as something each app declares on its own
   `Base`, the decorators, `record_transaction_step`), and kohle could adopt
   the snapshot hook.
5. **A programmatic Alembic runner** (`learning/migrate.py`: `HEAD` fast path,
   pre-migration backup, per-revision transactions). kohle runs `alembic
   upgrade` by hand. This is a shared-package candidate that kohle could
   adopt.

**Future package boundary. Informational, user-owned, not a Harald
deliverable.** The user has deferred the shared package and will assess
reusability themselves. No Harald issue builds it. This section and the
mirrored names only keep a later lift cheap.
- **Shared:**
  - `core/result.py` and `core/option.py`;
  - `db/connection.py` (the engine and session factories, the PRAGMA hook);
  - `infrastructure/{infra_errors, transaction_context, uow, crud}.py`,
    including the audit trail, with `Operation` / `OperationGroup` declared
    by each app on its own `Base`, and Harald's before-state snapshot hook;
  - the programmatic migration runner.
- **Stays in each application:**
  - its `Base` and models, its Alembic script directory, its domain errors,
    use cases and services;
  - kohle's `model_serde`;
  - Harald's `lexicon.db` access (its tables, mapped classes and
    queries, on the shared engine factory) and the build.
- **Naming and timing** of the package are the user's call. Nothing in
  Harald depends on it existing.

**`lexicon.db` uses the ORM too, in the same declarative style**, by the
user's decision: one data-access style, readable in review.
- `lexicon/models.py` has its own `Base`, as `learning/models.py` does,
  following kohle's conventions.
- One difference remains: it sits behind the `lexicon/` package interface,
  so callers get dataclasses and never a `Session` or a mapped class. A
  later Core or Rust swap therefore stays inside the package.

The details are in §4.4. The accepted startup cost and its budgets are in
§0 and §14.9.

### 7.8 Audit trail (kohle's, retained)

The user keeps kohle's audit trail in `learning.db`, for elegant rollbacks,
undos and deletes later. This reverses the earlier skip. It exists only in
`learning.db`: `lexicon.db` is rebuilt and read-only, so there is nothing
there to audit.

**What is taken from kohle unchanged:**
- **Models** in `learning/models.py`: `OperationGroup(id, created_at)` and
  `Operation(id, group_id, entity_type, entity_id, action, field, state)`,
  with kohle's exact columns.
- **`DbTransactionContext`**, now kohle's full version:
  `transaction_group`, `transaction_steps`, and `record_transaction_step()`,
  which creates the group lazily on the first recorded write, so a use case
  that only reads leaves no trace.
- **`DbTransaction.execute`**, which adds the steps before commit.
- **Decorators** `crud_create`, `crud_update`, `crud_delete` and
  `crud_retrieve` (`harald/infrastructure/crud.py`), mirroring kohle's
  `crud.py`.

**What Harald adds, so that undo is possible:**
- kohle's `Operation` already has nullable `field` and `state` columns, but
  kohle never writes them. Its rows record only *that* something happened
  (`entity_type`, `entity_id`, `action`). Undoing an update or a delete needs
  the prior values.
- So Harald fills the existing columns. **The schema is unchanged; only the
  usage differs from kohle.**
  - `state` = JSON of the **old values of exactly the attributes the write
    changed**: `{"deleted_at": null}`, or
    `{"gloss": "tape, ribbon", "labels": []}`.
  - `field` = the changed attribute names, sorted and comma-joined.
- **How the old values are captured** without changing the decorators' API:
  - A `before_flush` listener on `learning.db`'s session factory reads
    SQLAlchemy's attribute history for every dirty and deleted instance. It
    stores old values in `session.info["audit_before"][(table, id)]`.
  - It has to run at flush time because `DbTransactionContext.run` flushes
    and resets that history before a decorator could see it.
  - `crud_update` and `crud_delete` then pop that entry into
    `Operation.state` and `Operation.field`.
  - `crud_create` leaves both `NULL`. Undoing a create removes or
    soft-deletes the created row, which needs no prior state.
- **No after-state is stored.** It is either the current row (for the most
  recent change) or the next operation's before-state. That is enough to
  walk undo back, and a future redo can be built from both.
- **Serialising:** datetimes as ISO text, `JSON` columns as nested JSON.

**What is audited.** Every `learning.db` write, each use case as one
`OperationGroup`:
- `CreateWordCards`: the word upsert, each card, each deck membership;
- `SavePhrase`, and writing your own pair: the phrase, its card, its deck
  memberships;
- `EditCard`: card content, or the phrase row for phrase cards;
- `SetSuspended`;
- `DeleteCard`: `crud_delete`, which sets `deleted_at` (kohle's comment
  applies: "a soft delete is recorded as a delete");
- deck create, delete and membership changes;
- every `harald check` repair (§8.3): relink (word hint), accept (card
  content, plus FSRS fields when reset), keep (`link_state`, `check_ack`).

**What is not audited:**
- Alembic migrations, which are schema changes; the pre-migration backup
  covers them.
- Backups, which only read.
- There is no "backup restore" feature (backups are never read back), so
  there is nothing to audit there.

**Grades are audited too** (recommended, and adopted):
- `Grade` records one group with two operations:
  - `review` `create` (the new review row);
  - `card` `update`, with the old FSRS fields in `state`.
- **Cost, measured** (§0): a grade with its audit group took 8.2–8.5 ms
  median, against 7.5–8.0 ms without, so +0.2–0.9 ms. It is the same single
  fsync under `synchronous=FULL`, and well inside the 15 ms target.
- The review log already holds before and after, so the operation rows
  duplicate a little. The gain is that "undo the last action" walks one log
  (operation groups) for every kind of write, instead of two.

**Soft delete and the global criteria.**
- The deleted-card criteria (§7.7) hide deleted rows from normal queries.
- Audit readers (and a future undo) must load deleted rows, so they set
  `execution_options(include_deleted=True)`.
- Undoing a delete clears `deleted_at`. Undoing a create soft-deletes the
  row for cards, and deletes it for rows with no dependants, such as deck
  memberships.

**Enabled, but not delivered in v1:**
- undo the last action; undo a delete; revert a card edit;
- roll back a `check` repair, including a schedule reset;
- undo the last grade.

The spec excludes undo of the last grade for v1, and none of these is in
scope. The audit is designed to be **sufficient** for them: every write
leaves its entity, action and prior values in one group per user action.

A future grade-undo should **append** a compensating record rather than
delete the review row. The spec keeps the full review log for FSRS
optimisation.

**Alembic.** `operation_groups` and `operations` are part of `learning.db`'s
revision `0001` (§7.1). The schema is designed before anything ships, so no
separate migration is needed. Later schema changes to audited tables need no
audit-specific migration, because `state` is schemaless JSON. A future undo
must just tolerate snapshots that name columns which no longer exist.

**Benchmark.** `warm.grade` (§14.9) measures the audited grade. Its budget
stays as confirmed.

---

## 8. `harald check` (issue 021)

Open question 4 is resolved:
- **`check` is reachable from the CLI and from the TUI**, through a Check
  screen on Home key `k`. Nothing is shown automatically at startup, which is
  the spec rule.
- **Three repair actions per flagged card:** (a) relink to one candidate,
  (b) accept upstream changes, (c) keep the own copy and clear the flag.
- **Issue 021 is no longer blocked.**

### 8.1 Resolution and listing

Re-resolution is computed when `check` runs. Nothing runs at startup.

`resolve(word) -> Resolved(entry) | Disappeared | Ambiguous(candidates)`:
1. Candidates are the English-edition entries of headword `(lemma, pos)`. If
   there are none, the result is Disappeared.
2. If exactly one candidate's `discriminator` equals the word's, it is
   Resolved.
3. Otherwise take the candidates with that discriminator, or all candidates
   if none have it. Keep those whose senses contain every gloss of the
   word's live meaning cards verbatim. If exactly one remains, it is Resolved
   (the discriminator changed but the content identifies the entry).
   Otherwise the result is Ambiguous.

Per-card status against the resolved entry:

| Card type | Status rule |
|---|---|
| meaning (`de_en`, `en_de`) | changed unless the gloss is still present |
| `meaning_de_de` | resolved by the German group `(lemma, pos)` instead; changed unless the definition is present; disappeared if the group is gone |
| article | changed unless the gender and plural are equal |
| Stammformen | changed unless the principal parts, auxiliaries and `separable_prefix` are equal |
| phrase | never checked (Tatoeba pairs are copies; there is nothing upstream to repair them from) |

**Flag kinds.**
- **changed:** resolved, but the card's copy differs from upstream.
- **ambiguous:** two or more candidates.
- **disappeared:** no candidate under `(lemma, pos)`.

For disappeared cards, the candidate list for relinking is widened to the
same lemma under *other* parts of speech, because a re-tagged entry
(`noun` → `name`, say) is the common way an entry "disappears".

**Fingerprints and suppression.** Each status carries an upstream
fingerprint, the sha256 of canonical JSON:
- for **changed**: the upstream content of the card's type;
- for **ambiguous / disappeared**: the sorted candidate keys
  `(lemma, pos, discriminator)`, which is empty for disappeared.

A card is listed when its status is not OK **and** its stored `check_ack`
differs from the current fingerprint. So a dismissed problem stays quiet
until upstream changes again (§8.3 (c)). Cards always study from their own
copy, so a vanished or split entry changes nothing for study.

### 8.2 Hint key

`(lemma, pos, discriminator)` is captured on the `word` row **from issue 010
onwards**. The discriminator is gender plus plural for nouns (Band:
`n|Bänder`, `m|Bände`, `f|Bands`; See: `m|Seen`, `f|Seen`) and the past
participle for verbs (umfahren: `umgefahren` vs `umfahren`; übersetzen:
`übergesetzt` vs `übersetzt`).

### 8.3 Repair actions

Which actions each flag kind offers:

| Flag | (a) relink | (b) accept upstream | (c) keep own copy |
|---|---|---|---|
| changed | yes, if the headword has other candidates | **yes** | yes |
| ambiguous | **yes**, pick one candidate | only after (a), once there is one upstream | yes, marks it unlinked |
| disappeared | yes, if the same lemma exists under another pos; otherwise not offered | no, there is nothing upstream | **yes**, marks it unlinked |

Every repair runs as one use case through `DbTransaction.execute`, inside
one `OperationGroup`, so each is audited and undo-ready (§7.8). A repair can
apply to one card, or to all flagged cards of the word ("apply to all 3
cards of Leiter").

**(a) Relink.**
- **What changes:** the `word` row's hint (`lemma`, `pos`,
  `discriminator`) becomes the chosen candidate's. For a cross-pos relink of
  a disappeared word, `pos` changes too, and `meaning_de_de` cards then
  resolve against the German group of the new pos.
- **What doesn't:** the cards' own copies, FSRS state and review history.
  Relinking only says which upstream entry the copy belongs to.
- **Afterwards** the word is re-resolved immediately. If the copy differs
  from the new entry, it shows up as changed, with (b) and (c) offered.
- **Unlinked cards** (an earlier (c)) return to `linked` when relinked.

**(b) Accept upstream changes.**
- **Diff and confirmation:** always a per-field diff of copy against
  upstream (Check-detail wireframe, §12.8), and always an explicit
  confirmation. Upstream content is never taken over silently.
- **What changes:** the card's content fields are overwritten from upstream
  for its type:
  - meaning: `gloss`, `labels`, `example`;
  - `meaning_de_de`: `definition`;
  - article: `gender`, `plural`, `hint`;
  - Stammformen: `pres3sg`, `preterite`, `participle`, `auxiliaries`,
    `separable_prefix`, `hint`.

  `check_ack` is cleared, and `link_state` stays `linked`.
- **Scheduling: recommended defaults, overridable per repair.**
  - **Checked cards (article, Stammformen) where the expected answer
    changed: reset to new by default.** The interval was earned against an
    answer that is now wrong, so keeping it schedules certain failures.
    - Reset means `fsrs_state`, `step`, `stability`, `difficulty` and
      `last_review` are cleared, and `due` becomes now.
    - The card then queues as new. It does not consume the daily new-card
      cap, because the cap counts cards whose first review is today, and
      this card's first review is in the past.
    - The confirmation offers `[r] keep schedule` as the override.
  - **Self-graded cards (meaning, `meaning_de_de`): keep the schedule by
    default.** A reworded gloss rarely changes what the learner recalls. The
    confirmation offers `[r] reset schedule` as the override.
  - **Review history is never touched.** The reset's before-state is in the
    audit (§7.8). A future FSRS optimiser can split a card's history at a
    reset from those audit timestamps.

**(c) Keep own copy, clear the flag.**
- **For changed:** store the current upstream fingerprint in
  `card.check_ack`. The card is listed again only when upstream changes
  again, so the fingerprint differs.
- **For ambiguous and disappeared:** set `card.link_state = 'unlinked'` and
  store the candidate-set fingerprint in `check_ack`.
  - An unlinked card is an explicit state, not a recurring flag. It is shown
    as a count on the Check screen ("Unlinked: 1"), never as a warning.
  - It is listed again only if its candidate set changes: an entry
    reappears, or a new split or merge happens. Then (a) is offered.
  - Its content is never compared, since there is no link to compare
    against.
- **FSRS state and history** are untouched.

**Schema.** `card.link_state` (`'linked'` | `'unlinked'`, default `'linked'`)
and `card.check_ack` (nullable text) are part of `learning.db`'s v1 schema
(§7.1). The design is known now, so no later migration is needed.

### 8.4 Interfaces

**TUI.** The Check screen is reachable from Home (`k`). It lists flagged
words, then cards; opening one shows its detail with `a` / `b` / `c`, as
buttons and keys (wireframes in §12.8). The unlinked count sits at the
bottom of the list.

**CLI**, portrait-friendly: every line fits 40 columns and nothing is
tabular.
- **`harald check`**
  - Lists flagged cards grouped by word, two or three lines each: the word
    and its hint, then `card <id>  <type>  <flag>`, then a one-line diff
    summary.
  - Exits 0 when nothing is flagged and 1 when something is, so a script can
    test it.
- **`harald check --interactive`**
  - Walks the flagged cards one at a time: the diff (stacked "yours" /
    "upstream" lines, not side by side), then a line-based prompt:
    `[a]relink [b]accept [c]keep [s]kip [q]uit`.
  - For (b) it asks for confirmation, with the scheduling default shown and
    `r` to flip it.
- **Non-interactive, for scripts:**
  - `harald check accept <card-id> [--reset | --keep-schedule]`
  - `harald check keep <card-id>`
  - `harald check relink <card-id> --to <lemma>|<pos>|<discriminator>`. A
    candidate is named by its hint key, since entry ids are not stable
    across builds.

  Each prints the resulting state and exits 0, or exits 1 with the reason
  (for example, "not flagged" or "no such candidate").

**Changes issue 021's acceptance criteria need** (listed for the user, not
edited):
1. `check` is reachable from the CLI and from the TUI (Home → Check), and
   still nothing is shown at startup.
2. Each flagged card offers the actions its flag allows (the table in §8.3):
   relink, accept upstream, keep own copy.
3. Accept shows a per-field diff and requires confirmation. By default,
   checked cards whose answer changed reset their schedule and self-graded
   cards keep theirs, both overridable. Review history is never modified.
4. Keep on an ambiguous or disappeared card makes it unlinked. Unlinked
   cards are re-listed only when their candidate set changes. Kept changed
   cards are re-listed only when upstream changes again.
5. Every repair is recorded in the audit trail as one operation group.
6. The CLI has a listing mode (exit 1 when anything is flagged), an
   interactive mode, and per-card subcommands. All output fits 40 columns.

---

## 9. `$EDITOR` template (issues 017, 020)

`edit_fields(fields: list[FieldSpec], values: dict, validate) -> Result[Option[dict[str, str]], EditorFailed]`
in `harald/editor.py` (§14.10). `Ok(Option.none())` means the user cancelled, which is an
outcome, not an error. `validate` is `Callable[[dict[str, str]], Result[T,
InvalidInput]]`, and an `InvalidInput` message becomes the `# ERROR:` line. Its two callers are phrase entry and card editing, and
whichever of issues 017 and 020 lands first creates it.

- **Template**: `# ` comment lines (instructions; an `# ERROR: …` line at the
  top on a reopen), then one `Label: value` line per field. Lines that are
  neither comments nor labels continue the previous field.
- **Phrase template**: `English:`, `German:`, `Note:`. The search query is
  included as a comment for reference. It is not put into a field, because
  the query's language is unknown.
- **Editor command**: `$VISUAL`, then `$EDITOR`, then `vi`, split with
  `shlex.split`, like git. The temp file is `<tmp>/harald/EDIT.txt`, where
  `<tmp>` is `$XDG_RUNTIME_DIR` if set, else `tempfile.gettempdir()` (which
  honours Termux's `$TMPDIR`). It is deleted afterwards.
- **Cancel** when the saved text is byte-identical to what was written
  ("unchanged"), or when every field is blank after removing comments
  ("empty").
- **Validation failure** (for phrases, English or German missing): rewrite
  the file with `# ERROR: German is missing.` at the top and the user's text
  kept, then reopen.
- **A missing editor binary** (`FileNotFoundError`, caught by type) or a
  non-zero exit returns `Err(EditorFailed(command, detail))`.
- **In the TUI**, the whole loop, reopens included, runs inside one
  `with app.suspend():`, so the TUI doesn't flash between reopens. The phrase
  and its card are then created in one transaction.

---

## 10. Backup (issue 022)

- `backup(ldb, config, now) -> Result[Path, BackupError]`, where the error is
  `BackupNotConfigured` or `BackupFailed(detail)`
  (`sqlalchemy.exc.SQLAlchemyError` and `OSError` caught by type).
- `VACUUM INTO '<backup_dir>/.learning-<stamp>.db.partial'`, run with
  `exec_driver_sql` on an engine connection set to
  `isolation_level="AUTOCOMMIT"` (VACUUM cannot run inside a transaction),
  then fsync, then
  `os.replace` to `learning-<stamp>.db`. The temp file sits in the same directory
  because it must share a filesystem with the destination. Only complete
  files ever carry the final name. Recommend `*.partial` in the folder's
  `.stignore`.
- Prune to the newest `backup_keep` copies.
- Nothing ever reads the backup folder.
- **Trigger points (confirmed by the user)**: after each study
  session's summary and on TUI exit, if any write happened since the last
  backup; plus `harald backup` on demand. Default `backup_keep = 10`. When
  `backup_dir` is unset, backup is off and `harald backup` explains how to
  set it.

---

## 11. CLI (`harald/cli.py`, click)

**Two entry points (revised 2026-10-25, a finding from reviewing 009).** `harald-cli`
is the click CLI (`harald.cli:main`); `harald` is the TUI (`harald.tui.main:main`).
A bare `harald-cli` prints usage. Everywhere else in this document, `harald <command>`
for `lookup`, `phrase`, `build`, `info`, `check`, `backup` means `harald-cli <command>`.

| Command | Purpose | Notes |
|---|---|---|
| `harald` | TUI | its own entry point, not a subcommand of `harald-cli` |
| `harald-cli lookup [--en] [--conj] WORD…` | one-shot lookup | words are joined with spaces (`ruft an`); exit 1 on no match |
| `harald-cli phrase TEXT…` | phrase search | required from the CLI by issue 018 |
| `harald-cli build [--fetch] [--force]` | desktop build | prints sources, coverage, the unmapped count, task timings and db size; exit 1 on any `BuildError` |
| `harald-cli check [--interactive]`; `harald check accept\|keep\|relink <card-id> …` | §8.4 | lists flagged cards (exit 1 if any); interactive line prompts; per-card scripted repairs; 40-column output |
| `harald-cli backup` | §10 | |
| `harald-cli info` | versions, paths, sources with date, licence and attribution, coverage | the spec's "Harald displays the sources…" |

- Global options: `--config PATH`, or the `HARALD_CONFIG` environment
  variable (click's `envvar=`; an empty value counts as unset, as before).
- Exit codes:
  - 0 for success;
  - 1 when the operation failed;
  - 2 for a refusal (config error, missing lexicon, schema mismatch, newer
    `learning.db`) and for a usage error;
  - 130 on Ctrl-C.

  Refusals and failures come from one `exit_code(err)` match on the error's
  class (§14.2). §11.1 says how click is made to keep these codes.
- **Imports are lazy per subcommand.**
  - `lookup` and `phrase` import `click`, `sqlalchemy` (Core and ORM),
    `harald.use_cases.lexicon`, `harald.lexicon` (`models`,
    `lookup`/`phrases`) and `rich`, and nothing else heavy: not `textual`,
    `fsrs`, `alembic`, `harald.learning` or `harald.build`. `lookup` never
    opens `learning.db`, so it never reaches the migration path.
  - The TUI imports `sqlalchemy.orm` and both model sets, but `alembic` only
    when it migrates.
- **Trimming the ORM's cold cost: measured, and little is left to win**
  (§0):
  - importing `sqlalchemy.orm` is about 70% of the ORM's extra cold cost;
  - defining and configuring the mapped classes is about 13%;
  - compiling the first statements is about 12%.

  None of that can be cached across processes. So the trimming worth doing is
  hygiene:
  - keep `harald.learning.models` out of `lookup`. It is a separate registry, so
    its mappers are never configured there;
  - declare relationships `lazy="raise"` with explicit loaders, which costs
    nothing at startup and prevents N+1 queries;
  - install with compiled bytecode (`uv tool install --compile-bytecode`), so
    the phone's first run doesn't compile SQLAlchemy's modules.
- **Import-hygiene test** (deterministic, not timed): run `harald lookup` in
  a subprocess and assert that `textual`, `alembic`, `fsrs`, `harald.learning` and
  `harald.build` are absent from `sys.modules`. The timings themselves belong
  to the benchmark harness (§14.9).

### 11.1 click (revised 2026-10-20, confirmed by the user 2026-10-24)

The CLI uses click, as kohle does, by the user's decision. The earlier
revision chose argparse to keep click's import off the one-shot `lookup`
(§14.8).
- Measured (§0), that import costs about 10 ms on top of what `lookup`
  already loads (`rich`, `sqlalchemy.orm`), which is inside run-to-run
  noise.
- click is a pure-Python wheel, so the phone rule (§2) holds.

**Shape of `cli.py`:**
- **`cli` is a `click.group()`** with the `--config` option:
  `type=click.Path(dir_okay=False, path_type=Path)`,
  `envvar="HARALD_CONFIG"`, and no `exists=True`. Its callback only stores
  the path in `ctx.obj`.
  - *Why not load the config in the callback:* click runs the group
    callback before the subcommand parses its arguments. A broken config
    would then break `harald lookup --help`. kohle defers opening its
    ledger for the same reason (its `_LedgerCommand`).
  - *Why no `exists=True`:* `load_config` stays the one place that judges
    the file, with its own message and exit code 2.
- **Each command is a `@cli.command()` function** taking `@click.pass_obj`.
  - It loads the config, opens the handles it needs (`open_lexicon`; later
    `open_learning_db`), calls one use case (§11.2), renders, and **returns
    an `int` exit code**.
  - Failures go through the existing `_fail(err) -> int`, which prints
    `str(err)` to stderr and returns `_exit_code(err)`.
  - Commands never call `ctx.exit()` or `sys.exit()`. click's own source
    warns that mixing `return 1` with `ctx.exit(1)` makes non-standalone
    results ambiguous.
- **Options are as now:** `build --fetch --force`, and `lookup --conj
  WORD…` (`nargs=-1, required=True`). Later come `lookup --en`, `phrase
  TEXT…`, `backup`, and `check` as a nested `click.group` with `accept`,
  `keep` and `relink` (§8.4). Nested groups are one of the things click
  makes simpler than argparse's nested subparsers.
- **Imports stay lazy inside each command function**, as now. At the top,
  `cli.py` imports only `click`, `harald.config`, `harald.core.result` and
  the error modules.
- **`main(argv: Sequence[str] | None = None) -> int` stays the entry
  point.** `[project.scripts] harald = "harald.cli:main"` and `__main__.py`
  are unchanged.
  - It calls `cli.main(args=argv, prog_name="harald",
    standalone_mode=False)` and returns its result: the command's `int`, or
    0 for `--help`.
  - It catches `click.ClickException`, which covers usage errors including
    a missing subcommand. It calls `e.show()` and returns `e.exit_code`,
    which is 2, as argparse gave.
  - It catches `click.Abort` and returns 130. click converts
    `KeyboardInterrupt` into `Abort` before it reaches `main`, so this is
    now where Ctrl-C's 130 comes from. Cleanup still runs first, in the
    build's `finally` blocks (§3.5).
  - `EOFError` becomes `Abort` too. The only v1 command that reads stdin is
    `check --interactive`, and it treats EOF as quit itself (issue 021).
- **The TUI entry point (issue 009, revised 2026-10-25).** `harald` is a
  separate console script, `harald.tui.main:main`, with its own small click
  command taking only `--config`/`HARALD_CONFIG`.
  - It loads the config, checks the lexicon through `QueryLexiconInfo`,
    prints any refusal (exit 2), and only then imports `harald.tui.app` and
    runs `HaraldApp`. Textual is therefore never imported by `harald-cli`, or
    by a refused start.
  - The first cut of 009 made a bare `harald` start the TUI from inside the
    click group (`invoke_without_command=True`, plus a `tui` subcommand). That
    was reversed: one binary doing two jobs hid the CLI's usage text and tied
    the CLI's import cost to Textual.
  - `python -m harald` runs the CLI; `python -m harald.tui` runs the TUI.
- **Output.** Plain lines go through `click.echo` (with `err=True` for
  stderr). Renderables go through a Rich `Console()` created in the
  command, as now, so Rich still sizes them from `COLUMNS` and the terminal.

```python
@cli.command()
@click.option("--conj", is_flag=True, help="show every tense")
@click.argument("words", nargs=-1, required=True, metavar="WORD...")
@click.pass_obj
def lookup(config_path: Path | None, conj: bool, words: tuple[str, ...]) -> int:
    from harald.render import render_lookup
    from harald.use_cases.lexicon import LookUpGerman

    opened = _open_lexicon(config_path)  # load_config, then open_lexicon
    if opened.is_err:
        return _fail(opened.unwrap_err())
    query = " ".join(words)
    result = LookUpGerman(opened.unwrap()).execute(query)
    if not result.shown:
        click.echo(f"No match for {query!r}", err=True)
        return _EXIT_FAILED
    _print(render_lookup(result, conj))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        code: int = cli.main(args=argv, prog_name="harald", standalone_mode=False)
        return code
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except click.Abort:  # click's form of KeyboardInterrupt
        return _EXIT_INTERRUPTED
```

### 11.2 Use cases: what front-ends call (revised 2026-10-20, confirmed by the user 2026-10-24)

The user chose kohle's layering: front-ends call use cases, never the
lower-level modules. kohle's AGENTS.md states it as `app` → `use_cases` →
`services` → `infrastructure` / `domain`. Use cases validate and compose.
Services own persistence and are the only layer that touches a `Session`.
On Harald's packages that becomes:

| Layer | kohle | Harald | Touches |
|---|---|---|---|
| Front-ends | `app/cli`, `app/tui` | `cli.py`, `tui/` | input, output and exit codes; opens the handles (config, `Lexicon`, `LearningDb`) |
| Use cases | `use_cases/` | `use_cases/` (new) | nothing directly: they call services and decide |
| Services | `services/` | `lexicon/` (`lexicon.db` reads), `learning/` (`*_service(ctx, …)`, from 010), `build/` (the importer) | sessions, connections, files, the process pool |
| Below | `infrastructure/`, `domain/`, `core/`, `db/` | `infrastructure/` (from 010), `core/`, `db/`, `text.py`, each package's model and error modules | – |

`render.py` sits beside the front-ends, which pass it what use cases return.

**Rules:**
- **What front-ends import.** From `harald`, only:
  - `harald.use_cases.*`, `harald.render`, `harald.config` and
    `harald.core.result`;
  - the open functions and handle types: `harald.lexicon.db`, and later
    `harald.learning.db`;
  - the error modules, for `exit_code`;
  - `harald.lexicon.model`, for types only;
  - `harald.editor`, from issue 017.

  A static test holds this (§11.3).
- **Every use case has one call shape: `X(handles).execute(values)`.** This
  is the user's decision (2026-10-24). It is kohle's `UnitOfWork` call
  shape, `AddUnit(make_session()).execute(identifier, name, kind)`, used
  for every use case a front-end calls, transactional or not.
  - **The constructor takes the handles.** That is a fresh session from
    `LearningDb` for a `UnitOfWork` subclass, as kohle's CLI does; a
    `Lexicon` for the lexicon use cases; and the `Config` for
    `BuildLexicon`, the one use case that needs most of it.
  - **`execute` takes the values:** the query, the picked senses, the card
    id and rating, the flags. `now` is always an `execute` argument
    (§7.4).
  - Use cases never call `load_config`, read the environment, or open a
    database the front-end could have opened.
  - One exception follows kohle's `init_ledger`, which opens its own engine
    because deciding which file to open is its job: `BuildLexicon` opens
    the lexicon it has just published.
  - Front-ends construct a use case for each action, as kohle's CLI does,
    and don't keep it.
- **Two kinds of class.**
  - A use case that runs a `learning.db` transaction is a `UnitOfWork`
    subclass (§7.7). Its `execute` builds the closure and calls
    `self._run`, exactly as kohle's do.
  - Any other use case is a plain class whose `__init__` stores its handles,
    plus an `execute`. `lexicon.db` is read-only and immutable, so there is
    no transaction to scope, and `harald.lexicon` already opens and closes
    its own short sessions (§4.4). The build keeps its own boundaries
    (§3.5).
  - There is no base class or `Protocol` for the plain ones. Nothing calls
    use cases generically, so the shared shape is a convention. `UnitOfWork`
    exists only because it carries the transaction.
  - **This departs from kohle in one place.** kohle writes its
    non-transactional use cases as functions (`init_ledger`,
    `call_price_plugins`). Harald uses classes there too, so a front-end
    reads one shape everywhere.
- **Names are verb phrases**, as kohle's are: `LookUpGerman`,
  `BuildLexicon`, `CreateWordCards`, `Grade`.
  - The info read is `QueryLexiconInfo`, not `LexiconInfo`, because
    `LexiconInfo` is already the dataclass it returns (`lexicon/model.py`).
  - `Query…` is kohle's prefix for reads of that kind (`QueryPositions`,
    `QueryJournalByPeriod`).
- **One module per area, and no shared import.**
  - The CLI imports a use-case class lazily, inside the command that needs
    it (`from harald.use_cases.lexicon import LookUpGerman`). So a module's
    imports are what its commands pay for at startup.
  - So `lexicon.db` read use cases never share a module with `learning.db`
    or build ones, and `use_cases/__init__.py` stays empty, with no
    re-exports.
  - Otherwise `lookup` would import `harald.build` or `harald.learning` and
    fail the import-hygiene test (§11).
- **Use cases return what their services return:** dataclasses from
  `lexicon/model.py`, kohle-style mapped objects from `learning/`, and
  `Result` only where something can fail (§14.2). Rendering stays in the
  front-ends.
- **Use cases that only forward are still written.** `LookUpGerman` and
  `QueryLexiconInfo` add almost nothing today. They exist for three reasons:
  - the rule is that front-ends call use cases, which is the user's choice
    and kohle's practice (kohle's `ListUnits` and `ListOperations` only
    forward too);
  - the TUI (009) is a second caller that must get the same result;
  - when issues 006–008 make lookup richer, the change lands below them.

**Commands, screens and their use cases.** Use cases for features not yet
built get indicative names; the issue that builds each one fixes the name.

| Entry point | Use case | Module | Calls |
|---|---|---|---|
| `harald lookup [--conj] WORD…`; TUI Lookup (009) | `LookUpGerman(lex).execute(query) -> LookupResult` | `use_cases/lexicon.py` | `lexicon.lookup.lookup_de` |
| `harald info`; TUI Info | `QueryLexiconInfo(lex).execute() -> LexiconInfo` | `use_cases/lexicon.py` | `lexicon.info.load_info(lex, SCHEMA_VERSION)` |
| `harald build [--fetch] [--force]` | `BuildLexicon(config).execute(fetch, force) -> Result[BuildDone, BuildError \| LexiconError]` | `use_cases/build.py` | `build.run.build`, then `open_lexicon` and `QueryLexiconInfo` |
| `harald lookup --en` (008); TUI EN mode | `LookUpEnglish(lex).execute(query)` | `use_cases/lexicon.py` | `lexicon.lookup.lookup_en` |
| TUI Entry for an "Also" result (009) | `LoadHeadword(lex).execute(lemma, pos)` | `use_cases/lexicon.py` | `lexicon.lookup.load_headword` |
| `harald phrase TEXT…` (018); TUI Phrases | `FindPhrases(lex).execute(text)` | `use_cases/lexicon.py` | `lexicon.phrases.search_phrases` |
| TUI Add word, phrase saving, Cards (010–020) | `PlanWordCards(lex)` (§7.3); `CreateWordCards`, `SavePhrase`, `EditCard`, `SetSuspended`, `DeleteCard`, each `X(ldb.session())` | `use_cases/cards.py` | `learning.cards` services |
| TUI Study (010, 015) | `NextCard`, `Grade`, `SessionSummary`, each `X(ldb.session())` | `use_cases/study.py` | `learning.study` services |
| TUI Decks (016) | `CreateDeck`, `DeleteDeck`, `SetDeckMembership`, each `X(ldb.session())` | `use_cases/decks.py` | `learning.decks` services |
| `harald check …` (021); TUI Check | one class for the listing and one for each of the three repairs (§8.3), each `X(ldb.session())` | `use_cases/check.py` | `learning.check`, card services |
| `harald backup` (022); after sessions and on exit | `BackUp(ldb).execute(...)`, a plain class: `VACUUM INTO` runs outside a transaction (§10) | `use_cases/backup.py` | `learning.backup` |

The refactor slice builds only the first three rows (§11.3). The other rows
say where each later issue puts its use cases. Their signatures are the
ones designed in §7–§10.

**`BuildLexicon`.** The CLI used to run the build, then open the lexicon
and print its info. That composition moves into the use case.
- On success its `execute` returns `BuildDone(report: BuildReport, info:
  LexiconInfo)`.
- If the build returns `Err`, nothing is opened.
- **The build itself stays in `harald.build.run.build`, unchanged:**
  - it is the importer's sequence that carries the rebuild guarantees
    (§3.5);
  - the 004a and 004b tests drive it as one unit;
  - it is a broad-catch seam named in AGENTS.md's Override.
- Opening the lexicon afterwards is a read after the publish, not part of
  it (§14.1).

### 11.3 Landing it: a refactor slice before issue 006

- **This goes through the `change` door, not a spec issue.** Nothing a
  user can see changes except help text and the wording of usage errors.
- It lands after 005 and before 006. Issues 006–008 then extend lookup
  below a use case instead of inside `cli.py`.

**Order, each step green on its own:**
1. Add `click>=8.3,<9` to `[project] dependencies` and refresh `uv.lock`.
2. **Add `Option`** (§14.10, confirmed by the user 2026-10-24):
   - `harald/core/option.py`, with `tests/unit/test_option.py` and
     `tests/unit/test_result.py`;
   - convert `Jobs._reap` in `build/graph.py` from `BuildError | None` to
     `Result[None, BuildError]`;
   - add `enable_error_code = ["truthy-bool"]` to `[tool.mypy]`, which
     today's code already passes.

   Nothing else converts. Every other `T | None` in today's code falls
   under a keep rule of §14.10.
3. Add `harald/use_cases/` with its tests (below): an empty `__init__.py`,
   `lexicon.py` (`LookUpGerman`, `QueryLexiconInfo`) and `build.py`
   (`BuildLexicon`, `BuildDone`). `cli.py` is untouched, so every existing
   test still passes.
4. Rewrite `cli.py` on click (§11.1), calling only the use cases. The smoke
   tests are the regression net and must pass **unmodified**. Add the new
   CLI tests and the layering test.

**What the first build after the slice does.** The fingerprint covers every
`.py` file of the package (§3.5 step 5), so the first `harald build` after
this slice misses the fast path. It runs the graph for a few minutes, finds
the bytes identical, and leaves the published file untouched. That is
expected, not a regression, and Syncthing has nothing to send.

**Tests:**
- **Unchanged, and the contract for the switch:** the subprocess smoke
  tests in `tests/smoke/test_lookup_flow.py` and `test_conjugation_flow.py`.
  They check exit codes 0, 1 and 2, the stderr messages they match on, and
  output within 40 columns. The import-hygiene test also stays as it is: it
  calls `main([...])` in-process, and that signature is kept.
- **Unchanged, at the service layer:**
  - `tests/component/test_build.py`, `test_fetch.py` and
    `test_lexicon_queries.py` keep calling `build`, `fetch_all` and
    `lookup_de` directly. Services keep their own tests, as in kohle, where
    `test_*_services.py` sits beside `test_*_use_cases.py`.
  - The `built` fixture keeps calling `harald.build.run.build`.
  - `test_only_the_importer_reads_source_files` now also scans
    `use_cases/`, which must not mention `gzip` or `jsonl`.
- **New, for the use cases** (named like the existing
  `test_card_use_cases.py`):
  - `tests/component/test_build_use_cases.py`:
    - `BuildLexicon(config).execute(fetch=False, force=False)` returns the
      report and the info: sources in name order and the three coverage
      figures;
    - with the source file missing, it returns `SourceMissing` and opens
      nothing.
  - `tests/component/test_lexicon_use_cases.py`:
    - `LookUpGerman(lex).execute("Hund")` finds Hund;
    - `QueryLexiconInfo(lex).execute()` reports `SCHEMA_VERSION`;
    - the per-source date rule of §3.6, which no test pins today. Edit the
      `source_file` rows of a built lexicon before opening it. A source
      with dates `2026-10-01`, `2026-10-17` and `unknown` shows
      `2026-10-17`; one with only `unknown` shows `unknown`.
- **New, for the CLI** (in `tests/smoke/`):
  - `harald lookup --help` exits 0 with a config file that doesn't parse;
  - `HARALD_CONFIG` is honoured when `--config` is absent;
  - an unknown subcommand exits 2, and a bare `harald-cli` prints usage rather than starting the TUI;
  - Ctrl-C exits 130. Test it in-process: monkeypatch `execute` on
    `harald.use_cases.build.BuildLexicon` to raise `KeyboardInterrupt`,
    then call `main(["--config", …, "build"])`. This guards the `Abort` →
    130 mapping, which click would otherwise turn into exit 1.
- **New, for `Option` and `Result`:** `tests/unit/test_option.py` and
  `tests/unit/test_result.py`, as listed in §14.10. The existing build
  tests cover `_reap`'s conversion.
- **New, for the layering:** `tests/unit/test_layering.py`.
  - It parses `src/harald/cli.py` with `ast`, plus every file under
    `src/harald/tui/` once that exists.
  - It collects every `import harald…` and `from harald… import`, including
    the lazy ones inside functions.
  - It asserts each one is in the front-end allow-list of §11.2.
  - kohle holds a comparable rule the same way: a test forbids
    `journal.py` from touching prices.

---

## 12. TUI (`harald/tui/`)

A single `HaraldApp` with a screen stack. `cli` opens `Lexicon` and
`LearningDb` first, prints any refusal, and only then starts the app.
Screens call use cases (§11.2) with the handles the app owns. They never
call `harald.lexicon` or `harald.learning` directly.

| Screen | Keys / content |
|---|---|
| Home | `l` lookup, `e` English → German, `p` phrases, `s` study, `c` cards, `d` decks, `k` check, `i` info, `q` quit |
| Lookup | one screen, DE/EN modes toggled by `^t`; Input; search runs **on Enter**, not on every keystroke; result list; Enter opens Entry |
| Entry | scrollable `render_headword`; `c` full conjugation; `a` add word (Pick-entry modal first when the headword has several English entries) |
| Add word | three-step wizard: 1 English-sense `SelectionList`, 2 German-sense `SelectionList`, 3 automatic-card status (created / refused with missing forms), decks, Create |
| Study | pick "all due" or a deck; self-graded: space or the Show button reveals, `1`–`4` or buttons grade; article: `1`/`2`/`3` or buttons; Stammformen: three compact Inputs and Enter; feedback, then Enter, space or Next; Esc ends; summary screen |
| Phrases | Input, results; Enter saves the pair after confirmation; `^n` writes your own pair in `$EDITOR` |
| Cards | table of live cards; `/` filter; `e` edit (`$EDITOR`), `s` suspend toggle, `x` delete (confirm), `d` decks |
| Decks | list, create, delete |
| Info | `render_info` |
| Check | flagged words, then cards; detail with diff; `a` relink, `b` accept (confirm, `r` flips the schedule default), `c` keep (§8) |

The layout targets 80×24, with a supported floor of 80×12 (keyboard up). No
screen needs more than one column of widgets. §12.1–12.7 give the
conventions, the navigation map, wireframes for every screen, the
reduced-height rules, and the touch decision.

### 12.1 Screen conventions: header, body, footer, keys

- **Three bands.** Row 1 is the header, the last row is the footer, and the
  body is everything between (22 rows at 80×24).
- **Header.** Textual's built-in `Header` (one row, `tall=False`, icon
  blanked) shows `<screen> - <context>`, set through `Screen.title` /
  `sub_title`. The context is the lookup mode, the headword (`Band - noun`),
  the remaining study counts (`12 due, 8 new left`) or a count (`341 live`).
- **Footer.** `Footer(compact=True)` lists the bindings active in the current
  state, primary action first and `esc` last: at most about six at 80
  columns, three or four at 40, with `?` opening the full list (§12.8). Keys appear the way Textual prints them (`enter`, `esc`,
  `^t`). The footer changes with state: study shows `space Show` before the
  reveal and `1 Again … 4 Easy` after it. Bindings already shown elsewhere on
  the screen (the Home menu letters) are `show=False`.
- **Footer keys are tappable.** Textual's `FooterKey.on_mouse_down` simulates
  the key, so every footer hint is also a touch target. This is checked in
  the Textual 8.2.8 source.
- **Command palette off** (`ENABLE_COMMAND_PALETTE = False`). It duplicates
  the menu and footer. On a phone, its header icon is a stray tap target that
  opens a full-screen search. Turning it off also frees `ctrl+p`.
- **Global keys.** `esc` goes back one level (pops the screen, closes a modal,
  cancels the Add-word wizard, or ends a study session early with its
  summary). `ctrl+q` quits from anywhere (Textual's default). `q` also quits
  on Home.
- **Focus rule for keys.** Screens with a text `Input` bind their actions only
  to non-printing keys: `enter`, `esc`, `tab`, arrows, `ctrl+t`, `ctrl+n`.
  Letter keys are used only where no Input has focus. The reason: an Input
  consumes printable keys, so a letter binding would either never fire or,
  if made a priority binding, swallow letters the user types. The Ctrl keys
  were chosen to avoid the Input's own editing keys (`ctrl+a/e/d/w/u/k/x/c/v`),
  the app's (`ctrl+q`, `ctrl+c`), and `ctrl+s`/`ctrl+z` (flow control and
  process suspend in terminals). On the phone, Ctrl comes from Termux's
  extra-keys row, or the user taps the footer hint.
- **Body.** One column, never side-by-side panes. At 80 columns a list beside
  a preview leaves neither readable.
  - Content views (Entry, Study) wrap text and never truncate it.
  - The Cards table truncates long fronts with `...`.
  - Sense pickers wrap, because the user has to read a definition to choose
    it.
  - `Input`s are always `compact` (one row).
  - `Button`s are three-row bordered at normal height and compact in the
    short layout (§12.4).
- **Results of an action** are reported with `notify()` toasts, for example
  "6 cards created. Stammformen refused - missing: Präteritum."

### 12.2 Navigation map

```
Home
 +- l ---> Lookup (DE) --enter--> Entry --a--> [Pick entry]* --> Add word
 +- e ---> Lookup (EN)            |                                1 EN senses
 |          ^t toggles DE/EN      +- c: full conjugation           | n (b: back)
 |          EN: enter on a German word --> Entry                   2 DE defs
 |                                                                 | n (b: back)
 |                                                                 3 Confirm
 |                                                                 |c create
 |                                                                 v Entry
 +- p ---> Phrases --enter on pair--> [Save phrase] --> Phrases
 |           +- ^n --> $EDITOR (app suspended) --> Phrases
 +- s ---> Study start --enter--> card <-> feedback ... --> Summary
 |                                (esc ends early)            | enter --> Home
 +- c ---> Cards  --e--> $EDITOR (suspended)   --d--> [Deck membership]
 |                --x--> [Confirm delete]       --/--> filter Input
 +- d ---> Decks  --n--> [New deck]   --x--> [Confirm delete]
 +- k ---> Check  --enter--> detail: a relink / b accept / c keep
 +- i ---> Info

 [..] modal over the current screen     * only when the headword has more
                                          than one English-edition entry
 n / b: next / back step (letter keys, not Ctrl).  esc: back one level
 everywhere (closes a modal, cancels the whole Add-word wizard, ends a study
 session early with its summary).  ctrl+q: quit.
```

### 12.3 Wireframes at 80×24

Every frame below is exactly 80 columns by 24 rows: the wide layout for desktop and SSH (portrait frames are in §12.8). A script generated and
checked them; no line exceeds 80 cells. Row 1 is the header, row 24 the
footer. Content is illustrative: real Band and laufen data where §0 checked
it, and `<…>` placeholders where it didn't. The checkboxes, buttons and list
cursor `>` stand in for Textual's own glyphs. Study figures are made up.

```
         1         2         3         4         5         6         7         8
12345678901234567890123456789012345678901234567890123456789012345678901234567890
```

**Home.** An `OptionList` menu. Its letters are bindings, and tapping or
Enter on an item opens it.

```
==================================== Harald ====================================

  Due now 12      New left today 8 of 20      Cards 341      Phrases 27
  Lexicon: schema 4, Wiktionary 2026-10-03, Tatoeba 2026-10-17

  > l   Look up a German word
    e   English -> German
    p   Phrases
    s   Study
    c   Cards
    d   Decks
    k   Check after a rebuild
    i   Info










enter Open   q Quit   ? Keys
```

**Lookup, German mode.**
- One screen with two modes, toggled by `^t`; Home's `l` and `e` open it in
  either mode.
- Enter in the Input runs the search (§14.3: on Enter, not per keystroke)
  and moves focus to the first result. Enter or a tap on a result opens
  Entry.
- `tab` or `↑` from the first row returns to the Input.
- The third column says how each result matched: an inflected form
  (`form: lief`) or a fuzzy distance (`~1`).

```
=============================== Lookup - Deutsch ===============================
 DE > lief_
 ------------------------------------------------------------------------------
 > laufen                verb      form: lief
   Lauf                  noun      ~1
   Brief                 noun      ~1
   lieb                  adj       ~1
   Lied                  noun      ~1
   Liefer-               prefix    ~2
   ...













enter Open   ^t DE/EN   tab List/Input   esc Back
```

**Lookup, English → German mode.**
- English words and sense groups are disabled rows (not selectable). The
  German words are the selectable rows.
- Enter on one runs `lookup_de` on it. If it resolves to exactly one
  distance-0 headword, Entry opens directly. Otherwise the screen switches to
  German mode with that query.

```
========================== Lookup - English -> German ==========================
 EN > use_
 ------------------------------------------------------------------------------
   use (verb)
     employ, apply
 >     benutzen
       verwenden
       gebrauchen
       nutzen
     to exhaust the supply of, to consume
       verbrauchen
     to exploit
       ausnutzen
       zum Vorwand nehmen        (use as a pretext)
   use (noun)
     act of using
       die Benutzung
       die Anwendung
       der Gebrauch
   ...



enter Open word   ^t DE/EN   tab List/Input   esc Back
```

**Entry, noun with several entries.** A `VerticalScroll` of
`render_headword`; swipe or PgUp/PgDn scrolls. The German examples block
follows the German definitions further down.

```
================================= Band - noun ==================================
 das Band   pl. Bänder   [bant]
   1. tape, ribbon
   2. A ligament
   3. band or tie holding items together
   4. belt (conveyor belt, fan belt, etc.)
   5. band of the spectrum
   6. [figuratively] intimate bond to a person
   7. [figuratively] dependence, social bond
   8. [poetic] shackle
 der Band   pl. Bände
   1. volume, a single book, chiefly when part of a larger set
      <German example> - <English translation>
   2. volume of a multi-volume publication
 die Band   pl. Bands
   1. modern music band
 German definitions (de.wiktionary)
   das Band
     [1] dasjenige, was verbindet oder verknüpft
     [2] zumeist aus einem bestimmten Gewebe/Stoff bestehendes längeres,
         schmales, streifenartiges Stück, ...                   (scrolls)


a Add word   esc Back
```

**Entry, verb.** The default conjugation table (§6). `c` toggles the full set
of tables.

```
================================ laufen - verb =================================
 laufen   [ˈlaʊfən]   läuft / lief / ist gelaufen
   1. [transitive, intransitive] to walk; to jog; to run (to move on foot;
      either at a normal or an increased speed)
      Wir können mit dem Bus fahren oder laufen. - We could take the bus or
      walk.
   2. [intransitive] (of a fluid) to flow; to leak; to run
   ...                                                        (scrolls)
 Indikativ
              Präsens            Präteritum         Perfekt
   ich        laufe              lief               bin gelaufen
   du         läufst             liefst             bist gelaufen
   er/sie/es  läuft              lief               ist gelaufen
   wir        laufen             liefen             sind gelaufen
   ihr        lauft              lieft              seid gelaufen
   sie/Sie    laufen             liefen             sind gelaufen
 Imperativ: lauf(e)! / lauft!






a Add word   c Full conjugation   esc Back
```

**Pick entry**: a modal over Entry, shown by `a` only when the headword has
more than one English-edition entry. Each row shows the discriminator and the
first gloss, so homographs can be told apart.
German-edition-only headwords go straight to wizard step 2.

```
            +------------------ Add which entry? ------------------+
            | > das Band   pl. Bänder   tape, ribbon                |
            |   der Band   pl. Bände    volume, a single book, ...  |
            |   die Band   pl. Bands    modern music band           |
            +-----------------------------------------------------+
```

**Add word, a three-step wizard** (why a wizard: §12.6).
- Nothing is written until Create, which runs one transaction (§7.3). Back
  and Cancel are therefore free.
- A step with nothing to pick is skipped.
- The buttons docked at the bottom of the body mirror the keys.

Step 1, English senses:

```
======================= Add word - das Band (pl. Bänder) =======================
 Step 1 of 3: English senses (each gives a de->en and an en->de card)
 ------------------------------------------------------------------------------
 [X] 1. tape, ribbon
 [ ] 2. A ligament
 [X] 3. band or tie holding items together
 [ ] 4. belt (conveyor belt, fan belt, etc.)
 [ ] 5. band of the spectrum
 [ ] 6. [figuratively] intimate bond to a person
 [ ] 7. [figuratively] dependence, social bond
 [ ] 8. [poetic] shackle





 2 selected
+-------------------------------------+ +-------------------------------------+
|                Cancel               | |                Next >               |
+-------------------------------------+ +-------------------------------------+



space Toggle   n Next   esc Cancel
```

Step 2, German definitions, grouped by German-edition entry. Headings
(senses without a `sense_index`) are disabled rows.

```
======================= Add word - das Band (pl. Bänder) =======================
 Step 2 of 3: German definitions (each gives a de->de card)
 ------------------------------------------------------------------------------
     das Band
 [ ] [1] dasjenige, was verbindet oder verknüpft
 [X] [2] zumeist aus einem bestimmten Gewebe/Stoff bestehendes längeres,
         schmales, streifenartiges Stück, das verwendet wird als Schmuck/...
         Plural »Bänder«:                                (heading, not pickable)
 [ ] [3] [colloquial, figurative] intime Freundin
     ...
     der Band
 [ ] [1] (zumeist größeres) gebundenes Buch
 [ ] [2] einzelnes Buch, das Teil einer Buchreihe oder eines größeren
         Werks (Gesamtausgabe) ... ist
     die Band
 [ ] [1] Gruppe von Musikern (besonders im Bereich des Jazz und der Rockmusik)
 1 selected
+-------------------------------------+ +-------------------------------------+
|                < Back               | |                Next >               |
+-------------------------------------+ +-------------------------------------+



space Toggle   n Next   b Back   esc Cancel
```

Step 3: automatic cards, refusals, decks, and the total.

```
======================= Add word - das Band (pl. Bänder) =======================
 Step 3 of 3: Confirm
 ------------------------------------------------------------------------------
 Cards to create
   2 x German -> English, 2 x English -> German   senses 1, 3
   1 x German -> German                           [2] (das Band)
   1 x Article                                    das
 Refused
   none            (e.g. for a verb: Stammformen - missing: Präteritum, aux)
 Decks
 [ ] Haushalt
 [X] Lesen: Kafka
 [ ] Serie: Dark




+-------------------------------------+ +-------------------------------------+
|                < Back               | |            Create 6 cards           |
+-------------------------------------+ +-------------------------------------+



space Toggle   c Create   b Back   esc Cancel
```

**Study start.** Choose the scope. Enter starts the session.

```
==================================== Study =====================================

  Due now 12      New left today 8 of 20

  > All cards                 12 due     8 new
    Haushalt                   3 due     0 new
    Lesen: Kafka               5 due     4 new
    Serie: Dark                4 due     4 new















enter Start   esc Back
```

**Study, self-graded front (German → English).**
- The answer button and, after the reveal, the grade buttons sit in the same
  bottom zone, so a thumb never moves (§12.5).
- The example line is the copied sense example (§7.2).

```
========================== Study - 12 due, 8 new left ==========================

                               German -> English


                                    das Band
                                      noun

                        Die Frau trug ein Band im Haar.










+-----------------------------------------------------------------------------+
|                             Show answer  (space)                            |
+-----------------------------------------------------------------------------+

space Show   esc End
```

**Study, self-graded after the reveal.** Grading stores at once (§7.4) and
moves to the next card. There is no undo (spec).

```
========================== Study - 12 due, 8 new left ==========================

                               German -> English


                                    das Band
                                      noun

                        Die Frau trug ein Band im Haar.
                    ----------------------------------------
                                  tape, ribbon
                      The woman wore a ribbon in her hair.







+-----------------+ +-----------------+ +-----------------+ +-----------------+
|     1 Again     | |      2 Hard     | |      3 Good     | |      4 Easy     |
+-----------------+ +-----------------+ +-----------------+ +-----------------+

1 Again   2 Hard   3 Good   4 Easy   esc End
```

**English → German, revealed.** The front is the top block, down to `noun`.

```
========================== Study - 11 due, 8 new left ==========================

                               English -> German


                                  tape, ribbon
                                      noun

                    ----------------------------------------
                                    das Band
                        Die Frau trug ein Band im Haar.
                      The woman wore a ribbon in her hair.







+-----------------+ +-----------------+ +-----------------+ +-----------------+
|     1 Again     | |      2 Hard     | |      3 Good     | |      4 Easy     |
+-----------------+ +-----------------+ +-----------------+ +-----------------+

1 Again   2 Hard   3 Good   4 Easy   esc End
```

**German → German, revealed.**

```
========================== Study - 10 due, 8 new left ==========================

                               Deutsch -> Deutsch


   zumeist aus einem bestimmten Gewebe/Stoff bestehendes längeres, schmales,
   streifenartiges Stück, das verwendet wird als Schmuck/Zierde, zur
   Verstärkung, zum Zusammenhalten und dergleichen Zwecke

                    ----------------------------------------
                                    das Band








+-----------------+ +-----------------+ +-----------------+ +-----------------+
|     1 Again     | |      2 Hard     | |      3 Good     | |      4 Easy     |
+-----------------+ +-----------------+ +-----------------+ +-----------------+

1 Again   2 Hard   3 Good   4 Easy   esc End
```

**Phrase card, revealed.**

```
========================== Study - 9 due, 8 new left ===========================

                           Phrase: English -> German


                            History repeats itself.
                      note: said about recurring patterns

                    ----------------------------------------
                          Geschichte wiederholt sich.









+-----------------+ +-----------------+ +-----------------+ +-----------------+
|     1 Again     | |      2 Hard     | |      3 Good     | |      4 Easy     |
+-----------------+ +-----------------+ +-----------------+ +-----------------+

1 Again   2 Hard   3 Good   4 Easy   esc End
```

**Article card.**
- `1`/`2`/`3` or a tap answers, and the check grades it (§7.4).
- The front shows the plural and the copied hint gloss, because homographs
  (Band n/m/f, See, Leiter) would otherwise share a front while expecting
  different answers. That is a content change: `article` gains `plural` and
  `hint` (§7.2).

```
========================== Study - 8 due, 8 new left ===========================

                                    Article


                              Band   (pl. Bänder)
                                  tape, ribbon












+-----------------------+ +-----------------------+ +-----------------------+
|         1 der         | |         2 die         | |         3 das         |
+-----------------------+ +-----------------------+ +-----------------------+

1 der   2 die   3 das   esc End
```

**Article feedback.** Any of `enter`/`space`/the button continues.

```
========================== Study - 7 due, 8 new left ===========================

                                    Article


                              Band   (pl. Bänder)
                                  tape, ribbon

                     WRONG   das Band      (you chose: der)










+-----------------------------------------------------------------------------+
|                                Next  (enter)                                |
+-----------------------------------------------------------------------------+

enter Next   esc End
```

**Stammformen card.**
- Three compact Inputs. Enter moves to the next field, and Enter on the last
  field checks.
- The hint gloss tells homograph verbs apart (umfahren: `fährt um` vs
  `umfährt`), so `stammformen` gains `hint` (§7.2).
- A separable verb shows the TRENNBAR badge from `separable_prefix` (§7.2).

```
========================== Study - 7 due, 8 new left ===========================

                                  Stammformen

                         anrufen  -  to call, to phone
               TRENNBAR  an|rufen   (answer with the split forms)

        er/sie/es   [ ruft an                           ]
        Präteritum  [ rief an                           ]
        Perfekt     [ hat angerufen_                    ]

        ae/oe/ue/ss are accepted for ä/ö/ü/ß











enter Next field / Check   tab Field   esc End
```

**Stammformen feedback**, shown in place on the same rows (§12.4).

```
========================== Study - 6 due, 8 new left ===========================

                                  Stammformen

                         anrufen  -  to call, to phone
               TRENNBAR  an|rufen   (answer with the split forms)

        er/sie/es   ruft an                    ok
        Präteritum  rief                       WRONG  rief an
        Perfekt     hat angerufen              ok

  WRONG - graded Again.   trennbar: the prefix goes to the end in main clauses







+-----------------------------------------------------------------------------+
|                                Next  (enter)                                |
+-----------------------------------------------------------------------------+

enter Next   esc End
```

**Session summary.** Computed from the review log (§7.4). The backup line
appears when a backup was written (§10).

```
=============================== Session finished ===============================



                               15 cards reviewed
                             12 answered correctly

                    Backup written: learning-20261018-214012.db











+-----------------------------------------------------------------------------+
|                                Home  (enter)                                |
+-----------------------------------------------------------------------------+

enter Home
```

**Phrases.**
- Enter in the Input searches. Enter or a tap on a pair opens the Save modal.
- `^n` opens the `$EDITOR` template (§9) with the query as a comment. The
  app is suspended meanwhile, and Phrases returns afterwards with a toast.

```
=================================== Phrases ====================================
 > repeats itself_
 ------------------------------------------------------------------------------
 > Geschichte wiederholt sich.
     History repeats itself.
   <German sentence>
     <English sentence>
   <German sentence>
     <English sentence>
   ...











 No good match?  ^n writes your own pair in $EDITOR

enter Search / Save   ^n Write own   tab List/Input   esc Back
```

**Save phrase**: a modal over Phrases. The deck row appears only if decks
exist.

```
      +----------------------- Save phrase card -----------------------+
      | Geschichte wiederholt sich.                                    |
      | History repeats itself.                                        |
      | Decks:  [ ] Haushalt   [ ] Lesen: Kafka   [ ] Serie: Dark       |
      |                                   [ Cancel ]   [ Save ]        |
      +----------------------------------------------------------------+
```

**Cards.**
- A `DataTable` of live cards (deleted ones are filtered out by the
  session's global criteria, §7.7), sorted by due date.
- `/` focuses a filter Input docked at the top, matching front text, type
  and deck name. `esc` leaves the filter.
- `e` edits in `$EDITOR` (§9), `s` toggles suspend, `x` opens a confirm modal
  before the soft delete, and `d` opens a modal `SelectionList` of decks for
  the card's word or phrase.

```
=============================== Cards - 341 live ===============================
 Filter: (/ to filter)
 Type      Front                               Due           State
 ------------------------------------------------------------------------------
 > de->en  das Band                            2026-10-21
   en->de  tape, ribbon                        2026-10-19
   de->de  zumeist aus einem bestimmten Gew... today
   article Band (pl. Bänder)                   today
   stamm.  laufen                              new
   phrase  History repeats itself.             2026-11-02    suspended
   ...












/ Filter   e Edit   s Suspend   x Delete   d Decks   esc Back
```

**Decks.** `n` opens a one-row modal Input (Enter creates, `esc` cancels).
`x` deletes after confirmation; cards are untouched.

```
==================================== Decks =====================================

  > Haushalt                   12 items     30 cards
    Lesen: Kafka                8 items     21 cards
    Serie: Dark                 6 items     15 cards


















n New   x Delete   esc Back
```

**Info.** `render_info`, scrollable.

```
===================================== Info =====================================
 Harald 0.5.0     lexicon schema 4     learning.db revision 0001
 Paths
   lexicon     ~/storage/shared/harald/lexicon.db
   learning    ~/.local/share/harald/learning.db
   backup      ~/storage/shared/harald-backup   (last 2026-10-18 21:40)
 Sources
   Tatoeba           2026-10-17   CC BY 2.0 FR
     Tatoeba contributors (tatoeba.org)
   Wiktionary (de)   2026-10-03   CC BY-SA 4.0
     Wiktionary contributors, extracted by wiktextract (kaikki.org)
   Wiktionary (en)   2026-10-03   CC BY-SA 4.0
     Wiktionary contributors, extracted by wiktextract (kaikki.org)
 Coverage (informational; figures illustrative)
   verbs with complete Stammformen     nn.n %
   nouns with a gender                 nn.n %
   senses with a translated example    nn.n %






esc Back
```

### 12.4 Reduced height (about 80×12, on-screen keyboard up)

**Mechanism.** `HaraldApp.VERTICAL_BREAKPOINTS = [(0, "-short"), (16, "-normal")]`.
Textual 8 puts the class on the Screen according to terminal height. Under
`Screen.-short`:
- the `Header` is hidden;
- the `Footer` stays, because it carries the key hints and is tappable;
- `Button`s turn compact (one row, no border);
- the study prompt loses its vertical centring and starts at the top;
- the Add-word step line takes over the header's job of naming where you
  are.

The implementer may apply the compact style in TCSS or by toggling each
button's `compact` reactive. Either is acceptable, as long as the 80×12 tests
below pass.

**Supported floor: 80×12 for wide terminals, 40×12 in portrait (§12.8).**
Every screen keeps its essential controls visible and usable at 80×12. The 80×24 frames are the designed layout, and anything
between 16 and 23 rows is the normal layout with scrolling bodies. Below 12
rows nothing is designed. Lookup and Stammformen degrade last, because their
Inputs are docked to the top.

| Screen | Must work at 80×12? | How |
|---|---|---|
| **Lookup** | yes. Typing a word *is* the keyboard-up case | Input docked at the top (1 row), divider, results list takes the rest (about 8 rows) and scrolls |
| **Stammformen** | yes. The answer is typed | Title, infinitive and hint merge onto one row; three compact Inputs, 3 rows. Feedback replaces the input cells **in place**, adding no rows. Bordered three-row Inputs would need 9 rows, which is why Inputs are compact everywhere |
| **Add word** | yes. It opens straight from a lookup, often with the keyboard still up | The wizard gives each step's single list the whole body. The step line carries compact `Back`/`Next` buttons on the top row. Step 3's summary collapses to two lines, and the deck list scrolls |
| **Phrases** | yes. Typing | As Lookup. Each result takes 2 rows, so about 4 are visible |
| **Study** (self-graded, article) | yes, although the keyboard is normally hidden (buttons, §12.5) | Prompt from the top; compact answer and grade buttons on one row |
| **Cards filter**, **New deck** modal | yes | Filter Input docked at the top, table scrolls; the modal is 3 rows plus a button row |
| Entry, Info, Home, Study start, Summary, Decks | scrolling is enough | no special rules |

Lookup at 80×12:

```
 DE > lief_
 ------------------------------------------------------------------------------
 > laufen                verb      form: lief
   Lauf                  noun      ~1
   Brief                 noun      ~1
   lieb                  adj       ~1
   Lied                  noun      ~1
   ...



enter Open   ^t DE/EN   tab List/Input   esc Back
```

Stammformen at 80×12:

```
 Stammformen   anrufen - to call, to phone   TRENNBAR an|rufen

        er/sie/es   [ ruft an                           ]
        Präteritum  [ rief an                           ]
        Perfekt     [ hat angerufen_                    ]






enter Next field / Check   tab Field   esc End
```

Add word step 1 at 80×12:

```
 1/3 English senses   2 selected                    [ Cancel ]  [ Next > ]
 [X] 1. tape, ribbon
 [ ] 2. A ligament
 [X] 3. band or tie holding items together
 [ ] 4. belt (conveyor belt, fan belt, etc.)
 [ ] 5. band of the spectrum
 [ ] 6. [figuratively] intimate bond to a person
 [ ] 7. [figuratively] dependence, social bond          (list scrolls)



space Toggle   n Next   esc Cancel
```

Add word step 3 at 80×12:

```
 3/3 Confirm                               [ < Back ]  [ Create 6 cards ]
 Create: 2 de->en, 2 en->de (senses 1, 3); 1 de->de; 1 article (das)
 Refused: none
 Decks:
 [ ] Haushalt
 [X] Lesen: Kafka
 [ ] Serie: Dark                                        (list scrolls)




space Toggle   c Create   b Back   esc Cancel
```

Study, revealed, at 80×12:

```
 German -> English                 das Band  (noun)
 Die Frau trug ein Band im Haar.
 ----------------------------------------
 tape, ribbon
 The woman wore a ribbon in her hair.




 [   1 Again    ]   [    2 Hard    ]   [    3 Good    ]   [    4 Easy    ]

1 Again   2 Hard   3 Good   4 Easy   esc End
```

**Test hook.** Use `App.run_test(size=(80, 24))` and `run_test(size=(80, 12))`.
For each screen and study state, assert that the key widgets (the focused
Input, the highlighted list row, every Button, the Footer) have non-empty
regions lying fully inside the screen region. Whether to add snapshot tests is
the tdd step's call.

### 12.5 Touch and mouse fallback for grading: decided yes

**Decision.** Study shows tappable buttons, sized for thumbs at 40 columns
in portrait (§12.8):
- **Show answer** before the reveal, then **1 Again / 2 Hard / 3 Good /
  4 Easy**;
- **der / die / das** on article cards;
- **Next** on feedback, **Home** on the summary.

Elsewhere, buttons appear only in the Add-word wizard (Back/Next/Create) and
in modals (Save/Cancel/Delete). The rest relies on widgets that are already
tappable (`OptionList`, `SelectionList` and `DataTable` rows), on the tappable
footer keys, and on swipe-to-scroll. Keys stay primary everywhere. A button
calls the same action method as its key (`action_reveal`, `action_grade(n)`,
`action_answer_article(g)`), so there is exactly one code path.

**Rationale:**
1. Studying is the most frequent thing done on the phone, in spare moments,
   often one-handed. Self-graded cards need only "reveal" and "grade", never
   text.
2. With the soft keyboard hidden, Termux still shows its extra-keys row
   (Esc, Tab, Ctrl, Alt, arrows, PgUp/PgDn) but **not digits or space**.
   Without buttons, every self-graded card would force the keyboard up and
   shrink the screen to about 12 rows for the whole session.
3. Footer hints are already tappable, but they are one row high and 6–9 cells
   wide, too small for a thumb to hit reliably. A three-row button a quarter
   of the screen wide is not.
4. The cost is a handful of widgets and some CSS.

**Not added:**
- Stammformen buttons: the answer must be typed, so the keyboard is up
  anyway and Enter is on every soft keyboard.
- Lookup and Phrases buttons: typing again.
- Cards action buttons: footer taps are enough for infrequent actions.

**Accidental taps.** A grade is final (no undo, spec), and "Show answer"
spans the zone where the grade buttons then appear, so a double tap on Show
could land on a grade. Grade and article buttons therefore **ignore presses
for 300 ms after they appear**. Keys are not debounced.

**Dependency to verify.** Termux must deliver taps as mouse clicks and swipes
as wheel events while Textual's mouse tracking is on (Textual's default).
That is expected, not verified, so it is added to issue 009's phone checks
(§15). If it fails, the keys remain fully sufficient and the buttons become
inert rather than harmful.

### 12.6 Layout decisions and rationale

| Decision | Rationale | Rejected |
|---|---|---|
| Built-in `Header` / `Footer(compact=True)`, palette off | No custom chrome to maintain. The compact footer fits about six hints in 80 columns, and the palette is redundant with a stray tap target | custom status bars; keeping the palette |
| One column on every screen | 80 columns can't hold a list and a readable preview side by side | split list and preview for Lookup and Cards |
| One Lookup screen with DE/EN modes (`^t`) | Same Input, list and Entry flow. Home keeps two entries for discoverability | separate screens; a mode prefix typed into the Input |
| Two steps in Lookup (Enter searches, Enter opens) | Results are always fuzzily ranked and ties are common (essen/Essen), so the list should be seen; the second Enter or tap is cheap. Confirmed by the user (§12.7) | auto-opening the top hit |
| Add word as a **three-step wizard** | Two scrollable `SelectionList`s plus a deck list in one scroll container means nested scrolling, focus jumps and scroll-into-view bugs. At 12 rows no list would get more than about 4 rows. The spec already keeps the two pickers separate because the editions number senses differently, and a step per edition makes that explicit. Nothing is written before Create, so Back/Cancel cost nothing | one scrolling form; tabs per picker |
| Compact one-row `Input`s everywhere | Three-row bordered Inputs make Stammformen 9 rows of fields, which can't work keyboard-up. Using the same style everywhere avoids two looks | bordered Inputs at normal height only |
| Short layout below 16 rows: no header, compact buttons, footer kept | The footer carries the key hints and the tap targets; the header's context moves into each screen's first line | hiding the footer; a separate "mobile mode" setting |
| Stammformen feedback in place | Fits 80×12 with no extra rows, and each field's verdict sits next to what was typed | a separate feedback block |
| Cards filter behind `/` | Keeps the table focused so letter actions work (focus rule, §12.1) | an always-focused filter Input |
| Grade buttons with a 300 ms guard | §12.5 | keys only |
| Article and Stammformen fronts show a hint (and the plural for article) | Homographs would otherwise show identical fronts with different answers. `article` gains `plural`, `hint`; `stammformen` gains `hint` (§7.2) | relying on the lemma alone |

### 12.7 Layout questions: answered by the user

1. **Orientation: portrait.** The phone runs the TUI at about 40 columns.
   Every phone-facing screen has a narrow layout (§12.8). Desktop and SSH
   keep 80 or more.
2. **Lookup: two steps** (Enter searches, Enter opens). Kept as designed.
3. **Interval previews on the grade buttons: off**, as designed.
4. **The keyboard-up floor** is measured in issue 009, in portrait with the
   keyboard up (designed for 40×12, §12.8).

### 12.8 Portrait layout (the phone): 40 columns

**Decision (the user's): the phone runs the TUI in portrait.**
- **The target is 40 columns.** Portrait at a readable font gives about
  40–45 columns. Every layout must work from 40 up.
- **Desktop and SSH keep 80 or more**, with the wide layouts of §12.3.
- **Two layouts, picked by width:** narrow below 60 columns, wide from 60
  up. That is the same 60-column switch as `render.py` (§6). It is set
  through `HORIZONTAL_BREAKPOINTS = [(0, "-narrow"), (60, "-wide")]` on
  `HaraldApp`, next to the existing vertical `-short` breakpoint.

**Height.** A portrait phone is tall. At 40 columns there are usually about
35–40 rows, and an estimated 18–22 with the keyboard up. The frames below
use 40×24 and 40×12 on purpose, as margin. Issue 009 measures the real rows
in portrait with the keyboard up (§12.7 q4).

**Every phone-facing screen goes narrow.**

| Screen | Narrow? | Changes from the wide layout |
|---|---|---|
| Study (all card types, feedback, summary) | **yes, the priority** | same single column; four grade buttons of 9 columns each (thumb width, below); article buttons 12 columns each; Stammformen labels sit left of compact Inputs (`er/sie/es  [ … ]`) |
| Lookup (DE / EN) | yes | result rows shortened to lemma, pos and match (`form: band`, `~1`, `proper noun`); English → German words indented under their sense |
| Entry | yes | glosses wrap; tenses stack one per block (§6); TRENNBAR badge under the headword |
| Add word wizard | yes | already one list per step; definitions wrap under the checkbox; Back/Next buttons 19 columns each |
| Phrases + Save modal | yes | each pair wraps over two to four lines; the modal's deck list stacks |
| Cards | yes | three columns (type, front, due), with the state shown as a marker; front truncated with `...` |
| Decks | yes | name and counts on one line |
| Info | yes | paths wrap under their label |
| Check (new) | yes | flagged words over two lines; the detail diff stacks "yours" and "upstream" when a side-by-side pair won't fit (§8.4) |
| Home | yes | menu one item per line, plus the new `k` Check entry |

**Footer at 40 columns.** It shows three or four primary hints. `?` opens
Textual's `HelpPanel` (`action_show_help_panel`, present in Textual 8) with
every binding of the screen, so nothing becomes undiscoverable.

**Touch buttons at thumb width.** At 40 columns:
- four grade buttons are 9 columns each (`1 Again`, `2 Hard`, `3 Good`,
  `4 Easy`) with one-column gaps. That is about a quarter of the screen
  width each, roughly 15–17 mm on a typical phone, and three rows tall;
- the article buttons are 12 columns each;
- Show answer and Next span the full width.

They stay in the same bottom zone, and keep the 300 ms guard (§12.5). With
the keyboard up (`-short`) they collapse to one row, still 9 columns wide.

**Portrait wireframes, 40×24.** Generated and checked like §12.3: every line
is at most 40 columns.

Home:

```
================ Harald ================

 Due 12   New 8 of 20   Cards 341
 Lexicon: schema 4, 2026-10-03

 > l  Look up German
   e  English -> German
   p  Phrases
   s  Study
   c  Cards
   d  Decks
   k  Check after a rebuild
   i  Info










enter Open  q Quit  ? Keys
```

Lookup, German. Proper nouns rank after common words (§4.1):

```
=========== Lookup - Deutsch ===========
 DE > band_
 --------------------------------------
 > Band         noun  3 entries
   binden       verb  form: band
   Bande        noun  ~1
   Bank         noun  ~1
   bang         adj   ~1
   Band         name  proper noun
   ...













enter Open  ^t DE/EN  esc Back
```

Lookup, English → German:

```
========== Lookup - EN -> DE ===========
 EN > use_
 --------------------------------------
   use (verb)
    employ, apply
 >    benutzen
      verwenden
      gebrauchen
      nutzen
    to exhaust the supply of, to
    consume
      verbrauchen
    to exploit
      ausnutzen
      zum Vorwand nehmen
        (use as a pretext)
   use (noun)
    act of using
      die Benutzung
   ...



enter Open  ^t DE/EN  esc Back
```

Entry, noun:

```
============= Band - noun ==============
 das Band  pl. Bänder  [bant]
  1. tape, ribbon
  2. A ligament
  3. band or tie holding items
     together
  4. belt (conveyor belt, fan belt,
     etc.)
  5. band of the spectrum
  6. [figuratively] intimate bond to
     a person
  ...
 der Band  pl. Bände
  1. volume, a single book, chiefly
     when part of a larger set
  2. volume of a multi-volume
     publication
 die Band  pl. Bands
  1. modern music band
 German definitions (de.wiktionary)
  das Band            (scrolls)


a Add  esc Back  ? Keys
```

Entry, separable verb, with tenses stacked:

```
============ anrufen - verb ============
 anrufen  [ˈanˌʁuːfn̩]
 TRENNBAR  an|rufen
 ruft an / rief an / hat angerufen
  1. [transitive] to call, to phone
     Ruf mich morgen an. - Call me
     tomorrow.
 Präsens
  ich        rufe an
  du         rufst an
  er/sie/es  ruft an
  wir        rufen an
  ihr        ruft an
  sie/Sie    rufen an
 Präteritum
  ich        rief an
  du         riefst an
  er/sie/es  rief an
  ...                 (scrolls)




a Add  c All tenses  esc Back
```

Pick entry (modal):

```
 +--------- Add which entry? --------+
 | > das Band  pl. Bänder            |
 |     tape, ribbon                  |
 |   der Band  pl. Bände             |
 |     volume, a single book         |
 |   die Band  pl. Bands             |
 |     modern music band             |
 +-----------------------------------+
```

Add word, steps 1–3:

```
======= Add - das Band (Bänder) ========
 1/3 English senses
 (each: de->en and en->de card)
 --------------------------------------
 [X] 1. tape, ribbon
 [ ] 2. A ligament
 [X] 3. band or tie holding items
        together
 [ ] 4. belt (conveyor belt, fan
        belt, etc.)
 [ ] 5. band of the spectrum
 [ ] 6. [figuratively] intimate
        bond to a person
 [ ] 7. [figuratively] dependence,
        social bond
 [ ] 8. [poetic] shackle

 2 selected
+-----------------+ +-----------------+
|      Cancel     | |      Next >     |
+-----------------+ +-----------------+


space Toggle  n Next  esc Cancel
```

```
======= Add - das Band (Bänder) ========
 2/3 German definitions
 (each: a de->de card)
 --------------------------------------
     das Band
 [ ] [1] dasjenige, was verbindet
         oder verknüpft
 [X] [2] zumeist aus einem
         bestimmten Gewebe/Stoff
         bestehendes längeres,
         schmales Stück, ...
         Plural »Bänder«:
         (heading, not pickable)
     der Band
 [ ] [1] (zumeist größeres)
         gebundenes Buch
     ...
 1 selected
+-----------------+ +-----------------+
|      < Back     | |      Next >     |
+-----------------+ +-----------------+


space Toggle  n Next  b Back
```

```
======= Add - das Band (Bänder) ========
 3/3 Confirm
 --------------------------------------
 Cards to create
  2 de->en + 2 en->de (senses 1, 3)
  1 de->de  [2] (das Band)
  1 article  das
 Refused
  none
  (a verb could show: Stammformen -
  missing: Präteritum, auxiliary)
 Decks
 [ ] Haushalt
 [X] Lesen: Kafka
 [ ] Serie: Dark



+-----------------+ +-----------------+
|      < Back     | |     Create 6    |
+-----------------+ +-----------------+


space Toggle  c Create  b Back
```

Study start:

```
================ Study =================

 Due now 12   New left 8 of 20

 > All cards        12 due   8 new
   Haushalt          3 due   0 new
   Lesen: Kafka      5 due   4 new
   Serie: Dark       4 due   4 new















enter Start  esc Back
```

Study, self-graded front and revealed:

```
======== Study - 12 due, 8 new =========

           German -> English


                das Band
                  noun

    Die Frau trug ein Band im Haar.











+-------------------------------------+
|         Show answer  (space)        |
+-------------------------------------+
space Show  esc End
```

```
======== Study - 12 due, 8 new =========

           German -> English


                das Band
                  noun

    Die Frau trug ein Band im Haar.
        ------------------------
              tape, ribbon
       The woman wore a ribbon in
               her hair.







+-------+ +-------+ +-------+ +-------+
|1 Again| | 2 Hard| | 3 Good| | 4 Easy|
+-------+ +-------+ +-------+ +-------+
1-4 Grade  esc End  ? Keys
```

English → German, German → German, phrase (revealed):

```
======== Study - 11 due, 8 new =========

           English -> German


              tape, ribbon
                  noun

        ------------------------
                das Band
    Die Frau trug ein Band im Haar.
       The woman wore a ribbon in
               her hair.







+-------+ +-------+ +-------+ +-------+
|1 Again| | 2 Hard| | 3 Good| | 4 Easy|
+-------+ +-------+ +-------+ +-------+
1-4 Grade  esc End  ? Keys
```

```
======== Study - 10 due, 8 new =========

           Deutsch -> Deutsch

 zumeist aus einem bestimmten
 Gewebe/Stoff bestehendes längeres,
 schmales, streifenartiges Stück, das
 verwendet wird als Schmuck/Zierde,
 zur Verstärkung, zum Zusammenhalten
 und dergleichen Zwecke

        ------------------------
                das Band







+-------+ +-------+ +-------+ +-------+
|1 Again| | 2 Hard| | 3 Good| | 4 Easy|
+-------+ +-------+ +-------+ +-------+
1-4 Grade  esc End  ? Keys
```

```
========= Study - 9 due, 8 new =========

       Phrase: English -> German


        History repeats itself.
     note: about recurring patterns

        ------------------------
      Geschichte wiederholt sich.










+-------+ +-------+ +-------+ +-------+
|1 Again| | 2 Hard| | 3 Good| | 4 Easy|
+-------+ +-------+ +-------+ +-------+
1-4 Grade  esc End  ? Keys
```

Article card and feedback:

```
========= Study - 8 due, 8 new =========

                Article


          Band   (pl. Bänder)
              tape, ribbon













+----------+ +----------+ +----------+
|  1 der   | |  2 die   | |  3 das   |
+----------+ +----------+ +----------+
1/2/3 Answer  esc End
```

```
========= Study - 7 due, 8 new =========

                Article


          Band   (pl. Bänder)
              tape, ribbon

            WRONG   das Band
            (you chose: der)










+-------------------------------------+
|            Next  (enter)            |
+-------------------------------------+
enter Next  esc End
```

Stammformen card for a separable verb, and feedback. The TRENNBAR badge
comes from the card's `separable_prefix` (§7.2):

```
========= Study - 7 due, 8 new =========

              Stammformen

      anrufen - to call, to phone
           TRENNBAR  an|rufen
     (answer with the split forms)

 er/sie/es  [ ruft an               ]
 Präteritum [ rief an               ]
 Perfekt    [ hat angerufen_        ]

 ae/oe/ue/ss accepted for ä/ö/ü/ß










enter Next/Check  esc End  ? Keys
```

```
========= Study - 6 due, 8 new =========

              Stammformen

      anrufen - to call, to phone
           TRENNBAR  an|rufen
     (answer with the split forms)

 er/sie/es  ruft an          ok
 Präteritum rief             WRONG
            -> rief an
 Perfekt    hat angerufen    ok

          WRONG - graded Again
      trennbar: the prefix an goes
       to the end in main clauses

+-------------------------------------+
|            Next  (enter)            |
+-------------------------------------+



enter Next  esc End
```

Session summary:

```
=========== Session finished ===========



           15 cards reviewed
         12 answered correctly

            Backup written:
      learning-20261018-214012.db











+-------------------------------------+
|            Home  (enter)            |
+-------------------------------------+
enter Home
```

Phrases, and the Save modal:

```
=============== Phrases ================
 > repeats itself_
 --------------------------------------
 > Geschichte wiederholt sich.
     History repeats itself.
   <German sentence, wrapped
    over two lines when long>
     <English sentence>
   <German sentence>
     <English sentence>
   ...







 No good match? ^n writes your
 own pair in $EDITOR



enter Search/Save  ^n Own  esc Back
```

```
 +-------- Save phrase card ---------+
 | Geschichte wiederholt sich.       |
 | History repeats itself.           |
 | Decks: [ ] Haushalt               |
 |        [ ] Lesen: Kafka           |
 |        [ ] Serie: Dark            |
 | [ Cancel ]            [ Save ]    |
 +-----------------------------------+
```

Cards:

```
=========== Cards - 341 live ===========
 Filter: (/ to filter)
 Type   Front                Due
 --------------------------------------
 > de>en  das Band           10-21
   en>de  tape, ribbon       10-19
   de>de  zumeist aus ein... today
   art.   Band (Bänder)      today
   stamm  anrufen  TRENNBAR  new
   phrase History repeat...  susp.
   ...












e Edit  s Susp.  x Del  ? Keys
```

Decks:

```
================ Decks =================

 > Haushalt        12 items  30 cards
   Lesen: Kafka     8 items  21 cards
   Serie: Dark      6 items  15 cards


















n New  x Delete  esc Back
```

Info:

```
================= Info =================
 Harald 0.5.0
 lexicon schema 4
 learning.db revision 0001
 Paths
  lexicon  ~/storage/shared/harald/
           lexicon.db
  learning ~/.local/share/harald/
           learning.db
  backup   ~/storage/shared/
           harald-backup
           (last 2026-10-18 21:40)
 Sources
  Tatoeba          2026-10-17
    CC BY 2.0 FR
  Wiktionary (de)  2026-10-03
    CC BY-SA 4.0
  Wiktionary (en)  2026-10-03
    CC BY-SA 4.0
 Coverage, attribution  (scrolls)



esc Back
```

Check, the list (§8):

```
======= Check - 4 words flagged ========
 Lexicon built 2026-11-02, schema 4
 --------------------------------------
 > das Band  (n|Bänder)
     2 cards  changed
   fragen
     1 card   changed: Präteritum
   Leiter  (m|Leiter)
     3 cards  ambiguous: 2 entries
   Kiefer  (f|Kiefern)
     2 cards  disappeared

 Unlinked (kept, not re-flagged): 1










enter Open  esc Back  ? Keys
```

Check detail, changed. Accept shows the diff and resets the schedule by
default because the answer changed:

```
============ Check - fragen ============
 Stammformen  CHANGED

 Your copy        Upstream now
 fragt            fragt
*frug            *fragte
 hat gefragt      hat gefragt


 Accepting changes the answer:
 schedule resets to new  [r] keep
 Review history is kept.






+----------+ +----------+ +----------+
| a Relink | | b Accept | |  c Keep  |
+----------+ +----------+ +----------+


a/b/c Repair  esc Back  ? Keys
```

Check detail, ambiguous (relink):

```
====== Check - Leiter (m|Leiter) =======
 3 cards  AMBIGUOUS
 Your hint matches 2 entries now:

 > der Leiter  pl. Leiter
     leader, head (of a group)
   der Leiter  pl. Leiter
     conductor (of electricity)

 Relink: pick the entry; your cards
 keep their own copy. Then check
 again for changes.






+----------+ +----------+ +----------+
| a Relink | |   b -    | |  c Keep  |
+----------+ +----------+ +----------+


enter/a Relink  c Keep  esc Back
```

**Keyboard up, portrait, 40×12.** The `-short` rules of §12.4 apply: no
header, compact buttons.

Lookup:

```
 DE > band_
 --------------------------------------
 > Band         noun  3 entries
   binden       verb  form: band
   Bande        noun  ~1
   Bank         noun  ~1
   bang         adj   ~1
   ...



enter Open  ^t DE/EN  esc Back
```

Stammformen (separable):

```
 anrufen - to call  TRENNBAR an|rufen
 er/sie/es  [ ruft an               ]
 Präteritum [ rief an               ]
 Perfekt    [ hat angerufen_        ]







enter Next/Check  esc End
```

Add word, steps 1 and 3:

```
 1/3 EN senses  2 sel. [Cancel][Next>]
 [X] 1. tape, ribbon
 [ ] 2. A ligament
 [X] 3. band or tie holding items
        together
 [ ] 4. belt (conveyor belt, fan
        belt, etc.)       (scrolls)




space Toggle  n Next  esc Cancel
```

```
 3/3 Confirm     [< Back][Create 6]
 2 de>en, 2 en>de; 1 de>de; article
 Refused: none
 Decks:
 [ ] Haushalt
 [X] Lesen: Kafka
 [ ] Serie: Dark          (scrolls)




space Toggle  c Create  b Back
```

Study, revealed:

```
 de->en      das Band (noun)
 Die Frau trug ein Band im Haar.
 ------------------------
 tape, ribbon
 The woman wore a ribbon in her
 hair.



[1 Again] [2 Hard ] [3 Good ] [4 Easy ]

1-4 Grade  esc End
```

**Tests and benchmarks.**
- **The §12.4 test hook runs at four sizes:** 40×24, 40×12, 80×24 and 80×12.
  The key widgets must have non-empty regions inside the screen, and no
  `Static` content may overflow its width.
- **`cold.tui_start`** in the harness (§14.9) runs headless at 40×24, the
  phone's real shape. The desktop run also records 80×24.

**Spec and doc wording that must change** (user-owned; this design doesn't
edit them):
- **Spec line 36**, "Everything, TUI included, works at 80 columns minimum.
  That includes conjugation displays." → "works at 40 columns minimum
  (portrait phone); desktop and SSH use 80 or more. That includes
  conjugation displays."
- **Spec line 137**, "All lookup output, CLI and TUI, fits within 80
  columns." → "All lookup output, CLI and TUI, fits the terminal width down
  to 40 columns."
- **Spec line 257**, "Textual's startup time and rendering at 80 columns in
  Termux." → "… rendering at 40 columns (portrait) in Termux."
- **AGENTS.md line 8**, "Target terminals: 80 columns minimum, including
  phone SSH clients" → "Target terminals: 40 columns minimum (phone,
  portrait); 80 or more on desktop and SSH."
- **Issue 001 line 11, issue 002 line 10, issue 009 line 9** say "80
  columns". Change them to "down to 40 columns", and in 009, "in portrait".

---

### 12.9 Deviations found while implementing 009 (2026-10-25)

Where the code departs from the design above, and why. Reviewed by the user
as one batch.

- **Use cases take `Config`, not handles.** §11.2 has `cli` open `Lexicon`
  first and pass it in. The existing use cases (`LookUpGerman(config)`) open
  the lexicon inside `execute`, and the TUI follows them. The cost is one
  lexicon open per search and per "Also" row. The preflight in §12's intro is
  `QueryLexiconInfo(config)` rather than an opened handle.
- **`load_headword` is new.** `lexicon.lookup.load_headword(lex, lemma, pos)
  -> Option[Headword]`, with the use case `LoadHeadword(config)`; the
  eager-load options are shared with `lookup_de` as `_FULL_LOAD`. It serves
  the "Also" rows.
- **No match column.** The §12.3 and §12.8 lookup wireframes show `~1` and
  `3 entries` per result. `LookupResult` carries neither the fuzzy distance
  nor the entry count, so rows read `lemma  pos  [form: X]`. Adding the marker
  is a model change, deferred.
- **Tab order.** `tab` is not rebound, so Textual's default focus order
  applies; "tab or up from the first row returns to the Input" is not
  implemented.
- **Home** lists lookup (`l`), info (`i`) and quit (`q`) only. The due/new/
  cards line and the other entries arrive with `learning.db`.
- **Titles.** The app sets title `Lookup`, sub-title `Deutsch`, rather than
  the wireframes' single `Lookup - Deutsch` string.
- **Header** is hidden under the `-short` breakpoint (fewer than 16 rows);
  the footer is always compact. Breakpoints: width 60 for `-narrow`/`-wide`,
  height 16 for `-short`/`-normal`.
- **`tests/unit/test_layering.py`** allows `harald.tui` as a front-end.
- **Still unverified, by hand in Termux:** `$EDITOR` suspend and resume (no
  screen calls an editor and `harald.editor` does not exist yet), startup
  time, the row count with the keyboard up (§12.7 q4), and taps and swipes
  as clicks and scroll. Results go in `dev/issues/009-…md`.

---

## 13. Config (`harald/config.py`)

`$XDG_CONFIG_HOME/harald/config.toml` (default `~/.config/...`), read with
`tomllib`. Unknown keys are an error, to catch typos. Paths are expanded with
`~`.

| Key | Default | Machine |
|---|---|---|
| `lexicon` | `$XDG_DATA_HOME/harald/lexicon.db` | both. On the desktop, a path inside the send-only Syncthing folder; on the phone, where Syncthing delivers it |
| `learning_db` | `$XDG_DATA_HOME/harald/learning.db` | phone |
| `backup_dir` | unset (backup off) | phone, a send-only Syncthing folder |
| `backup_keep` | 10 (confirmed) | phone |
| `sources_dir` | `$XDG_DATA_HOME/harald/sources` | desktop |
| `staging_dir` | `$XDG_CACHE_HOME/harald/staging` | desktop, same filesystem as `lexicon` |
| `build_min_entries` | 50000 | desktop |
| `build_workers` | `os.cpu_count() - 1`, minimum 1; `0` runs every job inline (§3.7) | desktop |
| `new_cards_per_day` | 20 (confirmed) | phone |
| `day_starts_at` | 4 | phone |

**Phone storage note.** The Syncthing Android app cannot see Termux's private
`$HOME`. If that app is used, `lexicon` and `backup_dir` must live in
shared storage (`~/storage/shared/...`), while `learning_db` stays in Termux's
home for reliable locking and fsync. If Syncthing runs inside Termux, every
path can stay in `$HOME`. The design works either way, because every atomic
replace happens within a single directory's filesystem.

---

## 14. Decisions by category

### 14.1 State and data lifecycle

| Unit | Boundary | Why |
|---|---|---|
| Build | Staging file plus per-worker shard files, then one `os.replace`. All or nothing; the old file survives any failure, including a failed or killed worker | Spec: interrupted builds leave the previous file intact; partial files never reach the phone |
| No-op rebuild | Fingerprint fast path, then byte compare | Spec: identical inputs leave the file untouched (same mtime and hash) |
| Fetch, per file | `.part` file, then replace data, then replace sidecar | The previous download survives a failed fetch. A crash between the two replaces leaves a sha mismatch, which the build detects and turns into `unknown` |
| Grade | One transaction: card update plus review insert | Spec: a kill loses at most the card on screen |
| Add word | One transaction: word upsert, cards, deck memberships | Half a word's cards would leave orphan siblings and break dedupe |
| Save or write a phrase | One transaction: phrase plus card | Same reasoning |
| Edit, suspend, delete | One statement each | Nothing to compose |
| Backup | VACUUM INTO a temp file, then rename | Consistent snapshot; only complete files carry the final name |
| learning.db migration | Pre-migration backup (`VACUUM INTO`), then Alembic with one transaction per revision | The user's only copy of their data. A failed revision leaves the database at the last good revision, with the backup beside it |
| Build command (`BuildLexicon`, §11.2) | The build's own boundary (first row), then a read-only open for the info report | The report is not part of the publish. If reading it failed, the new file would stay published and the `Err` would say why it couldn't be read |

The use-case layer and click add no state of their own: no file, table or
transaction boundary.

**Auditable and replayable.** The review log is append-only, and every row
carries `state_before`, `state_after`, the scope and the timing. It holds
everything `fsrs.Scheduler.reschedule_card` or a future optimiser needs.
Every `learning.db` write, grades and `check` repairs included, also leaves
one `OperationGroup` with its operations' old values (§7.8). That is enough
to undo it later, although v1 delivers no undo (spec), so no row is ever
updated or deleted.

**Reversible.** Suspend is reversible. Delete is a soft delete, but v1 offers
no undelete (not requested). Card edits overwrite content without keeping
history, since the review log is what must be kept.

`lexicon.db` is disposable and rebuilt from sources. `learning.db` is the only
irreplaceable state.

### 14.2 Error propagation

The user has chosen a monadic `Result` model, the one kohle uses. It replaces
the per-function union return types an earlier draft of this design had.

**`Result[T, E]` lives in `harald/core/result.py`** (confirmed by the user),
the same path as kohle's `kohle/core/result.py`, so it can lift into the shared package (§7.7).
It has kohle's shape:
- a frozen dataclass built with `Result.ok(value)` / `Result.err(error)`;
- `is_ok` / `is_err`;
- `unwrap()` / `unwrap_err()`, which raise `RuntimeError` when misused. That
  is a bug, never control flow;
- `map`, `map_err`, `and_then`, `unwrap_or`.

One difference: `E` is a `TypeVar` bound to `Exception`. kohle's `is_ok`
means "no error stored", so an `Err(None)` would read as `Ok`. Bounding `E`
makes that unrepresentable to mypy.

**Error types are `Exception` subclasses used as values, never raised.** Each
carries the fields its message needs, and its `__str__` is the user-facing
message, as with kohle's domain errors. There is one `errors.py` per package,
with a family base class only where some caller handles the whole family:

| Module | Family | Members |
|---|---|---|
| `harald/config.py` | `ConfigError(path, detail)` | – |
| `lexicon/errors.py` | `LexiconError` | `LexiconMissing(path)`, `SchemaMismatch(found, expected, harald_version)`, `NotALexicon(path, detail)` |
| `infrastructure/infra_errors.py` (kohle's) | `InfrastructureError` | `UniqueViolation(constraint)`; plus `check_if_unique_constraint_failed(err, column)` |
| `learning/errors.py` | `LearningDbError` | `LearningDbTooNew(found, head)`, `NotALearningDb(path)`, `MigrationFailed(stage, detail)`, `StorageError(detail)`, `DeckNameTaken(name)` |
| `build/errors.py` | `BuildError` | `BuildLocked(lock)`, `SourceMissing(file)`, `SourceUnreadable(file, detail)`, `StagingNotSameFilesystem(staging, target)`, `FetchFailed(file, detail)`, `TaskFailed(task, detail)`, `TooFewEntries(found, minimum)`, `BuildFailed(stage, detail)` |
| `harald/editor.py` | – | `EditorFailed(command, detail)`, `InvalidInput(message)` |
| `learning/backup.py` | `BackupError` | `BackupNotConfigured`, `BackupFailed(detail)` |

**Every operation with a real failure mode returns a `Result`:**

| Function | Returns |
|---|---|
| `load_config` | `Result[Config, ConfigError]` |
| `open_lexicon` | `Result[Lexicon, LexiconError]` |
| `open_learning_db` | `Result[LearningDb, LearningDbError]` (§7.6) |
| `fetch_all` | `Result[FetchReport, FetchFailed]` |
| `build` | `Result[BuildReport, BuildError]` |
| `BuildLexicon.execute` (use case, §11.2) | `Result[BuildDone, BuildError \| LexiconError]` |
| each build job, inside its worker (§3.7) | `Result[JobOutput, TaskFailed]` |
| every `learning.db` use case (`CreateWordCards`, `SavePhrase`, `Grade`, `NextCard`, `SessionSummary`, `EditCard`, `SetSuspended`, `DeleteCard`, deck use cases) | `Result[…, LearningDbError]` through `UnitOfWork._run` → `DbTransaction.execute` (§7.7) |
| `DbTransactionContext.run(op)`, inside services | `Result[T, InfrastructureError]`, mapped to `LearningDbError` by the service with `map_err` |
| `edit_fields` | `Result[Option[dict[str, str]], EditorFailed]`. `Option.none()` means the user cancelled, an outcome rather than an error (§14.10) |
| validators passed to `edit_fields` | `Result[T, InvalidInput]` |
| `backup` | `Result[Path, BackupError]` |

**Functions and use cases with no failure mode return plain values:**
- `lookup_de`, `lookup_en`, `search_phrases`, `load_headword`;
- `execute` on the lexicon use cases (`LookUpGerman`, `QueryLexiconInfo`,
  and later `LookUpEnglish`, `LoadHeadword` and `FindPhrases`), which
  return what their services return;
- `render_*`, `answer_matches`, `check_*`;
- `PlanWordCards.execute`, whose refusals are data inside `CardPlan`;
- the importer's per-record mapping, where bad lines are counted and
  unmapped tag sets recorded (data quality is data).

Wrapping an infallible function in `Result` is exactly the unnecessary
abstraction the global rule forbids.

**Where arbitrary failure becomes `Err`.** These six seams are the only
broad catches. Each catches `Exception`, never `BaseException`, because each
holds partial state that must be rolled back or deleted before reporting:

| Seam | Partial state it protects |
|---|---|
| `infrastructure/uow.py` `DbTransaction.execute`, kohle's: commit on `Ok`; roll back on `Err` or on any exception (→ `Err(e)`); close the session | half a grade; half a word's cards |
| `infrastructure/transaction_context.py` `DbTransactionContext.run`, kohle's: `IntegrityError` → `UniqueViolation`, any other exception → `InfrastructureError` | a flush that failed mid-use-case; the use case gets an `Err` and `execute` rolls back |
| `learning/migrate.py`, the upgrade step | a half-applied revision (also rolled back by its own transaction) |
| `build/fetch.py`, the per-file download | a `.part` file; the previous copy must survive |
| `build/graph.py` `run_job`, inside each worker | the job's shard file. It also turns any worker exception into `Err(TaskFailed(task, detail))`, a picklable value, instead of relying on an exception crossing the process boundary |
| `build/run.py` `build`, the orchestrator | staging and shard files, plus the worker processes. Also converts `BrokenProcessPool` (a worker killed by the OOM killer, say) into `Err` |

Everywhere else, exceptions are caught by explicit type where they are
expected, or not caught at all:
- `sqlalchemy.exc.DatabaseError` in `open_lexicon`;
- `tomllib.TOMLDecodeError` and `OSError` in `load_config`;
- `FileNotFoundError` for the editor binary;
- `json.JSONDecodeError` per importer line;
- `sqlalchemy.exc.IntegrityError`, inside `DbTransactionContext.run`, which
  becomes `UniqueViolation` and then, in the service, `DeckNameTaken`.

Harald's code never catches `KeyboardInterrupt`. Cleanup runs in
`finally`. click then turns the interrupt into `Abort`, and `cli.main`
maps that to exit 130 (§11.1).

This reverses one earlier decision: runtime failures in `learning.db` writes are
no longer left to crash. They pass through `DbTransaction.execute`, come back
as an `Err`, and the TUI shows them while the session continues.

**AGENTS.md Overrides entry** for the user to add (this design doesn't edit
AGENTS.md):

> Broad exception catching at failure seams:
> `harald.infrastructure.uow.DbTransaction.execute` and
> `harald.infrastructure.transaction_context.DbTransactionContext.run` (the
> same two functions as kohle's Override), the upgrade step in
> `harald.learning.migrate`, the per-file download in
> `harald.build.fetch`, `harald.build.graph.run_job` and
> `harald.build.run.build` catch `Exception` rather than explicit types. This
> replaces the python-developer rule to catch explicit types. These are the
> seams where arbitrary failure is converted into an `Err` and partial state
> is rolled back or deleted: an open transaction, a half-applied migration, a
> `.part` download, staging and shard files, worker processes. An
> unanticipated exception escaping there would leave exactly the partial
> state the design exists to prevent. Ruff reports these as `BLE001`; they are
> deliberate. `BaseException` is never caught. Anywhere else, catch explicit
> types.

**How results compose, and where representation changes:**
- **Services map infrastructure errors** into Harald's families, as kohle's
  do: `ctx.run(op).map_err(lambda err: DeckNameTaken(name) if
  check_if_unique_constraint_failed(err, "deck.name") else
  StorageError(str(err)))`.
- **Within a layer**, short pipelines use `and_then` and `map`, for example
  `load_config(path).and_then(lambda c: open_lexicon(c.lexicon))`.
  Flows of three or more steps use early returns
  (`if r.is_err: return Result.err(r.unwrap_err())`), which read better than
  nested lambdas.
- **No `?`-style helper.** kohle's `resultify`/`q` raise an internal `Panic`
  exception to get early returns, which brings exceptions back as control
  flow to save one line per step.
- **At a seam**, `map_err` converts a lower-level failure into the caller's
  family when the caller's message must differ. Examples: `migrate.py` maps
  whatever Alembic raised, caught at the seam, into
  `MigrationFailed("upgrade", …)`; the orchestrator wraps a `TaskFailed` in
  `BuildFailed(stage=task, …)` so the message names the stage.
- **Use cases pass their services' errors through unchanged.**
  - They add no error family and no broad catch. The six seams stay six,
    and AGENTS.md's Override is unchanged.
  - A use case that composes two services returns the union of their
    families, as `BuildLexicon` does with `BuildError | LexiconError`.
    `exit_code` already matches on each class.
- **Absence is not failure.** A value that may be missing is an
  `Option[T]` at a public return. It sits inside a `Result` when the call
  can also fail, as in `Result[Option[StudyCard], LearningDbError]`.
  Success-or-failure with no value is `Result[None, E]`, never `Option[E]`
  (§14.10).
- **Source format to Harald records** happens only in `build/`.
- **SQL rows to model dataclasses** happens in `lexicon/` and `learning/`.
  Front-ends never see SQL, a `Session` or a `Row`. `lexicon/` returns
  dataclasses; `learning/` services, and the `learning.db` use cases that
  pass their results on (§11.2), return kohle-style mapped objects, which
  stay usable after the session closes (`expire_on_commit=False`).
- **`Result` to messages and exit codes** happens in `cli.py`, and
  click's usage errors and `Abort` are mapped in its `main` (§11.1).
  **`Result` to notifications** happens in `tui/`.

**How the CLI and TUI consume results.** Front-ends check `is_err`, and match
on the error's class only where cases are handled differently. `str(err)` is
always the message.

```python
res = open_lexicon(cfg.lexicon)
if res.is_err:
    return fail(res.unwrap_err())  # str(err) to stderr; returns exit_code(err)
dic = res.unwrap()


def exit_code(err: Exception) -> int:
    match err:
        case ConfigError() | LexiconError() | LearningDbTooNew() | NotALearningDb():
            return 2  # refusal
        case _:
            return 1  # the operation failed
```

- **TUI writes.** A handler such as `grade` calls `self.notify(str(err),
  severity="error")` on `Err` and keeps the card on screen, since the grade
  was rolled back. On `Ok` it advances.
- **Specific reactions.** Screens match on an error class only where the
  reaction differs: `DeckNameTaken` keeps the New-deck modal open with the
  message.
- **Startup errors never reach Textual.** `cli` opens config, lexicon and
  `learning.db` first.

### 14.3 Concurrency and ownership

- **Build** (desktop only): one main process plus a `ProcessPoolExecutor` of
  `build_workers` processes, using the forkserver start method (§3.7).
  - The main process owns the staging file's only write connection, the
    scheduler, and the reader threads (decompress and block scan per gzip
    source), which share nothing but bounded queues.
  - Each worker owns its shard file exclusively. The writer attaches a shard
    only after every job writing to it in that phase has finished, and
    detaches it after merging.
  - `flock` on `staging_dir/.lock` excludes a concurrent build.
  - Determinism rests on the id rules and `VACUUM INTO` (§3.5), not on a
    single thread.
- **TUI**: single-threaded, with **no worker threads in v1**. Textual's event
  loop calls synchronous functions. `learning.db` writes take milliseconds.
  Lookups run on Enter and measured 0.2–15 ms for candidate generation plus
  at most 52 ms of rerank on the desktop; the ORM adds about 4–5 ms once
  its statements are cached (§0). Engines are used, and sessions created,
  only on Textual's thread, and pysqlite keeps its default
  `check_same_thread`. If issue 009's measurements show lookups stalling the
  UI, the fix is a Textual `@work(thread=True, exclusive=True)` worker that
  opens **its own** session from the shared session factory, never a shared
  session.
- **Ownership**:
  - `HaraldApp` owns, for its lifetime, the one `Lexicon` (a read-only
    engine and a session factory; each `lexicon/` call opens and closes
    its own short session) and the one `LearningDb` (an engine and a session
    factory).
    Screens borrow them through `self.app`. Each use case gets a fresh
    `Session`, which `DbTransaction.execute` closes, as in kohle. No session
    outlives an action.
  - fsrs `Scheduler` objects are per process and immutable after
    construction.
  - Model dataclasses are frozen.
  - No module-level mutable state.
  - Use cases are objects built for one action.
    - A `UnitOfWork` lives for one `execute` and owns its session (kohle's
      single-shot shape).
    - A plain use case holds only the handles its constructor was given.
      Those handles belong to the front-end that opened them.
    - No front-end keeps a use case between actions, so nothing mutable
      outlives a call.
    - click's `Context` lives for one invocation.
- **Across processes on the phone**:
  - A second TUI or `harald backup` alongside the TUI: WAL plus
    `busy_timeout` serialise them. Two TUIs studying at once is not
    prevented, and SQLite keeps it safe; it just isn't a supported workflow.
  - `harald lookup` in another shell only opens `lexicon.db` immutable.
  - A Syncthing replacement of `lexicon.db` is a rename, so open readers
    keep the old inode.
- **Across machines**: the phone is the only writer of `learning.db`, and the
  desktop the only writer of `lexicon.db`. Both channels are one-way by
  configuration.

### 14.4 Reuse

The project is fresh. Only the uv scaffold exists (`pyproject.toml`,
`.python-version`, and `main.py`, which is deleted). So reuse means using what
already exists outside the project instead of rebuilding it, and factoring
shared pieces once inside it.

**Used instead of rebuilt:**
- wiktextract output, instead of a parser (spec);
- `fsrs`, instead of scheduling maths;
- Textual and Rich, instead of a UI layer;
- SQLite FTS5 and its porter tokenizer, instead of a search engine;
- `VACUUM INTO`, instead of a backup routine;
- stdlib `urllib`, `tomllib` and `fcntl`;
- click for the CLI (§11.1).

**Factored once, used twice or more:**
- `fold()`: build keys, lookup, phrase tokens;
- `fuzzy_deletes()` and `osa_within()`: German and English keys, build and
  runtime;
- `de_lemma_tokens(text, lemma_of)`: Tatoeba indexing at build time and
  queries at runtime. One function, so they cannot drift apart; only the
  key → lemma lookup is passed in, because the build reads through `sqlite3`
  and the runtime through the ORM;
- the `form_index` data, reused for phrase lemmatisation (the brief's
  suggestion), instead of adding a stemmer;
- `render.*`: CLI and TUI;
- `edit_fields()`: phrase entry and card editing;
- `answer_matches()`: Stammformen now, per-(tense, person) cards later;
- the deleted-card global criteria: every listing.

**Taken from kohle (the user's other Python project):**
- `Result[T, E]` with the same API, at the same path (`harald/core/result.py`);
- `Option[T]` with the same API, at the same path (`harald/core/option.py`),
  typed and with a picklable representation (§14.10);
- kohle's whole database infrastructure for `learning.db`, with the same names
  and shapes in mirrored modules: the PRAGMA connect hook and sessionmaker
  settings (as a factory), `DbTransactionContext.run`, `DbTransaction.execute`
  / `UnitOfWork`, `InfrastructureError` / `UniqueViolation`, declarative
  models feeding Alembic's `target_metadata`, the audit trail
  (`Operation` / `OperationGroup`, `crud_*`, `record_transaction_step`), and
  the same broad-catch Override. What's shared and what diverges is in §7.7;
- Alembic for the user's database, and a migration round-trip test modelled
  on kohle's `test_migration_downgrade.py`. Two deliberate differences: the
  script directory ships inside the package, because Harald runs installed on
  a phone rather than from a checkout; and Harald migrates programmatically at
  startup instead of by a manual `alembic upgrade`.
- its layering, front-ends → `use_cases/` → services (§11.2), and its CLI
  library, click. kohle's idioms come with it: `click.group`, `pass_obj`,
  and opening the database in the command rather than the group callback.
  One difference: Harald's commands return exit codes instead of raising
  `ClickException`, because they need 2 and 130 (§14.8).

**Reusable by the next comparable work:**
- The read → parse job → shard → merge pattern in `build/` (§3.7). A new
  source is one reader, one parse job and one merge node.
- The content dataclass, checker and `CARD_SCOPE` entry pattern. That is how
  issue 013's conjugation card slots in.
- One use-case module per area (§11.2). A new command is a click function
  plus a use case in its area's module, and the TUI screen for the same
  action calls the same use case.

### 14.5 Extension points

| Point | Contract | Intended client |
|---|---|---|
| `lexicon.db` schema + `SCHEMA_VERSION` (+ `fold`, `fuzzy_deletes`, `de_lemma_tokens` as specified here) | plain tables plus standard FTS5; the version must match exactly | the Rust rewrite, which will read the same file |
| `learning.db` schema + Alembic revisions (`HEAD` constant) | forward-only at runtime; each revision has a tested `downgrade()` | later Harald versions; the Rust rewrite (reads `alembic_version`); open question 1's export, if accepted |
| `fsrs_params` table + `CARD_SCOPE` | an absent row means defaults | the FSRS optimiser (a non-goal for v1) |
| `card_type` + content dataclass + checker | add a type: a dataclass, a checker, a scope entry, a study widget (CHECK already lists `conjugation`) | issue 013 |
| `build/` graph nodes | a parse job writes stage tables keyed by `(stream, seq, local_id)`; a merge node assigns final ids by rule | a future source |
| `harald.use_cases` (§11.2) | front-ends call only these. Their signatures and returned dataclasses stay put when a service changes underneath them (a Core fallback, §14.9, or a Rust hot path) | the CLI, the TUI (009), new commands |

**Deliberately none**: no plugin system, no Scheduler interface, no Renderer
interface, no repository or ORM layer. The global "no unnecessary
abstractions" rule applies, and the spec explicitly rejects the first three.

### 14.6 Build vs. buy

| Component | Decision | Evaluated | Why |
|---|---|---|---|
| Wiktionary data | **buy**: kaikki wiktextract dumps | own Wikitext parser | spec; parsing was only ever the price of the data |
| Scheduling | **buy**: `fsrs` 6.3 | – | spec; pure Python |
| TUI | **buy**: Textual 8 | – | spec; `suspend()` exists |
| CLI parsing | **buy**: click 8.3 (revised 2026-10-20; was stdlib argparse) | argparse, typer | the user's choice, matching kohle (confirmed 2026-10-24). Measured (§0): about 10 ms on top of what `lookup` already imports, inside noise; a pure-Python wheel. It gives declared options with help, `envvar=` for `HARALD_CONFIG`, and nested groups for `check accept\|keep\|relink` (§8.4). typer is a layer over click that adds annotation introspection at startup and nothing Harald needs |
| Rendering | **buy**: Rich (already a Textual dependency) | hand-formatted print | one width-adaptive rendering for both front-ends, from 40 columns up, with Rich doing the wrapping |
| Fuzzy candidates | **build**: prefix-7 symmetric-delete table | FTS5 trigram, trigram table, full delete-1, rapidfuzz in memory | measured (§0): trigram 45–1,553 ms; full delete-1 313 MB; in memory 790 ms load. Prefix-7: 130 MB, ≤15 ms, and catches tail typos |
| Fuzzy distance | **build**: ~30-line banded OSA | rapidfuzz | rapidfuzz has no Termux-installable wheel, so it would need a C++ build on the phone; pure-Python OSA measured at ≤52 ms worst case |
| Phrase search | **buy**: SQLite FTS5 (porter for English) | Whoosh, tantivy-py | FTS5 is present on both machines (Termux libsqlite has `--enable-fts5`); no dependency; whoosh is unmaintained; tantivy is compiled |
| German phrase normalisation | **build**: lemmatise via the form index | snowballstemmer (pure), PyStemmer (C) | stemming can't relate `lief` to `laufen`; the form index already exists |
| Downloads | **buy**: stdlib urllib | requests, httpx | GET with conditional headers and streaming is all it needs |
| Config and paths | **build**: XDG, about 10 lines, with tomllib | platformdirs | platformdirs detects Android under Termux and returns app-private paths instead of `~/.local/share` |
| Atomic writes | **build**: `os.replace` + fsync | atomicwrites | a few lines; the library is archived |
| Editor loop | **build** | `click.edit` | needs a validation-reopen loop, cancel on byte-identical text, and to run inside `App.suspend()`. `click.edit` also runs the editor through a shell and reports failure as a `ClickException`, which is CLI vocabulary inside the TUI (§0). "Would pull in click" no longer applies after §11.1 |
| Migrations (`learning.db`) | **buy**: Alembic | a hand-rolled script list with `PRAGMA user_version` (this design's earlier draft); yoyo | the user's choice, matching kohle. `batch_alter_table` performs SQLite's table rebuild for CHECK and column changes, and downgrades are testable. Installs as pure Python on Termux with SQLAlchemy ≥ 2.1 (§0) |
| `learning.db` access | **buy**: SQLAlchemy 2.1 ORM, through kohle's infrastructure (§7.7) | stdlib `sqlite3` with hand-written SQL (this design's earlier draft) | the user's decision: Harald and kohle will converge on one shared db package, so `learning.db` must use kohle's stack now. Costs +241 ms on TUI start (desktop) |
| `lexicon.db` access | **buy**: SQLAlchemy ORM with declarative read-only models (same style as `learning.db`), Core as the measured fallback | stdlib `sqlite3` (this design's previous revision); SQLAlchemy Core only | the user's decision: one data-access style, readable in review. The startup cost (cold lookup-shaped flow 205 ms with `sqlite3` against 827 ms with the ORM, slower machine state) is accepted under the §14.9 budgets |
| Audit trail | **buy**: kohle's (`Operation` / `OperationGroup`, `crud_*`), with Harald filling `state` / `field` through a `before_flush` hook | a custom undo log; SQLAlchemy-Continuum (versioned tables) | the user wants kohle's mechanism for later rollbacks and undo. Continuum would add shadow tables and a dependency for one feature v1 doesn't deliver |
| Benchmarking | **build**: `dev/bench/bench.py` with committed budgets and baselines | pytest-benchmark, asv | needs cold-process wall times, phone runs without a test runner, machine-state normalisation, and budget gates per metric. A ~200-line script against committed JSON does that; asv's web reports and pytest-benchmark's in-process focus don't fit cold-start measurement |
| Error model and `Option` | **build**: `harald/core/result.py` and `harald/core/option.py` (2026-10-24), each a small port of kohle's | `result` (rustedpy; last release June 2024), `returns` (dry-python; maintained, with `Maybe`, but a family of containers plus a mypy plugin) | the user's choice of kohle's model; the same API across the user's projects; no extra dependency on the phone. `option.py` differs from kohle's only in typing and its picklable representation (§14.10) |
| Parallel build | **buy**: stdlib `concurrent.futures.ProcessPoolExecutor` (forkserver) plus SQLite `ATTACH` | `multiprocessing.Pool.imap`; joblib, Dask, Ray | needs a bounded in-flight window, offset-based ordering and cancellation on the first failure, and the stdlib executor offers `cancel_futures`. `Pool.imap` consumes its input eagerly, which means unbounded memory on a 25 GB stream. The others are heavy dependencies for one desktop command |
| JSON speed | stdlib `json` | orjson | measured: the English parse is 29 s inline and 16 s with workers, while the critical path is reading the gzip stream (45 s). A faster parser would not shorten the build |

### 14.7 Abstractions introduced, each with its forcing problem

1. **`lexicon/schema.py` as the shared contract.** The importer and runtime
   must agree on DDL and interpretation, and the spec demands a version
   refusal.
2. **`build/records.py` dataclasses.** "The importer is the only module that
   knows where the data came from": parse jobs translate formats into records,
   so the merge nodes, the publish logic and the determinism rules stay
   format-free. Mapping can be unit-tested without a database or a pool.
3. **The `headword` table.** German definitions must be grouped once per
   (word, pos) across entries, and results are presented that way.
4. **Per-type content dataclasses in a JSON column.** Each card must carry its
   own type-specific copy. Typed columns would be mostly NULL, and the
   dataclass fields double as the edit template.
5. **`Result[T, E]` (`harald/core/result.py`) with `Exception` subclasses as error
   values.** The user's chosen error model, shared with kohle. Distinct
   failures need distinct messages (the schema mismatch must name both
   versions), and `map_err`/`and_then` compose them across layers without
   raising. Kept to kohle's API with no additions, and no `resultify`/`q`
   helper. kohle's `Option` type was first rejected here as duplicating
   `T | None`. It is now ported too (item 22; confirmed by the user
   2026-10-24).
6. **`render.py`.** CLI and TUI output must match and fit any width from 40 columns up (§6). A
   Renderer abstraction is banned, so a shared concrete rendering into
   Textual's native type is what's left.
7. **`edit_fields()`.** Two callers (issues 020 and 017) with the same needs:
   a validation-reopen loop, cancel when unchanged, TUI suspend.
8. **The deleted-card global criteria** (a `do_orm_execute` listener with
   `with_loader_criteria`). "Removed from every listing" must hold everywhere,
   so the filter lives in one place, and an ORM query that forgets it still
   can't list deleted cards.
9. **Alembic for `learning.db`** (`learning/migrate.py`, `learning/migrations/`). `learning.db`
   holds irreplaceable data that future versions must evolve in place, and
   SQLite schema changes such as a new CHECK need a table rebuild, which
   `batch_alter_table` does. `HEAD` is a constant so that a normal start
   needn't import Alembic at all.
10. **`search_key` / `key_headword` / `fuzzy_delete`.** Typo-tolerant lookup
    on a phone in milliseconds.
11. **`CARD_SCOPE`.** The spec wants scope splits to be a one-line change.
12. **kohle's `UnitOfWork` / `DbTransaction` / `DbTransactionContext`**
    (`harald/infrastructure/`). Forcing problems: every multi-statement write
    must roll back whole; arbitrary failure must come back as an `Err`
    (§14.2); and the user is converging Harald and kohle on one shared db
    package. Taking kohle's exact shapes now makes that a lift, not a
    rewrite. Use cases are `UnitOfWork` subclasses because that is kohle's
    shape.
13. **The build task graph (`build/graph.py`) with per-worker shards and
    offset-based ids.** Forcing problems:
    - the user requires parallel population;
    - SQLite allows one writer per file;
    - the output must stay byte-identical whatever the worker count and
      completion order;
    - returning rows to the single writer hit a measured ceiling.

    It is a fixed list of nodes and dependencies in code, not a general
    workflow engine.
14. **Declarative models for `learning.db`** (`learning/models.py`). Alembic's
    `target_metadata` and autogenerate need them, and they are kohle's shape.
15. **`make_engine(path, *, pragmas=None, read_only=False)` / `make_session_factory(engine)`.** kohle
    builds a module-global engine with a hardcoded URL. Harald has two
    databases, a configurable path, and a lazy-import rule. A future shared
    package would have to settle this divergence (§7.7, informational).
16. **Declarative read-only models for `lexicon.db` (`lexicon/models.py`),
    private behind `lexicon/`.** Forcing problems:
    - the user wants one ORM style for both databases;
    - the build and the runtime need a single schema definition (the build
      runs `create_all`, and its stage tables derive from the same models);
    - a later Core or Rust swap must stay local, so callers get dataclasses,
      not sessions.
17. **The benchmark harness with budgets and baselines** (`dev/bench/`). The
    user made accepting the ORM's startup cost conditional on regular
    measurement with explicit fallback thresholds, and the observed 2×
    machine-state drift means comparisons have to be normalised rather than
    eyeballed.

18. **The audit trail's before-state snapshots** (a `before_flush`
    listener filling `Operation.state` / `field`). Forcing problem: the user
    wants elegant undo and rollback later, and kohle's rows record only that
    something happened. The hook fills kohle's existing columns without
    changing its decorator API.
19. **Width-adaptive renderables** (`__rich_console__` choosing narrow or
    wide by `max_width`). Forcing problem: the phone is portrait at 40
    columns while desktop and SSH stay 80 or more, and the CLI and TUI must
    keep sharing one rendering.
20. **The `unlinked` link state and `check_ack` fingerprints** (§8.3).
    Forcing problem: "keep own copy" must silence a flag until upstream
    changes again, without re-flagging on every rebuild.

21. **The use-case layer (`harald/use_cases/`, §11.2).** Forcing
    problems:
    - the user wants front-ends to call use cases, never the lower-level
      modules, as in kohle;
    - the CLI and the TUI (009) must get the same composition;
    - the composition that lived in `cli.py` (build, then open and report;
      passing `SCHEMA_VERSION` to `load_info`) belongs below a front-end.

    Every use case is a class with kohle's call shape,
    `X(handles).execute(values)`: a `UnitOfWork` subclass for a
    `learning.db` transaction, a plain class otherwise. That is the user's
    decision (2026-10-24), so that front-ends read one shape. There is no
    base class, protocol or registry of its own. `BuildDone` exists because
    `BuildLexicon` returns two things.

22. **`Option[T]` (`harald/core/option.py`, §14.10).** Forcing problems:
    - the user wants absence stated in return types rather than implied by
      `T | None`, composed like `Result`, and turned into a `Result` with
      `ok_or`;
    - the planned `NextCard` and `edit_fields` returns, where none is an
      outcome rather than an error.

    It is kohle's API, typed, with a picklable representation and one
    addition that has callers (`from_optional`). Confirmed by the user
    2026-10-24.

Nothing else: no service classes, no use-case base class or interface
beyond kohle's `UnitOfWork`, no repository interfaces, no event bus, and no
dependency-injection container.

### 14.8 Alternatives rejected

| Alternative | Why rejected |
|---|---|
| One `item`/note table for words and phrases | The brief already rejected a unified note model. Word and phrase snapshots share no columns, so one table would be mostly NULLs under kind-dependent CHECKs. Two tables plus an exactly-one FK pair, as the brief proposed |
| Storing `lexicon.db` row ids on cards | Ids change on every rebuild (kaikki has no stable ids). Re-resolvable hints instead |
| Persisted link status, refreshed at startup | The spec puts nothing at startup, and a stored status goes stale. Computed in `check` |
| `etymology_number` as the discriminator | Measured: two of Band's three entries share `etymology_number` 1 |
| Building in place, or a temp file inside the synced folder | A partial file would reach the phone |
| Fingerprint or build time inside `lexicon.db` | Would change bytes without changing content, and Syncthing would resend |
| Relying on byte determinism alone, without the fast path | Kept as the safety net. Without the fast path, every no-op costs minutes of rebuild |
| WAL for `lexicon.db` | Readers would need `-shm`/`-wal`. Rollback mode plus `immutable=1` is lock-free |
| Copy fallback when staging is on another filesystem | Not atomic. A clear error instead |
| Trigram fuzzy (FTS5 or a table), in-memory rapidfuzz, full delete-1 | Measured too slow or too big (§0) |
| rapidfuzz as a dependency | No Termux wheel. A compiled build on the phone for a rerank that pure Python handles |
| Snowball stemming for German phrase search | Misses strong verbs. The form index already lemmatises |
| Full Tatoeba exports (sentences.tar.bz2 + links.tar.bz2, 370 MB) | The per-language files carry the same pairs in 40 MB |
| Indirect Tatoeba translations through a third language | Lower quality. Direct `deu-eng` links give 585k pairs |
| Using German-edition gender or forms as a fallback | The spec scopes the German edition to definitions and examples. One grammar source keeps refusals predictable |
| Stored "buried" flags | Computed from the review log: nothing to clean up, survives kills |
| In-memory session counters for the summary | `session_id` in the review log makes the summary exact and durable |
| Hard delete keeping orphan review rows | Breaks foreign keys. Soft delete keeps history intact (spec) |
| Hard/Easy choice after a correct checked answer | Breaks the single-keypress article card. Correct is Good, wrong is Again |
| Case-insensitive typed checking | The spec says exact, except for umlaut transliteration |
| Inline TUI inputs for card editing | Long German definitions in a one-line Input at 80 columns are unusable on a phone. The `$EDITOR` template is reused |
| Search as you type in the TUI | Would force worker threads and cross-thread connections. Search on Enter is enough until issue 009 shows otherwise |
| Textual worker threads in v1 | Measured lookup cost doesn't need them (§14.3) |
| argparse (previous revision) | Reversed by the user (confirmed 2026-10-24) for click, kohle's CLI library. The startup cost that justified argparse measured about 10 ms on top of `lookup`'s imports, inside noise (§0) |
| typer | A layer over click that adds annotation introspection at startup. Nothing in it is needed |
| click's standalone mode | It turns Ctrl-C into "Aborted!" and exit 1. Non-standalone mode, with `main` mapping `Abort` to 130, keeps §11's exit codes |
| Raising `click.ClickException(str(err))`, as kohle does | Always exit 1. Harald needs 2 for refusals, and a subclass per exit code would duplicate `exit_code` |
| Loading the config in the click group callback | click runs it before a subcommand parses its arguments, so a broken config would break `harald <command> --help`. kohle's `_LedgerCommand` exists for the same reason |
| kohle's `_LedgerCommand`, with handles injected through `obj` | Harald's CLI tests run the real command in a subprocess against a fixture-built lexicon, and use cases are tested without click. The injection seam would have no caller |
| A `harald/services/` package, as in kohle | `lexicon/`, `build/` and `learning/` already are the service layer, each with its database's models and errors. A `services/` tree would split each database's code across two trees and blur `lexicon/`'s package boundary (§4.4) |
| Use cases inside the domain modules (previous revision, §7.7) | Reversed by the user (confirmed 2026-10-24): one `use_cases/` layer to read, as in kohle |
| Plain functions for non-transactional use cases (kohle's `init_ledger` shape; this design's 2026-10-20 draft) | Rejected by the user on 2026-10-24. Every use case is a class with `execute()`, so front-ends read one call shape |
| A base class or `Protocol` for the plain use-case classes | Nothing calls use cases generically, so it would have no caller. `UnitOfWork` exists because it carries the transaction |
| `UnitOfWork` for `lexicon.db` reads | `lexicon.db` is read-only and immutable, with nothing to commit or roll back. `DbTransaction` would commit and add audit rows that belong to `learning.db`, and `lexicon/` hides its sessions by design (§4.4) |
| Moving `build.run.build` into `use_cases/build.py` | It is the sequence that carries the rebuild guarantees, tested as one unit by 004a and 004b, and a broad-catch seam named in AGENTS.md. Splitting it across layers gains nothing and would need an AGENTS.md change |
| A forwarding `BuildLexicon`, with the CLI opening the lexicon and printing the info itself | It leaves the composition in the front-end, which the use-case layer exists to remove |
| One `use_cases` module, or re-exports from `use_cases/__init__.py` | `lookup` would import `harald.build` (and, from 010, `harald.learning`), breaking the import-hygiene rule (§11) |
| Front-ends calling `harald.lexicon` directly where a use case would only forward | The user's rule is that front-ends call use cases. One place to look is worth more than saving a small class |
| platformdirs | Android detection under Termux gives surprising paths |
| Scheduler abstraction, Renderer abstraction, SM-2, per-deck FSRS | Spec non-goals (the old design's choices) |
| Hand-written two-layer Wikitext parser; seed CSV of irregular verbs | Spec non-goals (the old design's choices) |
| Download resume (HTTP Range) | Not required. Restarting a failed fetch is acceptable for a deliberate desktop step |
| A hand-rolled migration list with `PRAGMA user_version` (earlier draft) | Replaced by Alembic at the user's request (§7.6) |
| Plain `sqlite3` for `learning.db`, SQLAlchemy only as Alembic's engine (earlier draft) | Reversed by the user: Harald and kohle will share a db package, so `learning.db` uses kohle's SQLAlchemy infrastructure (§7.7). The import cost it was avoiding (+241 ms at TUI start on the desktop) is accepted |
| Stdlib `sqlite3` for `lexicon.db` reads (previous revision) | Rejected by the user in favour of one ORM data-access style. The cost is accepted under budgets, with a per-path Core fallback (§14.9) |
| Core `Table`s with read-only classes mapped onto them for `lexicon.db` (previous revision) | Dropped by the user for one declarative style across both databases. The build imports the ORM to run `create_all`, which costs nothing on the desktop. The cost: a Core fallback can no longer drop the `sqlalchemy.orm` import from the one-shot path (§14.9) |
| Stage tables declared as separate DDL in the build | That would be a second copy of every column list. Derived from the models instead (§3.5) |
| Mapping the FTS5 virtual tables as ORM classes | `MATCH`, `rank` and `bm25()` have no ORM expression, `create_all` can't emit `CREATE VIRTUAL TABLE`, and the queries only need rowids. `text()` through the session instead |
| Default lazy relationship loading | It invites N+1 queries in render loops. `lazy="raise"` with explicit `selectinload` makes every load visible |
| One long-lived `Session` for `lexicon.db` in the TUI | The identity map would grow across lookups. A short session per call, converted to dataclasses before closing, instead |
| Comparing benchmark runs in raw milliseconds | The desktop's bare-Python baseline drifted 21 → 51 ms between sessions. Cold metrics are normalised by `cold.python` |
| Skipping kohle's audit trail (previous revision) | Reversed by the user, who wants it for later rollbacks, undo and deletes. Measured cost: +0.2–0.9 ms per grade (§0) |
| Grades outside the audit (review log only) | Undo would have to walk two logs. Audited grades cost +0.2–0.9 ms (§7.8) |
| Storing the after-state in `Operation` | Derivable from the current row or the next operation's before-state |
| Skipping proper nouns (previous revision) | Reversed by the user: Deutschland, Berlin, Rhein and Müller must be findable. Measured cost is small (+11.6 MB, +4.6% fuzzy rows; 0.38% of single-edit typos spell a name exactly), and ranking and labels keep them out of the way |
| Excluding proper nouns from fuzzy candidates | Measurement showed no real precision cost (above), so the extra rule isn't worth it |
| Landscape on the phone (the earlier assumption) | The user chose portrait. Narrow layouts at 40 columns instead (§12.8) |
| Paging tenses at 40 columns | Stacked tense blocks scroll naturally and need no extra keys (§6) |
| Re-linking automatically when an unlinked entry reappears | Upstream changes are never applied silently. The card is re-listed with relink offered (§8.3) |
| Resetting the schedule on every accepted change | Rewording a self-graded card rarely changes what is recalled. Reset is the default only for checked cards whose answer changed (§8.3) |
| kohle's module-global engine with a hardcoded URL | Harald has two databases, a configurable path, and a lazy-import rule. An engine factory instead (§7.7) |
| The `live_card` SQL view | With ORM access, SQLAlchemy's global criteria put the filter on every query, without mapping a view as well |
| SQLAlchemy for the build's writes | Bulk `executemany`, ATTACH merges and `VACUUM INTO` on the desktop, where §3.7 measured the single writer as the bottleneck. The schema still comes from `Base.metadata.create_all` (§3.5) |
| An explicit `BEGIN IMMEDIATE` per write (earlier draft) | kohle's default pysqlite transaction handling, so `DbTransaction` behaves the same in both projects. With a single writer, an IMMEDIATE lock has nothing to guard against |
| Alembic for `lexicon.db` | Rebuilt from scratch every time and never upgraded in place. An `alembic_version` table would add bytes to a file that must change only with its content. `SCHEMA_VERSION` equality is the whole check |
| `harald.learning:migrations` resource-form script location | Alembic's own source marks that code path untested. An absolute path from `__file__` instead |
| Offline (`--sql`) migrations | Migrations only run against real files, and SQLite batch revisions would need hand-kept `copy_from` table snapshots to render offline |
| Per-function union return types (earlier draft) | Replaced by `Result[T, E]` at the user's request (§14.2) |
| kohle's `resultify`/`q` helper | `q` raises an internal `Panic` to imitate `?`, which brings exceptions back as control flow |
| Leaving out kohle's `Option` (previous revision: "`T \| None` does what `Option` does") | Reversed by the user (confirmed 2026-10-24): it states absence in the type, composes, and converts to a `Result` (§14.10) |
| kohle's `object()` sentinel inside `Option` | It loses its identity in a pickle round trip, so an unpickled `none()` reads as Some (measured, §0). A `bool` flag is used instead |
| `Option` everywhere, fields and parameters included | Fields mirror nullable columns and JSON `null`, so absence keeps one representation. `Mapped[Option[T]]` would need a `TypeDecorator`, and an `Option` parameter makes every caller wrap (§14.10, rule 4) |
| `Option` in hot loops and kernels | It adds about 0.5 µs per Some (§0): about 20% of `_table_slot` and 1–10% of `osa_within`. The kernels are Rust candidates whose FFI maps to `T \| None` anyway |
| `Option[BuildError]` for `Jobs._reap` | Success-or-failure is `Result[None, BuildError]`. An `Option` would put failure in the Some arm |
| Wrapping `EntryRecord \| FormOfRecord \| None` in `Option` | The caller dispatches on all three arms. `Option[A \| B]` adds an unwrap before the same dispatch |
| `Result.ok_option()` and `Option.to_optional()` | No caller. `ok_option` would drop an error, which the error model never does |
| A `__bool__` on `Option` | One meaning `is_some` would silently change `if x:` for a former `T \| None` holding `0` or `""`. One that raises would catch the mistake only at runtime. mypy's `truthy-bool` catches it statically instead |
| Letting runtime `learning.db` failures crash | Superseded by `DbTransaction.execute`, which rolls back and returns an `Err` |
| A single-process sequential importer (earlier draft) | Replaced by the task graph at the user's request. Measured components put it at about 2.5× faster (§3.7) |
| Returning parsed rows to the writer for every task | Measured ceiling: the English parse plateaued at 16 s for any worker count above 2, and the fuzzy index took 8 s against 4 s with shards |
| Python line iteration for the prefilter | 72 s, against 45 s for a block scan with a decompression thread (measured) |
| Splitting the gzip stream across processes; `pigz -dc` | A single-member gzip stream can't be split. zlib in a thread is already near its 33 s floor |
| Threads instead of processes for parsing | `json.loads` holds the GIL |
| The `fork` start method | Reader threads are already running when the pool starts. Forking a threaded process can deadlock |
| Moving the block scan into its own process | Deferred. It would copy 2 GB of chunks across one more process boundary. Revisit only if issue 004b's timings show main-process GIL contention on the critical path |

### 14.9 Performance: benchmark harness, budgets, and the Core fallback

The user accepted the ORM's startup cost on one condition: regular
benchmarking against explicit budgets, so that any path that becomes
abysmal falls back to Core. This section is that contract.

**Harness layout** (`dev/bench/`). The script, the query set, the budgets
and the two baselines are committed. `results/` is gitignored, and
`.gitignore` gains `dev/bench/results/`:

```
dev/bench/bench.py              uv run python dev/bench/bench.py --machine desktop|phone --label slice-010
                                  [--lexicon PATH] [--learning-db PATH] [--compare dev/bench/baseline-desktop.json]
dev/bench/queries.toml          the fixed query set (below)
dev/bench/budgets.toml          target and abysmal per metric, per machine (the table below)
dev/bench/baseline-desktop.json accepted reference run on the desktop
dev/bench/baseline-phone.json   accepted reference run on the phone (first written by issue 009)
dev/bench/results/              gitignored: one JSON per run, <date>-<machine>-<label>.json, plus <…>-importtime.txt
```

**Inputs.**
- `--lexicon`: a real built `lexicon.db`. On the desktop that is the
  published file; on the phone, the synced one. Without it, the harness
  builds the fixture lexicon.
- `--learning-db`: copied to a temporary file before anything runs, so the real
  `learning.db` is never written. Without it, the harness generates a fixture
  with 2,000 cards and their reviews.

**The fixed query set** (`queries.toml`):
- German lookups: `Hund` (exact), `lief` (inflected), `schnel` (fuzzy),
  `verschlimbessern` (worst-case compound), `ueberzetsen` (two edits);
- English: `use`;
- phrases: `repeats itself`, `and the pattern then repeats itself`,
  `make use of`;
- headwords to load: Band, laufen, anrufen.

The set is fixed so runs stay comparable. Changing it means writing a new
baseline.

**Metrics.** Each records the median and p90.
- Cold metrics run as fresh processes (`subprocess`, N = 9).
- Warm metrics run in-process after one warm-up run (N = 200, or N = 50 for
  the 3,000-row reads).

| Metric | What it measures |
|---|---|
| `cold.python` | `python -I -c pass`. The machine-state reference: §0 saw it drift from 21 ms to 51 ms between sessions on the same desktop |
| `cold.lookup` | wall time of `harald lookup laufen` and of `harald lookup verschlimbessern`, stdout discarded |
| `cold.tui_start` | wall time to the first rendered Home screen. `HARALD_BENCH_EXIT_ON_READY=1 harald` runs the app headless at 40×24 (the phone's portrait shape; the desktop run also records 80×24) and exits from `call_after_refresh` in the Home screen's `on_mount` |
| `warm.fuzzy_candidates` | the candidate query alone, per query in the set; the worst query is reported |
| `warm.phrase_search` | `search_phrases` end to end, all tiers, per query |
| `warm.headword_load` | `load_headword` (ORM entity load plus conversion), Band-sized |
| `warm.grade` | the `Grade` use case, including its audit group (§7.8), on the temporary `learning.db` copy (WAL, `synchronous=FULL`) |
| `warm.read_3000_columns` | a 3,000-row column select through the session (the shape of the worst fuzzy candidate set) |
| `warm.read_3000_entities` | 3,000 ORM entities (the Cards-screen shape once the deck has grown) |
| `warm.lookup_e2e` | `lookup_de` including rerank. Informational: it catches algorithmic regressions |

**Each result file also records** the Harald version, git commit, Python
version, SQLAlchemy version and whether its C extensions are active, the
SQLite version, the machine label, and the first 12 characters of the
lexicon's sha256.

**Budgets.**
- *Target* is what the design expects. *Abysmal* is the point where a path
  falls back to Core.
- The desktop rows come from §0's measurements with room for the observed
  2× machine-state swing.
- The phone rows are the desktop rows × about 4.
- **The user confirmed these budgets as proposed, with no further tuning**,
  since a Rust port is planned. Issue 009 records the phone baseline against
  them.
- Abysmal sits where an action starts to feel broken: about 100 ms for a
  keypress response on the desktop and 300 ms on the phone. For the one-shot
  command, it's the point where it is no longer clearly faster than starting
  the TUI.

| Metric | Desktop target | Desktop abysmal | Phone target | Phone abysmal |
|---|---|---|---|---|
| `cold.lookup` | ≤ 0.6 s | > 1.5 s | ≤ 2 s | > 4 s |
| `cold.tui_start` | ≤ 1.2 s | > 3 s | ≤ 3 s | > 6 s |
| `warm.fuzzy_candidates` (worst query) | ≤ 5 ms | > 25 ms | ≤ 20 ms | > 100 ms |
| `warm.phrase_search` (per query) | ≤ 15 ms | > 75 ms | ≤ 60 ms | > 300 ms |
| `warm.headword_load` | ≤ 10 ms | > 50 ms | ≤ 40 ms | > 200 ms |
| `warm.grade` | ≤ 15 ms | > 100 ms | ≤ 50 ms | > 300 ms |
| `warm.read_3000_columns` | ≤ 15 ms | > 60 ms | ≤ 60 ms | > 250 ms |
| `warm.read_3000_entities` | ≤ 50 ms | > 200 ms | ≤ 200 ms | > 800 ms |

For reference, measured on the desktop (§0): the cold lookup-shaped flow
took 0.83 s in the slower machine state (an estimated ~0.35 s in the faster
one); grade, 6.4 ms, and 8.2–8.5 ms with its audit group in another session;
3,000 rows, 11 ms as columns and 37 ms as entities.

**Comparing runs.** `--compare BASELINE` prints, per metric, the value, the
baseline, their ratio and the budget status.
- **Budget breach:** the metric's median exceeds its abysmal budget. The
  command exits non-zero, so a release step can gate on it.
- **Regression:** the metric is more than 1.5× its baseline. Cold metrics are
  first divided by the `cold.python` ratio between the two runs, so a slow
  machine day doesn't read as a regression. A regression is reported for
  investigation and does not fail the run.

**When to run it:**
- at every slice boundary that touches a measured path (the issues are
  listed in §15);
- before every release;
- whenever a dependency changes (SQLAlchemy, Textual, Python, Termux's
  Python or SQLite);
- on the phone after issue 009, then at least before each release.

A run's numbers survive only if they are promoted to a baseline. A new
baseline is written only deliberately (`--write-baseline`), with the
reason in the commit message.

**The fallback rule, per path.**
- **Trigger:** a path's metric exceeds its abysmal budget on the machine it
  is budgeted for in two runs on different days (a guard against noise), or
  the user calls it unusable.
- **Action:** swap that path to Core, inside its package only. Public
  signatures and result dataclasses don't change.
  - **Candidates, keys and phrase ids:** `session.execute(stmt)` becomes
    `connection.execute(stmt)` on the same `select()`/`text()`, with
    identical SQL (§4.4). This saves session overhead only.
  - **Headword load, English → German, German block:** ORM entity loads
    become column selects assembled into the same dataclasses. Measured: 33
    rows took 1.3 ms as entities against 236 µs with Core.
  - **Cards listing** (`warm.read_3000_entities`): a column select into the
    listing dataclass.
  - **`warm.grade`:** this is fsync-bound (6.4 ms). If it breaches, look at
    WAL and fsync first; the ORM is not the suspect.
  - **`cold.lookup`:** even with every lookup path on Core (selects over
    `Model.__table__.c`), the declarative models still import
    `sqlalchemy.orm` and define their classes. The fallback saves only
    `configure_mappers` (about 23 ms) and the ORM's part of compiling and
    hydrating results. §0's breakdown puts that at roughly 10% of the ORM's
    extra cold cost. **If `cold.lookup` breaches, the remaining options are a
    Core-only table module for the one-shot path, or stdlib `sqlite3` for
    it. Each brings back something the user has rejected (the
    tables/models split, or the access-style split), so both are the
    user's call, not automatic steps.**
- **What stays either way:**
  - `lexicon/models.py`, which still defines the schema for the build, its
    stage tables and the drift check;
  - the engine and session factories;
  - the mapped classes for paths that are within budget;
  - all of `learning.db`'s kohle infrastructure, which is the shared-package
    path.

**`python -X importtime` guidance.**
- Record the import tree of a cold lookup:
  `python -X importtime -c "from harald.cli import main; main(['lookup', 'laufen'])" 2> dev/bench/results/<…>-importtime.txt`.
  Then sort by the cumulative column: `sort -t'|' -k2 -n -r … | head -40`.
- What to look for:
  - `textual`, `alembic`, `fsrs`, `harald.learning` or `harald.build` showing up
    under a lookup;
  - `alembic` under a normal TUI start;
  - a new heavy import arriving with a dependency bump.
- The same import set is also checked deterministically, not by timing, in
  the import-hygiene test of §11.
- **Install with compiled bytecode** (`uv tool install --compile-bytecode`).
  Otherwise the phone's first run compiles every SQLAlchemy and Textual
  module. The harness discards its first cold run, so it measures warm
  bytecode.

**First measurements on the real lexicon (2026-10-25, desktop, WSL2).** The
benchmark harness (`dev/bench/`) does not exist yet; these are single
`time` runs, not medians.
- *Build* (`harald-cli build --fetch`, downloads included): **7 m 14 s**
  wall. `lexicon.db` is **468.2 MB**, schema 7, 102,897 entries, 0 bad lines.
  Stages: `en.read+parse` 128 s, `de.read+parse` 40 s, `lexicon.merge` 17 s,
  `keys.merge` 19 s, `fuzzy` 21 s, `fuzzy.merge` 20 s, `finalize` 7 s.
  The English-translation load added by 008 is within the 468 MB.
- *Coverage*: verbs with complete Stammformen 96.8 % (10631/10981); nouns
  with a gender 98.9 % (58964/59610); senses with a translated example
  13.2 % (15461/117302).
- *Cold CLI*: `lookup Hund` took **5.4 s** (`verschlimbessern` 9.3 s) on the
  real lexicon, against 0.19 s for `--help`-class commands. Cause: the
  fuzzy candidate query joined `search_key` to `fuzzy_delete`, and with no
  `sqlite_stat1` SQLite chose the `(lang, key)` index, scanning all 1.19M
  German keys and probing `fuzzy_delete` (9.3M rows) for each. Fixed in
  `lookup._candidate_keys` by making the `lang` filter unusable as an index
  key (`lang || '' = ?`), so the five or so `fuzzy_delete` rows drive the
  join: the same 21 rows in under a millisecond, and a cold `lookup` of
  about 1.1 s. A component test asserts the plan starts with a
  `fuzzy_delete` search. The plan depends on the planner's statistics, so a
  future `ANALYZE` in the build would make the workaround unnecessary.
- *What remains of the 1.1 s* is process start: about 0.7 s of it is
  importing SQLAlchemy, the cost §4.4 accepted. The lookup itself takes
  0.13 s in-process.
- *Ranking*: `lookup schnel` shows *Schnee* first and *schnell* only under
  "Also". Both are one edit away, so the tie is decided by richness. Whether
  that is wanted is open.

### 14.10 `Option[T]`, and where `T | None` stays (confirmed by the user 2026-10-24)

The user added kohle's `Option` to the refactor slice (§11.3). The reasons:
- `T | None` is everywhere;
- an `Option` return states that absence is an expected outcome;
- it composes like `Result` (`map`, `and_then`, `or_else`);
- it converts into a `Result` with `ok_or`.

This reverses the earlier rejection (§14.7 item 5, §14.8).

**Shape** (`harald/core/option.py`, beside `core/result.py`):
- **kohle's API, with the same names and behaviour:** `some`, `none`,
  `is_some`, `is_none`, `unwrap`, `expect`, `unwrap_or`, `unwrap_or_else`,
  `map`, `map_or`, `map_or_else`, `and_then`, `or_else`, `filter`,
  `inspect`, `flatten`, `zip`, `ok_or`. It is kept identical for the same
  reason as `Result`: a later lift into the shared package (§7.7) stays a
  rename.
- **Representation: a frozen, slotted dataclass with `_value: T | None` and
  `_is_some: bool`**, not kohle's `object()` sentinel.
  - *Why:* measured (§0), the sentinel loses its identity when pickled, so
    an unpickled `none()` reads as Some. That breaks the moment an `Option`
    crosses the build's process boundary, where job results travel pickled
    (§3.7).
  - `Option.some(None)` stays representable, as in kohle.
- **`none()` returns one module-level instance.** Measured 0.07–0.3 µs,
  against 0.77 µs for a fresh allocation.
- **Typed throughout**, in `result.py`'s PEP 695 style.
  - `ok_or[E: Exception](self, err: E) -> Result[T, E]` replaces kohle's
    untyped `ok_or`.
  - It imports `Result` at module top. `result.py` imports nothing from
    `option.py`, so there is no cycle.
  - The internals carry the same `# type: ignore` on the storage field that
    `result.py` does. A prototype passes `mypy --strict` (§0).
- **One addition, because it has callers:** `Option.from_optional(value: T
  | None) -> Option[T]`. It is the conversion at the boundary (rule 3
  below), for an ORM `session.scalar(...)` or a `dict.get`.
- **Not added, for want of a caller:**
  - `Result.ok_option()` (Result → Option). It would drop the error, and
    the error model never drops one (§14.2);
  - `to_optional()`. It arrives with the first use case that has to put an
    `Option` into a record field.
- **No `__bool__`.** An `Option` is always truthy, like a `Result`, so an
  `if opt:` left over from `T | None` code is always true. mypy's optional
  `truthy-bool` error code catches that statically. It is enabled in the
  slice, and today's `src` and `tests` pass it unchanged (§0).

**The convention:**
1. **`Option` is required** for a value that may be absent in the return
   type of:
   - every use case's `execute` (§11.2);
   - any public function or method of `lexicon/`, `learning/`, `build/` or
     `editor.py` that code outside its own module calls.

   Where the call can also fail, the `Option` sits inside the `Result`:
   `Result[Option[T], E]`.
2. **Never `Option` for success-or-failure.** An operation that succeeds
   with no value, or fails, returns `Result[None, E]`. An `Option[E]` would
   put failure in the Some arm.
3. **Convert at the return.** A service that returns an `Option` builds it
   with `Option.from_optional(...)` from the `T | None` its query or lookup
   gave. A use case for which absence is an error turns it into one with
   `.ok_or(err)`.
4. **`T | None` stays in five places:**
   - **Data records:** dataclass fields (`lexicon/model.py`,
     `build/records.py`, `learning/content.py`) and SQLAlchemy
     `Mapped[T | None]` columns.
     - They mirror nullable columns and JSON `null`, so absence has one
       representation across `lexicon.db`, `learning.db`'s content JSON and
       the dataclasses.
     - SQLAlchemy derives nullability from the annotation, and an `Option`
       column would need a `TypeDecorator` for no gain.
   - **Parameters with a `None` default** (`load_config(path=None)`,
     `deck_id | None`). That is a calling convention, and an `Option`
     parameter would make every caller wrap.
   - **Private helpers** (a leading underscore, or nested). Their caller is
     in the same module, and it converts if it returns publicly.
   - **Hot paths:** functions called per line, per record, per form row,
     per token or per fuzzy candidate in the build or lookup loops, and the
     kernels the Rust rewrite will take over (`osa_within`, `lemma_of`).
     - Measured (§0): an `Option.some` costs about 0.5 µs more than
       returning the value.
     - The Rust FFI maps `Option<T>` to `T | None` anyway.
   - **A union where `None` is one arm of a dispatch**
     (`EntryRecord | FormOfRecord | None`).
     - The caller matches on all three arms (`case None:`), and
       `Option[A | B]` would make it unwrap and then dispatch.
     - If such a union ever leaves its module, `None` becomes a named
       outcome type, not an `Option`.

**Hot-path cost**, from §0's measurements:

| Site | Calls | Its own cost | `Option` would add |
|---|---|---|---|
| `parse_line` | once per kept line (459,333 English lines) | about 100 µs on the fixture, 280 µs on average on real lines | 0.2–0.5%: negligible, but kept under the dispatch and importer-internal rules |
| `_table_slot` | once per verb form row (millions) | 2.6 µs | about 20% of the function; 1–2% of the English parse's 128 s of CPU |
| `osa_within` | once per fuzzy candidate, up to 3,311 per query | 5–60 µs | 1–10% per call: about 2 ms on the worst desktop query, 6–10 ms on the phone (3–5×) |

**Audit of today's code and the designed signatures:**

| Site | Today | Decision | Reason |
|---|---|---|---|
| `lexicon/fuzzy.py` `osa_within` | `int \| None` | keep | hot kernel and a Rust candidate (rule 4) |
| `build/wiktextract_en.py` `parse_line` | `EntryRecord \| FormOfRecord \| None` | keep | `None` is one arm of a dispatch; per line; importer-internal (rule 4) |
| `_form_of`, `_separable_prefix`, `_plural` (same module) | `T \| None` | keep | private. The last two fill `EntryRecord` fields that mirror nullable columns |
| `build/forms.py` `_head_slot`, `_table_slot` | `str \| None` | keep | private, and called per form row (rule 4) |
| `build/graph.py` `Jobs._reap` | `BuildError \| None` | **convert to `Result[None, BuildError]` in the slice** | success or failure, not presence (rule 2). It is the per-function union style §14.2 replaced, and it runs once per finished job, so the cost is nil. Its caller becomes `if (r := self._reap(...)).is_err: return Result.err(r.unwrap_err())` |
| `lexicon/lookup.py` `first()`, nested in `_principal_parts` | `str \| None` | keep | nested helper that fills `PrincipalParts` fields |
| fields: `lexicon/model.py` (`PrincipalParts.*`, `Entry.plural`, `separable_prefix`, `principal_parts`, `Headword.via_form`), `build/records.py` (`plural`, `separable_prefix`), `build/run.py` `Timing.job_seconds` | `T \| None` | keep | data records (rule 4) |
| mapped columns: `lexicon/models.py` `Entry.plural`, `separable_prefix`, `BuildStat.denominator`; the `learning.db` models (§7.1) | `Mapped[T \| None]` | keep | data records (rule 4) |
| state: `graph._shard`, `Jobs._pool` | `T \| None` | keep | private mutable state set by an initializer, not a return |
| `core/result.py` `_ok`, `_err` | `T \| None` | keep | `Result`'s own storage |
| parameters: `load_config(path)`, `cli.main(argv)`, the click commands' `config_path` | `T \| None = None` | keep | parameters (rule 4) |
| planned: `NextCard.execute` (§7.4) | `Result[StudyCard \| None, …]` | **convert:** `Result[Option[StudyCard], LearningDbError]` | a use-case return. `none` means the session is over |
| planned: `edit_fields` (§9) | `Result[dict[str, str] \| None, EditorFailed]` | **convert:** `Result[Option[dict[str, str]], EditorFailed]` | a public return. `none` means the user cancelled |
| planned: the `lemma_of` callback (§4.3) | `str \| None` | keep | called per token over 585k sentences in the build, and a callback across the build/runtime seam (rule 4) |
| planned: `PlanWordCards`' `entry \| None`, `NextCard`'s `deck_id \| None` | parameters | keep | parameters (rule 4) |
| planned: `learning.db` lookups by card id (§7.5, and §8.4's per-card commands) | – | the service returns `Option[Card]`; the use case calls `.ok_or(...)` with a not-found error that issue 017 or 021 names | `ok_or`'s first caller |

So in today's code only `_reap` changes, and it becomes a `Result`.
**`Option` itself has no caller in today's code**, because every current
`T | None` falls under a keep rule. Its first callers are `NextCard` (issue
010), `edit_fields` (017 or 020) and the lookups by card id (017, 021). It
lands in the slice anyway, at the user's request, so those issues start
from it.

**Tests** (in the slice, §11.3):
- `tests/unit/test_option.py`:
  - every method on Some and on `none`: `map`, `and_then`, `filter` and the
    rest apply on Some and pass `none` through;
  - `unwrap` and `expect` raise `RuntimeError` on `none`;
  - `some(None)` is Some;
  - `from_optional` of a value and of `None`;
  - `ok_or` gives `Ok` and `Err`;
  - `none()` is a single instance;
  - a pickle round trip of `none()` and `some(0)`.
- `tests/unit/test_result.py`. Harald has no unit tests for `Result` yet,
  so there is nothing to mirror. They are added in the same shape (`ok` and
  `err`, misuse of `unwrap`/`unwrap_err` raising `RuntimeError`, `map`,
  `map_err`, `and_then`, `unwrap_or`), so the two core types are tested
  alike.
- **`_reap`:** the existing build tests already cover both arms
  (`test_failing_task_publishes_nothing_and_cleans_up` at 0 and 3 workers,
  and the worker-count invariance tests). No new test.
- **`truthy-bool`** runs in the normal mypy pass over `src` and `tests`.
- **Later issues:** 010 and 017/020 assert `Option.none()` for "no card
  left" and for "cancelled" in their own tests.

---

## 15. Issue order and where each one's decisions live

Dependencies follow the issue files. The user split issue 004 into 004a (the
single-process deterministic, atomic, versioned build; criteria unchanged)
and 004b (the parallel task graph, with the four criteria in its row).
- **004a and 004b come early,** because every later build slice must keep
  their guarantees.
- **004b lands right after 004a, before 002.** Every later build slice (002,
  003, 007, 008, 018) then adds its nodes to the parallel graph under the
  worker-count invariance tests from the start. Because 001's parse already
  runs as an inline job, 004b could also slip after 002 or 009 without
  rework, if the user prefers.
- **009 still comes before anything builds on the TUI** (010 onwards), since
  the spec's early risks must be retired first.
- **A refactor slice lands after 005 and before 006** (added 2026-10-20):
  click, the use-case layer (§11.1–§11.3) and `Option` (§14.10). 005 landed before 006,
  reversing the table's order. 006 comes next, and it extends lookup below
  the new use case.

| # | Issue | Design sections it implements | Notes |
|---|---|---|---|
| 1 | 001 noun lookup | §2 layout, §3.1 (headword/entry/sense), §3.3 entry rules, §3.5 open + version, §3.7 job shape, §4.1 exact, §4.4 `lexicon/models.py` + engine factory, §6 width-adaptive renderables + width-parametrised tests (40/60/80/100), §11 import-hygiene test, §13, §14.2 `Result`, §14.9 harness | **bench step: sets up `dev/bench/` and writes the first desktop baseline** (`cold.lookup`, `warm.headword_load`). source placed by hand; fixtures from §0 records. The English parse is written as a chunk job writing a shard, then merged, running inline (`build_workers = 0`), so issue 004b adds the pool without reshaping |
| 2 | 004a deterministic, atomic, versioned build (single process) | §3.5 steps 1–11: lock, fingerprint fast path, staging, byte compare, single-rename publish, version check; §3.7 jobs run inline (`build_workers = 0`) | criteria unchanged; the 004a tests in §3.5 (`--force` twice; Ctrl-C leaves the old file; schema mismatch refused) |
| 3 | 004b parallel task graph | §3.7 graph executor, process pool (forkserver), per-worker shards, offset ids, ATTACH merges, cancellation; §3.5 determinism rules | depends on 001 and 004a. Criteria: output byte-identical for any `build_workers`; a failing task cancels the rest and nothing is published; no shard or staging file survives a failure or Ctrl-C; the build prints per-node timings |
| 4 | 002 conjugation + inflected lookup | §3.2, §3.3 forms + unmapped + separable prefix, §3.7 `verb_form_stage`/`key_stage`, §4.1 kind 1, §6 conjugation (stacked tense blocks at 40 columns, TRENNBAR badge) | |
| 5 | 009 TUI + Termux risks | §12 skeleton, §12.8 portrait layout, §14.3 | **verify on the phone and record in the issue**: (a) suspend/resume with `$EDITOR`; (b) startup time; plus three this design adds: (c) `sqlite3` FTS5 available in Termux Python; (d) lookup time with `lexicon.db` where Syncthing delivers it (shared storage if using the Syncthing app), opened `immutable`; (e) installing Harald's pure-Python dependencies on Termux; (f) taps and swipes reach Textual as mouse clicks and scrolling (§12.5); (g) in **portrait**: rows available with the soft keyboard up (designed for 40×12, §12.8), and every screen rendering at the phone's real width; (h) installing the migration stack on Termux: alembic, SQLAlchemy ≥ 2.1 (pure wheel), Mako, and MarkupSafe (compiles its speedups if clang is present, else plain Python), plus one `alembic upgrade` of a scratch file; (i) run `dev/bench/bench.py --machine phone` and write `baseline-phone.json`. This records the phone baseline against the confirmed budgets and replaces the assumed 3–5× factor (§14.9) with measurements, including `cold.lookup` (ORM; no `textual`) and `cold.tui_start` (no `alembic`), checked with `python -X importtime` |
| 6 | 003 fuzzy lookup | §3.3 keys, §3.7 `fuzzy` jobs + `fuzzy.merge`, §4.1 fuzzy, §4.4 candidate query, `fuzzy.py` | bench step: `warm.fuzzy_candidates`, `warm.read_3000_columns`, `warm.lookup_e2e`. measured 3.47M rows, 60 MB for the English keys, so the size lever (drop adjective-declension forms from `fuzzy_delete`) is unlikely to be needed |
| 7 | 006 full English entry | §3.3 IPA, labels, examples; §4.1 display | bench step: re-run `warm.headword_load` (examples make the entity load heavier) |
| 8 | 005 fetch, dates, attribution, coverage | §3.4, §3.6, `harald info` | fetch runs before the graph (§3.5 step 4); coverage counters come back from the parse jobs |
| 8a | refactor: click CLI, use cases and `Option` | §11.1, §11.2, §11.3, §14.10 | through the `change` door, not a spec issue; lands before 006. Bench step: `cold.lookup`, once the harness exists (§16). Until then the hand measurement in §0 stands in |
| 9 | 007 German-edition block | §3.3 German edition, §3.7 `de.read`/`de.parse`, §4.1 blocks, §4.4 German block load | Band is the fixture. Bench step: re-run `warm.headword_load` |
| 10 | 008 English → German | §3.3 English → German, §3.7 `en_translation_stage`, §4.2, §4.4 | fuzzy for English confirmed (formerly open question 7). Bench step: `use` in `warm.lookup_e2e` |
| 11 | 010 add word + meaning cards + study | §7.1 whole schema as models, §7.2, §7.3, §7.4, §7.6 Alembic `0001` + `migrate.py`, §7.7 kohle's infrastructure (`harald/core`, `harald/db`, `harald/infrastructure`), §7.8 audit trail, §8.2 hint capture plus `link_state`/`check_ack` columns, §14.2 `Result` in the TUI | the first slice to touch `learning.db`. Bench step: `warm.grade`, `warm.read_3000_entities`, `cold.tui_start` with `learning.db` |
| 12 | 011 article cards | §7.2, §7.4 checked grading | |
| 13 | 012 Stammformen | §5 `answer_matches`, §7.2 (`separable_prefix`, TRENNBAR badge), §12.8 | separable verbs: split forms plus the highlight (open question 5 part 2, resolved) |
| 14 | 015 new cap + sibling burying | §7.4 | cap 20 confirmed |
| 15 | 014 German → German cards | §7.3 German picker | |
| 16 | 016 decks | §7.1, §7.5 | |
| 17 | 017 edit, suspend, delete | §7.5, §9 | creates `editor.py` if 020 hasn't |
| 18 | 018 Tatoeba search | §3.3 Tatoeba, §3.7 `tatoeba.parse` / `tatoeba.lemmas` / `tatoeba.merge`, §4.3, §4.4 FTS5 through `text()` | bench step: `warm.phrase_search` |
| 19 | 019 save phrase card | §7.2, §7.3 transaction | |
| 20 | 020 write phrase in `$EDITOR` | §9 | |
| 21 | 022 backup | §10 | trigger points and retention confirmed |
| 22 | 021 `harald check` | §8 entire, §7.8 audited repairs, §12.8 Check screen, §11 CLI | depends on 004a and 010. Acceptance-criteria changes are listed in §8.4 |
| – | 013 per-(tense, person) cards | §7.2 (`separable_prefix` carried) | **blocked on open question 5 part 1** (persons, Sie, imperative) |

---

## 16. Open items needing the user's decision

**Blocked (no answer invented):**
- **Open question 5, part 1, blocks issue 013**: which persons count (is
  the formal Sie separate from 3rd person plural?) and which persons the
  imperative has. Facts for the decision:
  - the data has **no Sie rows** (Sie forms would be the 3pl form plus
    "Sie", constructed by rule);
  - the imperative has **only du and ihr** in the data (a Sie imperative
    would also be constructed);
  - `formal` in the data is a register marker, not a person.

  Part 2 is resolved: separable verbs use the split forms plus the TRENNBAR
  highlight (§7.2).

**Still open:**
- **The Core fallback's limit**, a consequence of your ORM decisions. Moving
  lookup paths to Core still imports the ORM through the declarative models,
  so it recovers only about 10% of the extra cold-start cost. If
  `cold.lookup` ever breaches its budget, the options are a Core-only table
  module for that path, or stdlib `sqlite3` for it. Each undoes one of your
  decisions, so that call stays yours.

**Spec and doc wording that must change** (user-owned):
- **80 columns → portrait 40:** spec lines 36, 137 and 257; AGENTS.md line
  8; issue 001 line 11, issue 002 line 10, issue 009 line 9. Exact
  replacements are in §12.8.
- **Old database names still in the spec:** lines 121 and 139
  (`dictionary.db`), 190–197 (the "Two databases" block: `dictionary.db`,
  `user.db`), 229–230 and 241. Generic "the dictionary" wording: lines 9, 16
  and 30. "Dictionary mode" (line 39) names a mode and can stay. The issues
  and AGENTS.md are already renamed.
- **Proper nouns:** the spec is silent on them, so nothing needs to change.
- **Issue 021's acceptance criteria** need the six changes listed in §8.4.

**Notes, informational:**
- **`Option` has no caller in today's code** (§14.10). Every current
  `T | None` is a data-record field, a parameter, a private helper or a hot
  kernel. Its first callers are `NextCard` (010), `edit_fields` (017/020)
  and the lookups by card id. In the slice, the one conversion is
  `Jobs._reap`, and it becomes a `Result`.
- **The bench harness isn't in the repository.** §15 gives issue 001 the
  job of creating `dev/bench/` and the first desktop baseline, and gives
  later slices bench steps. But `dev/bench/` does not exist, so none of
  those steps has run. The click cost in §0 was measured by hand instead.
- **The first build after the refactor slice reruns the graph** and
  publishes nothing (§11.3), because the fingerprint covers every `.py`
  file.
- **The bench steps change issue scope** (§15). Issue 001 gains the harness
  and the first baseline. Issue 009's checklist item (i) becomes "write
  `baseline-phone.json`". Issues 003, 006, 007, 008, 010 and 018 re-run
  their metrics.
- **Issue 001's shape.** The English parse is a chunk job writing a shard
  from day one, run inline, so issue 004b only adds the pool.
- **The SQLAlchemy pin** is `>=2.1`, newer than kohle's 2.0.46, because 2.0
  pulls greenlet (compiled) on the phone's aarch64.
- **The build speedup is an estimate.** About 2.5× end to end, from
  measured components (§3.7); issue 004b measures the real figure.
- **One behaviour change.** A failing `learning.db` write shows an error and
  keeps the session going, instead of crashing the TUI.

**Gaps found while designing, decided here but worth a veto:**
- **Where `T | None` stays** (§14.10, rule 4). Data-record fields, mapped
  columns, parameters with a `None` default, private helpers and hot paths
  keep `T | None`, and `Option` is required only at public and use-case
  returns. Making fields `Option` as well would mean converting at every
  SQLAlchemy, JSON and rendering boundary.
- **"Answered correctly"** in the summary means a card whose first grade in
  the session was not Again. "Reviewed" counts distinct cards.
- **Context on German → English cards.** Each meaning card copies the
  sense's first translated example as context, so several cards of one word
  don't show identical fronts.
- **Homograph hints.** Article and Stammformen cards copy a hint gloss (and
  the plural, for article cards), so Band n/m/f or the two umfahren verbs
  don't share identical fronts (§7.2, §12.6).
- **Touch buttons in Study**, with a 300 ms guard against double taps (§12.5,
  §12.8).
- **Extra CLI commands.** The design adds `phrase`, `info` and `backup`, and
  the `check` subcommands of §8.4.
- **The Tatoeba licence** is displayed as CC BY 2.0 FR, the precise form of
  the spec's "CC-BY".
- **Where files live on the phone** (§13). If the Syncthing Android app is
  used, `lexicon.db` and the backup folder must sit in shared storage.
- **Check scheduling defaults** (§8.3). Accepting upstream changes resets
  the schedule of checked cards whose answer changed and keeps it for
  self-graded cards, overridable per repair.
- **Grades are audited** (§7.8), measured at +0.2–0.9 ms per grade, so that
  a future undo walks one log.

**Confirmed by the user** (no longer open):
- kohle's `Option`, ported to `harald/core/option.py` with the convention
  of §14.10, in the refactor slice (2026-10-24). This reverses its earlier
  rejection in §14.7 item 5 and §14.8;
- click for the CLI and the `use_cases/` package (§11.1–§11.3), confirmed
  2026-10-24. They reverse §14.6's argparse decision and §7.7's
  domain-module layout for use cases;
- every use case is a class with `execute()`, in kohle's `UnitOfWork` call
  shape (§11.2), 2026-10-24;
- one date per source in `harald info` is the newest trusted date among
  its files (§3.6), 2026-10-24;
- **AGENTS.md states the layering: resolved 2026-10-24.** The main session
  makes the edit at the user's request. Suggested sentence for its Context
  section: "Code is layered front-ends (`cli.py`, `tui/`) → `use_cases/` →
  `lexicon/`, `learning/`, `build/` → `infrastructure/`, `db/`, `core/`.
  Front-ends call only use cases; only the per-database packages touch a
  session, a connection or a file." The Overrides entry for the six
  broad-catch seams (§14.2) is already in AGENTS.md and needs no change,
  because no seam moved;
- portrait TUI at 40 columns (§12.8);
- two-step Lookup; no interval previews;
- the 12-row floor, to be measured in issue 009 in portrait with the
  keyboard up;
- the audit trail retained (§7.8);
- proper nouns imported (§3.3);
- `check` in CLI and TUI with three repair actions (§8);
- separable verbs split and highlighted;
- backups after each session and on exit, plus `harald backup`, keeping 10;
- a daily cap of 20; fuzzy matching for German and English → German but
  not phrases;
- correct → Good, wrong → Again;
- the 04:00 day boundary;
- a missing `lexicon.db` refused at startup;
- the budgets; the `Result` path; the shared package as user-owned and
  informational; the 004a/004b split;
- issue 010's Alembic criterion.

## Issue 007 notes (2026-10-25)

As implemented in af41b34; the open items need a decision before they stop being open.

- **Schema version 6.** 007 added the German-edition tables (`de_*`), so an existing `lexicon.db` is rebuilt.
- **`de_example` ids use an offset rule:** each chunk's example count gives `example_off`, ids are `example_off + local_id`, independent of shard order (tested with 1-byte chunks and 2 workers).
- **German edition is optional:** a build without `de-extract.jsonl.gz` succeeds with no German blocks and no `de.read+parse` timing. Open: should a missing file be an error instead?
- **Editions parse serially.** Phase 1 says English and German parse at once, but `Jobs.run` drives one stream at a time. Output is identical; only the build is slower. Open: add an interleaving mechanism or amend phase 1.
- **German-only words** are searchable and render a bare title line (lemma, pos) above the German blocks.
- **Richness** counts English senses plus German senses that have an index; heading senses do not count.
- **Label rule assumes English-vocabulary gender tags** (`masculine`, `feminine`, `neuter`) and reuses the English `LABELS` for sense labels. Unverified against a real `de-extract` dump; check on the first full build. Only `pos == "noun"` gets an article.
- **German-edition form-of entries are skipped** and add no index forms. Open: should they?
- **Open from issue 006:** English `example` ids still come from shard attach order, which follows worker pids, so output may not be byte-identical across worker counts on real data. The fix mirrors `de_example`: an `example_off`.
- **`dev/bench/` does not exist**, so the `warm.headword_load` re-run was not done.
- **Convention (AGENTS.md):** absent values return `core.option.Option`; use cases open the lexicon themselves and return `Result`.
