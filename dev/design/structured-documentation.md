# Design: Structured documentation

Spec: `dev/specs/structured-documentation.md` (frozen). Issues:
`dev/issues/028`–`036`. Precedent: kohle's sweep (`~/code/kohle`,
`dev/design/cli-documentation.md`, `tests/docs_examples.py`,
`docs/mkdocs.yml`, `.github/workflows/docs.yml`). Where the spec and the
precedent differ, the spec wins; §15.9 lists every place this design departs
from kohle and why.

**Upstream state this design assumes.**

- The spec and issues 028–036 are committed on `change/docs-sweep-brief`
  (7eee571), not yet on `main`. The spec is in `dev/specs/`, so it is treated
  as frozen.
- Implementation is paused for about a week (spec, Timing). Nothing here
  depends on the review points from that week, except the content pass, which
  is out of scope.
- §16 lists the gaps, conflicts and readings. Each one names the decision taken
  so that no slice is blocked. **[confirm]** marks the ones still open for the
  user.
- **User decisions, 2026-11-08.** G3, G4, G7 and G14 are confirmed as
  recommended. G9 is decided as out of scope and recorded as a follow-up. G7
  goes beyond the spec's wording (§13). The issue files are being updated
  separately with the work order (§3) and with G1, G2, G5 and G6. G8 stays a
  manual step, noted in 035. G12 is still open.

**Verified, not assumed** (2026-11-08, against the installed textual 8.2.8,
rich 15.0.0, click 8.5.0, markdown-it-py 4.2.0, Python-Markdown 3.10/3.11 and
mkdocs-click 0.9.0 sources):

- `CliRunner.isolation()` sets Click's `formatting.FORCED_WIDTH = 80`, swaps
  `sys.stdout`/`sys.stderr` for captured streams, and applies an `env=`
  mapping in which `None` deletes a variable. Rich's `Console()`, which
  `harald.cli._print` constructs per call, reads `COLUMNS` when it is
  constructed. With `COLUMNS=80`, `lookup --en use` pads its lines to exactly
  80 columns and emits no ANSI codes.
- Built in-process with `build_workers = 0`, the current fixture builds in
  0.29 s. In process, `lookup` takes 13–40 ms and `info` about 100 ms.
- With `harald.build.run.time` and `harald.build.graph.time` replaced by a
  frozen clock, `build --force` prints every stage, and the total, as
  `0.0 s`.
- markdown-it-py (`MarkdownIt("commonmark").enable("table")`) parses
  `<!-- docs: keys home -->` on the line directly above a table as a separate
  `html_block`, followed by a `table_open` whose `map[0]` is the next line.
  Python-Markdown renders the same source as a table, with the comment passed
  through.
- `textual.keys.format_key` maps `esc` and `escape` to `esc`, and `/` and
  `slash` to `/`. `Binding.make_bindings` expands `"home,ctrl+a"` into one
  binding per key. Both names are public.
- mkdocs-click's `:style: table` prints only `option.help`. `:style: plain`
  prints Click's own help formatter, so `show_envvar=True` shows
  `[env var: HARALD_CONFIG]`.

---

## 1. Decisions at a glance

| Question | Decision | § |
|---|---|---|
| What a checked example is | Every ` ```console ` fence in `docs/**/*.md` and `README.md`. `$ ` lines are commands; the lines under each are its expected output. | 5.1 |
| Option vocabulary | `<!-- docs: illustration -->` above a non-console fence; `<!-- docs: keys SCREEN -->` above a key table. Nothing else. | 5.2 |
| Problem classes | Eleven, listed with their messages in §5.4. They are returned as `page:line: message` strings and reported together by one test. | 5.4 |
| Where the sample sources live | `docs/examples/en-edition.jsonl` and `de-edition.jsonl`: new, hand-cut, separate from `tests/fixtures/`, and excluded from the published site. | 7 |
| Building the sample once per session | A session fixture runs the real `harald-cli build` once into a template home (`tests/docs/sample.py`). Each example gets a `copytree` of it. The VHS tape calls the same builder with `python -m tests.docs.sample`. | 7.3 |
| Runner | `harald.cli.main(args)` in process, inside `CliRunner().isolation(env=docs_env(home))`. It is the function the `harald-cli` script runs; `CliRunner.invoke(cli)` is not used. | 5.6 |
| Width seam | `COLUMNS=80` in `docs_env`, with `FORCE_COLOR` and `TTY_COMPATIBLE` deleted. Click is already forced to 80 by the isolation. | 6.1 |
| Clock seam | Source dates come from a `.meta.json` sidecar written by the sample builder with `DOCS_SOURCE_DATE`. Build timings come from replacing the `time` attribute of `harald.build.run` and `harald.build.graph` with a frozen clock, for every example. These are the only clock reads a CLI command can reach. | 6.2 |
| Key tables | A table with the header `Key \| Does` must carry `<!-- docs: keys SCREEN -->` on the line above it. SCREEN is one of `home`, `lookup`, `entry`, `add-word`, `study`. 031 adds the lookup, entry and study tables, which do not exist yet, and changes no existing prose (G3, decided). | 9.1, 9.4 |
| Widget keys | `KEY_SCREENS` in the checker maps each screen name to its `Screen` class and to the widget classes whose bindings it relies on. A row passes if its key is bound on the screen, the app or a declared widget. A declared widget must be constructed in the screen's `compose()`. | 9.2 |
| Reference | `::: mkdocs-click` with `:style: plain` on `docs/reference.md`. `--config` gains `show_envvar=True`. | 8 |
| Developer site | `dev/docs/`, with its own strict `mkdocs.yml`, served and built locally only. | 4.3 |
| Pages and CI | The existing workflow gains a `uv run --frozen pytest tests/docs` step and a deploy job (`upload-pages-artifact`, then `deploy-pages`). Deploy is gated on a push to `main`, the docs tests and the strict build. The test gate goes beyond the spec's wording (user decision, G7). | 13 |
| Tape test | It reads the `Type` lines that are shown (outside `Hide`/`Show`) from `docs/demo/taste.tape` and compares them, in order, with the README's only console block. | 12 |
| Order | 028 → 029 → 030 → 035 → 031 → 032 → 033 → 034 → 036. 031 needs 029, 033 needs 035, and 036 needs everything. | 3 |

---

## 2. Files

```
.gitignore                         + /site-dev/                                   028
.github/workflows/docs.yml         uv build command (030); docs tests and Pages deploy (035)
AGENTS.md                          ## Documentation                               036
README.md                          dev-guide link (028); temporary marker (029);
                                   docs command (030); cut (033); GIF (034)
pyproject.toml                     dev group + markdown-it-py                     029
docs/
  mkdocs.yml                       nav, validation (028); exclude examples/ (029);
                                   mkdocs-click + reference nav (030);
                                   site_url, repo_url (035); admonition removed (032)
  requirements.txt                 + mkdocs==1.6.1 (028); + mkdocs-click==0.9.0 (030)
  index.md                         no dev/roadmap links (028); "About the examples" (029);
                                   any feature statement no page holds (033)
  roadmap.md                       deleted                                        028
  reference.md                     generated                                      030
  user/lookup.md                   first checked page                             029
  user/*.md                        temporary markers (029); options out (030);
                                   key tables (031); conversions (032)
  examples/en-edition.jsonl,
  examples/de-edition.jsonl        sample sources (029; extended by 032)
  demo/taste.tape, demo/taste.gif  034
dev/docs/
  mkdocs.yml, index.md             028
  architecture.md, testing.md,
  build-internals.md, workflow.md  git mv from docs/developer/ (028); testing.md
                                   gains the tests/docs/ layer (029)
  guide.md                         how the guide is checked (029); key tables (031);
                                   publishing and the Pages setting (035)
  demo-gif.md                      034
tests/docs/
  checker.py                       parser, lint, runner, KEY_SCREENS; its module
                                   docstring is the syntax reference              029, 031
  sample.py                        sample home builder; `python -m` entry          029
  test_docs_examples.py            examples, well-formedness, meta-tests          029
  test_key_tables.py               031
  test_demo_tape.py                034
src/harald/cli.py                  help text; show_envvar on --config             030
```

`tests/docs/` is a new test layer, next to `unit/`, `component/`, `smoke/` and
`tui/`. Like `tests/tui/`, it has no `__init__.py`. `tests/__init__.py` makes
`tests.docs.checker` and `tests.docs.sample` importable, which is how
`tests.tui.helpers` is reached today. Test file basenames stay unique across
the suite, as pytest's default import mode requires.

---

## 3. Order of work and dependencies

The spec's order is skeleton, checker, reference, key tables, remaining fences,
README and GIF, then AGENTS.md. It does not place the Pages deploy (035). Four
dependencies were missing from the issues as first written. The issue files are
being updated with them and with the sequence below (2026-11-08):

| Issue | Says it depends on | Also depends on | Why |
|---|---|---|---|
| 029 | 028 | — | The checker scans every page from the start (spec: "No page is exempt"), so 029 leaves the suite green by marking every unconverted `harald-cli` fence `illustration`, on all pages and in the README (§5.9, G1). |
| 031 | 028 | **029** | `keys` is a word in the checker's closed vocabulary. Without 029's checker there is nothing to parse the comment, and the checker would report `keys` as unknown (G2). |
| 033 | 029, 030 | **035** | 033's README links to the published guide. That URL serves nothing until 035 has deployed from `main` (G5). |
| 036 | 029, 030 | **031–035** | Its AC says the section "matches what issues 028–035 built" (G6). |

Recommended sequence:

1. **028** Skeleton: both site configs, the developer pages moved, the roadmap
   page removed.
2. **029** The checker, the sample, `lookup.md` converted, and temporary
   markers everywhere else.
3. **030** The reference, help text, and CI moved to the uv command.
4. **035** Pages deploy, gated on the docs tests and the strict build. This is
   the earliest slot after 030: from 030 on, the build needs harald
   importable, and 035's AC names the uv command. Landing it here also gives
   every later slice a live site, and runs every later slice's examples in CI.
5. **031** Key tables. It is independent of 030 and 035, and could go in
   parallel with them after 029.
6. **032** The remaining fences, with the temporary markers removed.
7. **033** README cut.
8. **034** GIF and tape test.
9. **036** AGENTS.md.
10. The content pass: later, gated on the review points, and not an issue.

---

## 4. The two sites (028)

### 4.1 `docs/mkdocs.yml`

These are changes to the existing file. `docs_dir: .`, `site_dir: ../site`,
the theme and `strict: true` stay.

```yaml
validation:
  nav:
    omitted_files: warn      # a page on disk but in no nav entry fails strict
  links:
    anchors: warn            # a broken #anchor fails strict
nav:
  - Overview: index.md
  - Getting started: user/getting-started.md
  - Cards and study: user/study.md
  - Lookup: user/lookup.md
  - Building the lexicon: user/build.md
  - Configuration: user/configuration.md
  - Data and licences: user/data.md
  # 030 adds:  - Command reference: reference.md
```

- `nav.not_found` and `links.not_found` already warn by default, so a broken
  link or a nav entry for a missing page fails strict without config. The two
  added keys cover the omitted page and the broken anchor. MkDocs 1.6 has both
  checks built in and logs them at `info` unless they are raised to `warn`
  (kohle §3.1).
- The nav loses its "User guide" and "Developer guide" groups. With one
  audience left, the extra level is noise. Page files keep their `user/`
  paths, so no link changes.
- `exclude_docs` gains `examples/` in 029 and `demo/*.tape` in 034. The GIF
  stays in the site, so `index.md` may embed it.
- `admonition` is removed in 032, per that issue. Until then nothing uses it,
  and the checker's raw-line rule (§5.3) covers the one way it could hide a
  fence.

### 4.2 `docs/requirements.txt`

`mkdocs==1.6.1` is pinned explicitly next to `mkdocs-material==9.5.39`. The
`validation` keys need MkDocs 1.6, and material only pins a range. 030 adds
`mkdocs-click==0.9.0`. These are the versions kohle uses, so there is one docs
toolchain across projects. Only top-level packages are pinned. The toolchain
never enters `pyproject.toml`.

### 4.3 Developer site `dev/docs/`

- `git mv docs/developer/*.md dev/docs/`, plus a new `dev/docs/index.md` that
  says what is there and how to serve it.
- `dev/docs/mkdocs.yml` has the same shape as §4.1: `site_name: Harald
  developer notes`, `docs_dir: .`, `site_dir: ../../site-dev` (an output
  inside `docs_dir` is an error), `exclude_docs: mkdocs.yml`, the same theme
  and `validation` block, the extensions `toc` / `pymdownx.highlight` /
  `pymdownx.superfences` / `tables`, and `strict: true`. Nav: Overview,
  Architecture, Testing, Build internals, Workflow. 029 adds "Checked guide",
  and 034 adds "Demo GIF".
- It reuses `docs/requirements.txt` (one pinned toolchain):
  `uv run --with-requirements docs/requirements.txt mkdocs serve -f dev/docs/mkdocs.yml`.
- `/site-dev/` goes into `.gitignore`.
- **Links across the split.** `workflow.md` links `../user/getting-started.md`
  and `../roadmap.md`, and `build-internals.md` links `../user/build.md`. A
  relative link out of `docs_dir` fails strict. They become repo paths in code
  spans (`docs/user/build.md`), as `architecture.md` already cites
  `dev/specs/harald-v1.md`. Repo paths read offline and survive a Pages move.
  The roadmap reference becomes "the README roadmap".
- Never built in CI, never published (spec). Its readers have the repository.
  The trade-off: a broken link there is caught only by a local build.

### 4.4 Index and README links

- `docs/index.md` drops the Roadmap bullet and the whole "Developer guide"
  list. Nothing else in it changes in 028.
- `README.md` links `docs/developer/workflow.md` ("developer guide"). 028
  points that link at `dev/docs/workflow.md`, so the README has no dead link
  between 028 and 033. The README roadmap stays as it is (AC 028).

---

## 5. The checker (029)

### 5.1 Syntax

````markdown
```console
$ harald-cli lookup --en use
use (verb)
  employ, apply
    benutzen
```
````

- A checked example is any fence whose info string's first word is `console`.
  The tag is the marker, so a session shown with output cannot be left
  unchecked by forgetting a marker.
- A line beginning with `$ ` is a command. The lines after it, up to the next
  `$ ` line or the end of the block, are its expected output.
- A command is split with POSIX `shlex` rules: quotes work, and a `#` comment
  is dropped. There are no continuation lines and no `NAME=value` prefixes. No
  page needs either, and each would be a small addition later (§15.8).
- Commands are written bare: `$ harald-cli lookup lief`.
  `getting-started.md` says once that the desktop runs them through `uv run`.
- Output is shown only in console blocks. A `text` fence of command output
  without its `$ ` line is not detectable, so this is a page rule, stated in
  the docstring and in AGENTS.md (§14).

### 5.2 Option vocabulary

An HTML comment on the line directly above a block carries options. It is
invisible on GitHub and in the site (verified for tables; kohle and s2s for
fences). Its regex is `^\s*<!--\s*docs:\s*(.*?)\s*-->\s*$`. An HTML comment
that does not start with `docs:` is an ordinary comment and is ignored.

| Comment | Above | Meaning | Forcing page |
|---|---|---|---|
| `<!-- docs: illustration -->` | a non-console fence | It shows `harald-cli` lines on purpose and is not run. | `build --fetch` and `prune` (getting-started, build), the Termux install |
| `<!-- docs: keys SCREEN -->` | a `Key \| Does` table | The table describes SCREEN's keys and is verified against its bindings (§9). SCREEN ∈ `home`, `lookup`, `entry`, `add-word`, `study`. | the five TUI screens the spec names |

The vocabulary is closed. A new word is an edit to `tests/docs/checker.py`
and its docstring, not a plugin seam. Words considered and left out are in
§15.8: `width`, `first-run`, `file`/`uses`, `exit`.

### 5.3 Discovery and the invocation lint

- Pages are `docs/**/*.md` and `README.md`, both from 029 on (spec: "covers
  every page from the start"). `dev/` is never scanned.
- `MarkdownIt("commonmark").enable("table").parse(text)` gives `fence`,
  `code_block`, `html_block` and `table_open` tokens with `map` (0-based start
  line, exclusive end). Fences inside list items and blockquotes are found,
  with their content dedented. The options comment is the raw line
  `map[0] - 1`, after stripping its indentation.
- markdown-it-py is already locked (4.2.0), as a dependency of rich and of
  textual. The checker imports it directly, so 029 declares it in the `dev`
  dependency group in `pyproject.toml`. That adds no package to `uv.lock`.
  MkDocs and its plugins stay out of `pyproject.toml` (G14, decided).
- **Invocation lint.** Each of these is a problem:
  1. a line in a non-console fence, or in an indented `code_block`, that holds
     `harald-cli` as a whitespace-separated token, unless the fence is marked
     `illustration`. That catches `harald-cli …`, `$ harald-cli …` and
     `uv run harald-cli …` alike;
  2. a raw line outside every block that starts, after indentation, with `$ `
     and holds the `harald-cli` token. This catches a fence that markdown-it
     cannot see, such as one indented under an admonition or inside an HTML
     block.
- **Inline code is not an invocation.** Prose like "`harald-cli lookup --en
  use` lists German words" names a command and is never flagged. The pages
  carry dozens of these (G10).

### 5.4 Problem classes

Each problem is a string `page:line: message`, and the message says what to do
instead. `collect` returns them all, and `test_docs_pages_are_well_formed`
lists every one at once.

| # | Problem | Message gist |
|---|---|---|
| 1 | An unknown option word, or a known word with the wrong arguments (`illustration x`, `keys` with no screen, `keys` with an unknown screen) | the vocabulary, quoted |
| 2 | An option above the wrong kind of block: `illustration` above a console fence or a table, or `keys` above anything but a `Key \| Does` table | "a console block is always run; use an `sh` fence"; "`keys` goes above a `Key \| Does` table" |
| 3 | Output before the first `$ ` line in a console block, or a console block with no command | "start the block with `$ harald-cli …`" |
| 4 | A command whose first word is not `harald-cli` (`ls`, `harald`, `uv run harald-cli`, `HARALD_CONFIG=x harald-cli`) | "only harald-cli runs here; use an `sh` fence, and write it bare" |
| 5 | A shell operator token (`\|`, `&&`, `;`, `>`, `<`, `&`, `(`, `)`) | "show the effect in prose" |
| 6 | A command that cannot be split (an unbalanced quote) | the `shlex` error |
| 7 | A command that would prompt: its Click subcommand has a `yes` parameter and `--yes` is not passed | "pass `--yes` and describe the question in prose" |
| 8 | A `harald-cli` invocation outside a console fence that is not marked `illustration` (§5.3, both forms) | "make it a console example or mark the fence `<!-- docs: illustration -->`" |
| 9 | A `Key \| Does` table without a `keys` comment | "name its screen with `<!-- docs: keys SCREEN -->`" |
| 10 | A key-table row whose first cell holds no backticked key | "write each key in backticks" |
| 11 | The same screen named by two tables, or one of the five screens named by none (reported by the key-table test, §9.3, since it needs every page) | the pages involved |

Class 7 is decided statically from the Click group (`harald.cli.cli`), not by
running the command. The `--yes` flag is the project's only prompt mechanism
today (`prune`), and a second confirming command would follow it. A prompt
that slips past (a future `click.prompt` with no `--yes`) still fails, because
the isolated stdin is empty and the output shows `Aborted!`. Unknown
subcommands are not checked statically either: they fail the match with
Click's usage error.

### 5.5 Starting state of an example

Each example runs in `tmp_path / "home"`, a `copytree` of the session's
template home (§7.3). It is laid out as a first-time user's machine with
default paths:

```
~/.config/harald/config.toml       build_min_entries = 0, build_workers = 0
~/.local/share/harald/lexicon.db   the sample lexicon
~/.local/share/harald/sources/     raw-wiktextract-data.jsonl.gz, de-extract.jsonl.gz,
                                   and a .meta.json sidecar for each
~/.cache/harald/staging/           the last-build record, so `harald-cli build`
                                   reports "unchanged"
```

- **Scratch config.** Only the two build keys are set. Every path resolves
  through the XDG defaults into the scratch home, so printed paths read like a
  real machine (`~/.local/share/harald/lexicon.db`). `build_min_entries = 0`
  lets a build of a dozen entries publish. `build_workers = 0` runs jobs
  inline: there is no forkserver pool inside pytest, it is faster, and the
  frozen clock reaches the job timings (§6.2).
- **Scratch `learning.db`.** It is the default path inside the scratch home.
  No CLI command opens `learning.db` today, so none is created. When `check`
  (021) or `backup` (022) reach the CLI, their first use lands there and never
  at the real path (G11).
- **Isolation.** `docs_env(home)` (§6) sets `HOME`, `XDG_CONFIG_HOME`,
  `XDG_DATA_HOME` and `XDG_CACHE_HOME` into the scratch home, and deletes
  `HARALD_CONFIG`. A developer's own `XDG_DATA_HOME` or `HARALD_CONFIG` can
  therefore never point an example at real files.
- `monkeypatch.chdir(home)`. `uv run pytest` runs from the repository, and
  `Config.learning_db`'s dataclass default is the relative `learning.db`. The
  chdir keeps any relative write out of the user's checkout.
- `socket.socket.connect` raises `RuntimeError("network access in a docs
  example")`. That turns "offline" into a check (kohle §4.3).
- The clock is frozen (§6.2).

Nothing crosses examples. Commands within one example share its home, in
order. The first mismatch ends the example, because the state after it is
undefined.

### 5.6 Running a command

```python
with CliRunner().isolation(env=docs_env(home)) as (_, _, output):
    main(args)        # harald.cli.main: prog_name, standalone_mode=False, exit codes
actual = output.getvalue().decode()
```

- `harald.cli.main` is what the `harald-cli` script runs (`[project.scripts]`).
  Calling it, rather than `CliRunner.invoke(cli, …)`, keeps its error mapping
  exactly as a user meets it. A `ClickException` is shown through `e.show()`,
  an `Abort` returns 130, and the program name is `harald-cli`.
  `CliRunner.invoke` runs the group in standalone mode, which prints
  `Aborted!` and maps codes differently.
- The `output` stream is stdout and stderr interleaved as a terminal shows
  them (Click ≥ 8.2), so `No match for 'x'` on stderr is compared like any
  other line.
- The exit code is not compared. A page shows output, and the text already
  tells a refusal from success (kohle §4.4).
- An exception that escapes `main` (a bug in harald) is not caught. pytest
  reports it with its traceback, and the test id names the page and the line.
  Catching it would only reformat what pytest already shows.

### 5.7 Comparing

- Both sides are split into lines, each line is right-stripped, and trailing
  blank lines are dropped. On the actual side, every occurrence of
  `str(home)` becomes `~` first. Nothing else is normalised: no wildcards, no
  placeholders.
- Trailing blank lines count as trailing whitespace. `RenderHeadword` ends
  every entry with blank lines, and a page cannot show them visibly before a
  closing fence (G10).
- Failure text, through `pytest.fail(msg, pytrace=False)`:

```
docs/user/lookup.md:57: `harald-cli lookup lief` printed something else (example at line 55)
--- expected (page)
+++ actual
@@ ... unified diff ...
```

### 5.8 Module and tests

`tests/docs/checker.py`. Its module docstring is the authoritative description
of §5.1–5.7, §6 and §9.1 for page authors. AGENTS.md points to it (§14).

```python
@dataclass(frozen=True, slots=True)
class Command:
    line: int            # 1-based page line of the `$ ` line
    text: str            # as written after `$ `
    expected: list[str]

@dataclass(frozen=True, slots=True)
class Example:
    page: str            # repo-relative, e.g. "docs/user/lookup.md"
    line: int            # 1-based line of the opening fence
    commands: list[Command]

@dataclass(frozen=True, slots=True)
class KeyRow:
    line: int
    keys: tuple[str, ...]      # the backticked spans of the first cell

@dataclass(frozen=True, slots=True)
class KeyTable:
    page: str
    line: int
    screen: str                # a KEY_SCREENS name
    rows: list[KeyRow]

@dataclass(frozen=True, slots=True)
class Parsed:
    examples: list[Example]
    tables: list[KeyTable]
    problems: list[str]

KEY_SCREENS: dict[str, tuple[type[Screen[Any]], tuple[type[Widget], ...]]]   # §9.2

def parse_page(page: str, text: str) -> Parsed
def collect(root: Path) -> Parsed
def run_example(example: Example, home: Path) -> Option[str]   # failure text, or none
```

- Problems are returned, not raised. One malformed page must not stop every
  other page's examples from being collected, and the project prefers
  Result-like values to exceptions.
- `run_example` returns `harald.core.option.Option`, because "no failure" is
  the expected outcome (the AGENTS.md convention). Kohle returned
  `str | None`.

`tests/docs/test_docs_examples.py`. The examples are collected at import, as
kohle does, so they can be parametrised:

- `test_docs_example[docs/user/lookup.md:55]`: one case per example. The id
  names the page and block, so `pytest -k lookup` runs one page.
- `test_docs_pages_are_well_formed`: `collect(ROOT).problems == []`.
- Meta-tests on synthetic pages, through the real setup:
  - a wrong block fails, and its text names `page:line` and the diff;
  - a right block passes;
  - `sh` and `toml` fences without `harald-cli` yield nothing;
  - `harald-cli` in an `sh` fence, `uv run harald-cli` and a prose `$ harald-cli`
    line are each a problem, and an `illustration` fence is not;
  - an unknown option, `illustration` above a console fence, `ls`, a pipe, a
    redirect, `harald`, and `prune` without `--yes` are each a problem;
  - `README.md` is scanned alongside `docs/`;
  - a `Key | Does` table without `keys` is a problem, and `keys home` parses
    into a `KeyTable` with its rows.

### 5.9 The first page, and temporary markers (029)

- **`docs/user/lookup.md`.** The `--en use` `text` fence becomes a console
  example with its real output against the sample. Its prose claims "lief"
  finds *laufen*, so a `$ harald-cli lookup lief` example goes under "Exact
  and inflected forms". The synopsis fence (`harald-cli lookup [--conj]
  WORD...`) is not runnable. It is marked `illustration` in 029, and 030
  removes it as an option list.
- **Every other page and the README.** Each fence that holds `harald-cli` is
  marked `<!-- docs: illustration -->`. Its contents are unchanged. This
  touches getting-started.md (Termux, Build the lexicon, prune, Look something
  up, See what you built from), build.md (synopsis, prune) and the README's
  Quick start. The checker has no exemption list. The temporary markers are
  visible in source, 032 converts what can run and keeps the marker only on
  what cannot, and 033 deletes the README's Quick start (G1).
- `docs/index.md` gains "About the examples". Every console session in this
  guide is run by the test suite against a small sample lexicon built from a
  few hand-cut Wiktionary entries, at 80 columns, so the output shows that
  lexicon's words, counts and coverage. Source dates read 2026-11-01 and build
  timings 0.0 s. A real lexicon gives longer entries. index.md is not one of
  the two frozen-prose pages.
- `dev/docs/guide.md` ("Checked guide") gives the developer's view. It covers
  where the checker and sample are, how to run only these tests
  (`uv run pytest tests/docs`), how to read a failure, how to add a word to
  the sample, and that adding a word can change `info` and `Also:` lines on
  other pages.
- `dev/docs/testing.md` gains the `tests/docs/` row. Its rule, "add it to the
  fixture rather than building a second one", gains one exception: the docs
  sample, for the reason in §7.1.

---

## 6. Pinning width and clock

One function holds the environment of every example and of the sample build:

```python
def docs_env(home: Path) -> dict[str, str | None]:
    return {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "HARALD_CONFIG": None,
        "COLUMNS": "80",
        "FORCE_COLOR": None,
        "TTY_COMPATIBLE": None,
    }
```

It lives in `tests/docs/sample.py` and the checker imports it. That module is
the one both callers already depend on (§7.3).

### 6.1 Width

- **What depends on it.** `harald.render` adapts to Rich's console width: the
  narrow layout below 60 columns, conjugation tenses per row, wrapping, and
  `Padding` filling lines to the width. Click's help and usage text wraps to
  its formatter width.
- **Mechanism.** `COLUMNS=80`. Rich reads it when `Console()` is constructed,
  and `_print` constructs one per call, inside the isolation. Without it, Rich
  asks `os.get_terminal_size` on fds 0, 1 and 2, and stdin is the
  developer's real terminal under an interactive pytest, so the width would
  follow the window. Click is already forced to 80 by
  `CliRunner.isolation()`.
- **Colour.** The captured stdout is not a TTY, so Rich emits no ANSI codes,
  unless `FORCE_COLOR` or Rich 14+'s `TTY_COMPATIBLE` forces terminal mode.
  Both are deleted, because a developer's shell may set them.
- **No other widths.** The spec pins 80. The 40-column phone layout stays
  prose, and the TUI tests already verify it at 40 columns.

### 6.2 Clock

**What a CLI command can show** (audited with `grep` over `src/harald`):

| Read | Where | Shown by | Pinned by |
|---|---|---|---|
| Source date | `fetch.source_date` reads `last_modified` from the `.meta.json` sidecar, and only while its `sha256` matches the file (never the mtime) | `info`, and every `build` | the sample builder writing each sidecar with `DOCS_SOURCE_DATE = "Sun, 01 Nov 2026 00:00:00 GMT"`, so dates print as `2026-11-01` |
| `time.monotonic()` | `build/run.py` (stage and total timings), `build/graph.py` (`run_job` seconds) | `build` when it rebuilds: stage lines, `(jobs … s)`, `… in … s` | the frozen clock below |
| `datetime.now`, `time.monotonic` | `tui/addword.py`, `tui/study.py` | the TUI only; no CLI path reaches it | n/a |

**Mechanism.** For every example:

```python
FROZEN_CLOCK = types.SimpleNamespace(monotonic=lambda: 0.0)
monkeypatch.setattr(harald.build.run, "time", FROZEN_CLOCK)
monkeypatch.setattr(harald.build.graph, "time", FROZEN_CLOCK)
```

- The patch is narrow: those two modules see a frozen clock, and nothing else
  in the process does. If either module starts using another `time` function,
  it raises `AttributeError`, a loud failure rather than a silent unpinned
  read.
- It works only in process, and only with `build_workers = 0` (§5.5). Pool
  workers start by forkserver and re-import the modules.
- **Sidecars.** The builder gzips with `mtime=0`, so the gzipped bytes and
  their sha are stable. It writes `{"sha256": …, "last_modified":
  DOCS_SOURCE_DATE}` through `fetch.sidecar_path`. Those are the two keys
  `source_date` reads; the other keys only matter to a fetch, which never runs
  here. Without sidecars, `info` would print `unknown` and every build would
  warn `no trusted date …`, which a real user never sees.
- **Tatoeba.** The sample has no Tatoeba files, so `info` lists Tatoeba as
  `unknown`. That is true of the sample lexicon, which has no sentence pairs.
  When phrase mode (018) lands, it adds Tatoeba sample sources and sidecars
  (G13).
- **Who uses the clock pin.** 032 shows one `harald-cli build --force` on
  build.md under "Guarantees". It proves "rebuilt identical bytes: published
  file left untouched" and shows what a build prints, with timings at 0.0 s,
  as "About the examples" says. If 032 decides against that example, the pin
  stays anyway: it is what keeps any future `build` example deterministic.
- **A new CLI clock read** shows up as a failing example on its first run. One
  likely case is 022's timestamped backup file name. The fix is to extend the
  pin, and the docstring lists the pinned modules. No guard test is added for
  it (§15.8).

---

## 7. Sample data

### 7.1 Where: `docs/examples/`, separate from `tests/fixtures/`

**Decision.** The guide gets its own hand-cut sources,
`docs/examples/en-edition.jsonl` and `docs/examples/de-edition.jsonl`. They
are excluded from the site (`exclude_docs: examples/`).

**Why not reuse or extend `tests/fixtures/*.jsonl`:**

- Several outputs depend on the **whole** lexicon, not only on the word shown.
  `info`'s coverage lines count every verb, noun and sense, `build` prints the
  entry and bad-line counts, and fuzzy lookup's `Also:` line names neighbours.
  `dev/docs/testing.md` tells every slice to "add it to the fixture rather
  than building a second one". Shared, every test that adds an entry would
  break a guide page.
- The test fixture is test-shaped: a line with no `word`, foreign-language
  lines (French *Hund*), a deliberately broken line kept last. The guide
  would show `1 bad lines` and a coverage report shaped by edge cases.
- The precedent agrees: kohle's sample files are "not from `tests/fixtures/`,
  which is free to change for test reasons".

**Why `docs/examples/` and not `tests/fixtures/docs/`:**

- The sample is owned by the pages. A word is added to it because a page shows
  that word, in the same PR. Keeping it next to the pages makes that pairing
  visible.
- Under `tests/fixtures/` it would be the natural target of the project's own
  "add it to the fixture" rule, which recreates the coupling above.
- The spec names `docs/examples/` as the alternative, and kohle uses it.

It is excluded from the site because no page links to it. Publishing raw
Wiktionary excerpts adds nothing for a reader, and the repository already
carries such excerpts under the same licence.

### 7.2 Content

- Real wiktextract lines, hand-cut from the kaikki dumps as the test fixture
  was, so that the importer parses them exactly as it parses the real data.
  The implementer may start from the fixture's lines for laufen, lief and use.
  That copies data, not files.
- The sample covers exactly the words the checked examples run. 029:
  `lief`/`laufen` and `use`. 032: whatever getting-started.md and build.md show
  (for example `gehen` for `--conj`). 033's taste reuses 029's words.
- No bad lines, so `build` prints `0 bad lines`.
- German-edition lines for a word only where a page wants to show the German
  block.
- **Personal data.** The words are dictionary words chosen for the pages. None
  may be taken from the user's own deck. The implementer cannot check that,
  and must never open the real `learning.db` to try (G12).
- **Accepted coupling within the docs.** Adding a word to the sample can change
  `info`'s coverage lines and another example's `Also:` line. The slice that
  adds the word updates those pages, and the checker makes sure it does.

### 7.3 Built once per session

`tests/docs/sample.py`:

```python
DOCS_SOURCE_DATE = "Sun, 01 Nov 2026 00:00:00 GMT"   # also stated in docs/index.md
CONFIG_TOML = "build_min_entries = 0\nbuild_workers = 0\n"

def docs_env(home: Path) -> dict[str, str | None]: ...          # §6
def build_sample_home(home: Path) -> Result[None, str]: ...     # Err carries the build output

if __name__ == "__main__":   # python -m tests.docs.sample DIR, used by the VHS tape
    ...
```

`build_sample_home`:

1. It gzips `docs/examples/en-edition.jsonl` to
   `home/.local/share/harald/sources/raw-wiktextract-data.jsonl.gz`, and the
   `de` file to `de-extract.jsonl.gz`, with `gzip.GzipFile(…, mtime=0)`. It
   uses `EN_FILENAME` and `DE_FILENAME` from `harald.build.sources`.
2. It writes each sidecar (§6.2) with `sidecar_path` and `sha256_file`, reused
   from `harald.build.fetch` and `harald.build.publish`.
3. It writes `home/.config/harald/config.toml` with `CONFIG_TOML`.
4. It runs `harald.cli.main(["build"])` inside
   `CliRunner().isolation(env=docs_env(home))`, then returns `Err(output)` if
   the exit code is not 0.

The template is made by the real command, through `load_config` and the
default paths, as kohle makes its template ledger with the real `init`. That
writes the staging last-build record too, so `harald-cli build` on a copy
reports `unchanged`. The record holds a fingerprint and a sha, with no paths,
so the copy matches.

The session fixture in `test_docs_examples.py`:

```python
@pytest.fixture(scope="session")
def sample_home(tmp_path_factory: pytest.TempPathFactory) -> Path:
    home = tmp_path_factory.mktemp("docs-sample") / "home"
    built = build_sample_home(home)
    assert built.is_ok, built.unwrap_err()
    return home
```

After that it is only read, by `shutil.copytree` per example. The build costs
about 0.3 s once. A copy of the small tree costs a few milliseconds, so 30
examples pay roughly 0.3 s in total and not 9 s. A session fixture cannot use
function-scoped `monkeypatch`, which is why the builder applies its
environment through `isolation(env=…)`.

---

## 8. Generated CLI reference (030)

`docs/reference.md`:

```markdown
# Command reference

Generated from `harald-cli`'s own help when the site is built. On GitHub this
page shows only the directive below; run `harald-cli COMMAND --help`, or read
the published guide.

::: mkdocs-click
    :module: harald.cli
    :command: cli
    :prog_name: harald-cli
    :depth: 1
    :style: plain
    :list_subcommands: true
```

- `mkdocs-click` is added to `markdown_extensions`, and the page is added to
  the nav as "Command reference".
- **`:style: plain`, not kohle's `table`.** Plain style renders Click's own
  help formatter, so `show_envvar=True` on `--config` prints
  `[env var: HARALD_CONFIG]` from the option's `envvar=` declaration. Table
  style prints only `option.help`, so the variable name would have to be
  restated in the help string, a second source that can drift. That breaks
  "Click help text is the one source". As a side effect, `harald-cli --help`
  shows the variable too.
- `:prog_name:` makes headings and usage read `harald-cli …`, not `cli …`.
- Rendering builds Click contexts and never invokes a command, so building the
  docs never reads a config or opens a lexicon. It imports `harald.cli`, whose
  imports are already kept light (`test_lookup_does_not_import_heavy_modules`).
- **Help text.** The group has no help today, and the command help strings are
  lowercase fragments next to Click's "Show this message and exit." 030 gives
  the group a one-sentence description and turns each command and option
  string into a sentence-case sentence ("Build lexicon.db from the locally
  kept sources."). It changes wording only, not behaviour (spec Non-Goals).
- **Option lists leave the pages.** The lookup.md and build.md synopsis fences
  and build.md's "Flags" section go. build.md's behaviour sentences there (the
  task graph, `build_workers`, what the build prints) stay under another
  heading. Each page links to the reference. The prune fence on build.md stays
  `illustration`: it shows behaviour (asks versus does not ask), not an option
  list. configuration.md's `--config PATH` / `HARALD_CONFIG` sentence is
  behaviour, and stays.
- **Build command.** CI and the README move to
  `uv run --with-requirements docs/requirements.txt mkdocs build --strict -f docs/mkdocs.yml`,
  and `pip install` goes (AC 030). The project environment is needed because
  mkdocs-click imports harald.
- **The `harald` TUI command** has its own `--config`. It is not part of the
  `harald-cli` group, so the reference does not cover it (spec), and
  configuration.md's prose does (G17).
- **To verify on the first build:** mkdocs-click 0.9.0 runs against Click 8.5.0
  here, while kohle runs Click 8.3.1. If it breaks, use the newest mkdocs-click
  that supports Click 8.5, still pinned (G18).

---

## 9. TUI key tables (031)

### 9.1 How a table names its screen

```markdown
<!-- docs: keys add-word -->
| Key | Does |
|---|---|
| `space` | tick or untick a row |
| `n` / `b` | next / back |
```

- A **key table** is a table whose header row is exactly `Key | Does`. Both
  existing key tables use it. configuration.md's `Key | Default | Meaning`
  table describes config keys and does not match. The header is what makes a
  key table that names no screen detectable (problem 9).
- The `keys SCREEN` comment sits on the line directly above it. Both
  markdown-it and Python-Markdown accept that with no blank line in between
  (verified).
- A row's keys are the backticked spans of its first cell, so `n` / `b` gives
  `n` and `b`. Keys are written as the guide already writes them: `esc`, `/`,
  `space`, `enter`, a letter or a digit. They are compared through
  `textual.keys.format_key` on both sides, so `esc` matches `escape` and `/`
  matches `slash`, the names Textual's own footer uses. There is no alias table
  of our own.

### 9.2 Widget keys

```python
KEY_SCREENS = {
    "home":     (HomeScreen,    (OptionList,)),
    "lookup":   (LookupScreen,  (Input, OptionList)),
    "entry":    (EntryScreen,   ()),
    "add-word": (AddWordScreen, (SelectionList,)),
    "study":    (StudyScreen,   (Input,)),
}
```

- The mapping lives in `tests/docs/checker.py`, next to the vocabulary it
  closes. The checker reports an unknown screen name from its keys.
- **The keys a screen handles** are the union of the bindings over the MRO of
  the screen class, of `HaraldApp`, and of each declared widget class. Each
  class's own `BINDINGS` is read from its `__dict__` and expanded with
  `Binding.make_bindings`. The MRO walk matters: `SelectionList` declares only
  `space`, and inherits `enter` and the arrows from `OptionList`.
  `Screen.BINDINGS` adds `tab`/`shift+tab`, and `App` adds `ctrl+q`. Textual's
  `_merged_bindings` would give the same set, but it is private.
- **A declared widget must be real.** The test parses `inspect.getsource` of
  the screen's `compose` with `ast` and requires a call whose callee is the
  widget class's name. A subscripted callee such as
  `SelectionList[object](…)` counts. Without this, a screen that stopped
  using a widget would let that widget's keys keep passing, which is exactly
  the silent drift the test exists to catch.
- Today's tables need these widget keys: `space` (SelectionList) on add word,
  and `enter` (Input submit, OptionList select) on lookup. Study's `enter` is
  also a screen binding (`continue`). Home's OptionList is declared because it
  is the screen's menu, though its table lists only letters.

### 9.3 `tests/docs/test_key_tables.py`

- `test_key_table[docs/user/study.md:22]`, one per table:
  - **every row is handled.** Each key of each row is in the handled set
    (§9.2). Failure: `docs/user/study.md:25: \`x\` is not handled by
    AddWordScreen (or its declared widgets SelectionList)`.
  - **every visible binding has a row.** Each binding in the screen's and the
    app's MRO with `show=True` has its key in the table. Failure:
    `AddWordScreen binds \`h\` (Note) visibly, but docs/user/study.md:22 has
    no row for it`. Hidden bindings (Home's `l`/`s`/`i`, study's `1`/`2`) may
    be documented and need not be. "Visible" means declared `show=True`;
    `check_action` hides some bindings per step, but they are still visible
    bindings.
- `test_each_screen_has_one_key_table`: the screens named across all pages
  are exactly `KEY_SCREENS`, each once. Two tables for one screen would be two
  sources for the same facts (problem 11).
- `test_declared_widgets_are_composed`: §9.2.

The test needs no lexicon and runs no app, so it is pure class inspection in
milliseconds.

### 9.4 Tables in 031

| Screen | Page | Today | 031 |
|---|---|---|---|
| home | getting-started.md, Browse in the TUI | table `l s i q` | adds the `keys home` comment |
| add-word | study.md, Add a word | table `space`, `n`/`b`, `h`, `c`, `esc` | adds the `keys add-word` comment |
| lookup | getting-started.md | prose bullets only | adds a table: `enter` searches, then opens the highlighted result; `/` back to the query; `esc` from the results back to the query, else back |
| entry | getting-started.md | prose bullets only | adds a table: `c` all tenses; `a` add the word as cards; `esc` back |
| study | study.md, Study | none (keys spread over the card table) | adds a table: `enter` checks the answer, then goes on after the verdict; `space` goes on after the verdict; `1` / `2` Again / Good on a self-graded card; `esc` ends the session |

The spec names all five screens, and the test's purpose ("a rebound key goes
unnoticed") needs a table for each. The three new tables restate only what the
adjacent prose and the bindings already say, and no existing prose changes
(AC 031). "Key-table markup" therefore covers new tables as well as the
comment on the existing two (G3, decided). Info, the end-of-session summary
and the Pick-entry and Note dialogs have keys but are not among the five
screens. They get no table in this sweep, and tables for them are a recorded
follow-up (G9, decided).

---

## 10. The remaining pages (032)

Per page, with the temporary markers from 029 removed or confirmed:

- **getting-started.md.** Only fences, key-table markup, and one prose
  sentence change.
  - The `uv run` sentence goes under "Install": on the desktop, run the
    commands below through `uv run` (`uv run harald-cli lookup lief`). The
    spec requires the sentence, and it is the only prose change on this page
    (G4, decided). 031's new key tables are markup, not prose.
  - The Termux fence stays `illustration`. Its comment becomes "about 11
    minutes on a recent phone".
  - "Build the lexicon" (`build --fetch`) and the `prune` fence stay
    `illustration`, written bare.
  - "Look something up" becomes a console block: `lookup lief`,
    `lookup --conj gehen`, `lookup --en use`, with the current comments
    dropped or kept as `#` comments.
  - "See what you built from" becomes a console `harald-cli info`.
  - The TUI fence shows bare `harald` in an `sh` fence (not runnable here).
- **study.md.** Only fences and key-table markup change. `uv run harald`
  becomes `harald`. The audit `sh` fence (`cp`, `python3 …`) has no
  `harald-cli` and stays as it is.
- **build.md.** It keeps the `prune` illustration and may add a checked
  `harald-cli build --force` under "Guarantees" (§6.2). An unchanged
  `harald-cli build` example shows the "unchanged: ~/.local/share/harald/lexicon.db
  left untouched" path.
- **configuration.md, data.md.** They have no `harald-cli` fences. data.md may
  show a checked `harald-cli info` where it says `info` prints the
  attribution.
- **mkdocs.yml.** `admonition` is removed.
- **Personal data.** "a Pixel 9" goes (above). The note
  `to call someone on the phone` and the words in study.md's prose are frozen
  until the content pass. The user confirms that none is their own (G12).
- The sample is extended for every new example word (§7.2).

---

## 11. README (033)

- It holds only: the pitch (the "reading, TV and conversation" line, as on
  `docs/index.md`), the taste, the GIF (034), a link to
  `https://hariceratops.github.io/harald/`, how to read the guide locally,
  the licence and data note, and the roadmap.
- **Taste:** one console block, `$ harald-cli lookup lief` and
  `$ harald-cli lookup --en use`, checked like any page. It must be the
  README's only console block, because the tape test (§12) takes "the README
  block" to mean it. An ordinary comment above it says the tape mirrors it,
  and is not a `docs:` comment.
- **Reading locally:**
  `uv run --with-requirements docs/requirements.txt mkdocs serve -f docs/mkdocs.yml`.
- **Removed sections are accounted for in the PR**, statement by statement
  (kohle precedent):
  - Use case and Features become guide pages, and any statement no page holds
    goes into `index.md`;
  - status notes ("not yet verified on the phone") go into the roadmap;
  - Quick start goes into getting-started.md, which already has it;
  - Development (pytest, ruff, mypy, AGENTS.md, `dev/`) goes into
    `dev/docs/testing.md` and `workflow.md`, which already have it.
- **Roadmap:** written by hand, one generic line per open brief in
  `dev/inbox/` (the spec's rule). It names no device, sync arrangement or
  level ("a Pixel 9", Syncthing and "B1" appear in the briefs). It is not
  generated: deciding what a brief still leaves open takes judgement.

---

## 12. Demo GIF and tape test (034)

- **Files.** `docs/demo/taste.tape` writes `docs/demo/taste.gif`. The tape is
  excluded from the site.
- **Run** from the repository root: `vhs docs/demo/taste.tape`. vhs, ttyd and
  ffmpeg are system tools, never Python dependencies.
- **Hidden prelude:**

```
Hide
Type "source .venv/bin/activate; export PS1='$ '" Enter
Type `D=$(mktemp -d); python -m tests.docs.sample "$D"` Enter
Type `export HOME=$D XDG_CONFIG_HOME=$D/.config XDG_DATA_HOME=$D/.local/share XDG_CACHE_HOME=$D/.cache COLUMNS=80; unset HARALD_CONFIG; cd "$D"; clear` Enter
Show
```

  - `python -m tests.docs.sample` builds the same sample home the checker
    uses, so the GIF shows the same output as the checked README block. A
    shell copy of the gzip, sidecar, config and build steps could drift
    silently.
  - The venv is activated before `HOME` is faked. `uv run` under a fake `HOME`
    would resolve a fresh uv cache, which is slow and needs the network.
  - `COLUMNS=80` pins Rich exactly as the checker does. `Set Width` and
    `Set FontSize` give the terminal at least 80 columns, so nothing wraps.
  - The neutral prompt and the temporary home keep the user name, host and
    paths out of the recording.
- **Visible part:** one `Type "harald-cli …" Enter`, `Wait`, `Sleep` per taste
  command. `Set WaitPattern` waits for the prompt rather than a guessed pause
  (kohle's lesson).
- **`tests/docs/test_demo_tape.py`:**

```python
def test_the_demo_tape_types_the_readme_taste_in_order() -> None:
    (taste,) = [e for e in collect(ROOT).examples if e.page == "README.md"]
    assert _typed_while_shown(TAPE.read_text()) == [c.text for c in taste.commands]
```

  `_typed_while_shown` walks the tape's lines. `Hide` and `Show` toggle a
  flag, and while the tape is shown, a `Type` line (`Type "…"` or
  ``Type `…` ``, with an optional `@speed`) yields its string. The README side
  is the command text as written after `$ `. Text and order must both match
  (AC 034). The tuple unpacking also fails if the README has no console block,
  or more than one.
- The GIF is never regenerated in CI or in the suite. `dev/docs/demo-gif.md`
  gives the regeneration steps, the tools and where to get them, and a check
  of the first and last frames for a leaked path before committing.

---

## 13. Pages workflow (035)

`.github/workflows/docs.yml`, as left by 030, gains the docs tests and the
deploy:

```yaml
name: docs
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
permissions:
  contents: read
jobs:
  # The docs tests run first: a failing example stops the job, so nothing is
  # built or published. The build installs harald too: mkdocs-click imports
  # harald.cli. --frozen, so a stale lock does not turn the docs check red.
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          python-version: "3.12"
      - run: uv run --frozen pytest tests/docs
      - run: uv run --frozen --with-requirements docs/requirements.txt mkdocs build --strict -f docs/mkdocs.yml
      - uses: actions/upload-pages-artifact@v3
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        with:
          path: site
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    concurrency:
      group: pages
      cancel-in-progress: false
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- **Triggers** stay as they are today: pushes to `main` and PRs to `main`. The
  spec asks only that PRs build and do not publish. Kohle's every-push trigger
  came from its own spec.
- **The docs tests gate the deploy (G7, user decision 2026-11-08).**
  `uv run --frozen pytest tests/docs` runs the checked examples, the key-table
  test and the tape test before the build. This goes beyond the spec, which
  names only the strict build as the gate. With it, the published guide is
  always a checked one. It runs on PRs too, so a PR whose examples fail shows
  red. Only `tests/docs` runs here, because the rest of the suite is not the
  guide's gate. The step needs nothing beyond the `dev` group that `uv run`
  already syncs, and the examples block network access themselves (§5.5).
- **A failed test or build publishes nothing.** The artifact is uploaded only
  after both steps succeed, and `needs: build` keeps deploy from running
  otherwise. The deploy condition checks the event as well as the ref, so a PR
  from a branch named `main` cannot publish.
- **Python 3.12.** The project has no Python pin (dropped for Termux), so
  setup-uv would otherwise choose the newest interpreter. The spec's toolchain
  is 3.12.
- **The `dev/docs/` site** is never named by the workflow.
- `concurrency` on the deploy job keeps two deploys from overlapping without
  serialising PR builds.
- The action versions are kohle's. Bumping them is a separate change.
- `docs/mkdocs.yml` gains `site_url: https://hariceratops.github.io/harald/`,
  `repo_url: https://github.com/hariceratops/harald` and
  `edit_uri: edit/main/docs/`.
- **One-time setting,** noted in `dev/docs/guide.md` under "Publishing": set
  the repository's Pages source to "GitHub Actions". Pages on a private
  repository needs a paid plan. This stays a manual step, also noted in 035
  (G8).

---

## 14. AGENTS.md (036)

A `## Documentation` section, written after 028–035 so that it matches what
they built:

- `docs/` is the user-facing description of behaviour, published to GitHub
  Pages from `main`. The README is only a pitch that points to it.
- Builds: `uv run --with-requirements docs/requirements.txt mkdocs build
  --strict -f docs/mkdocs.yml` for the guide, and the same with
  `-f dev/docs/mkdocs.yml` for the developer notes, which are local only.
  `serve` reads either live.
- CI runs `uv run --frozen pytest tests/docs` and the guide's strict build on
  every PR, and publishes from `main` only when both pass.
- Every `console` block in `docs/` and `README.md` runs in `uv run pytest`.
  The module docstring of `tests/docs/checker.py` defines the syntax, the
  `docs:` options and key tables. The sample lexicon's sources are
  `docs/examples/`. Command output is shown only in console blocks.
- A slice that changes user-visible behaviour updates the matching page in the
  same PR.
- When an example's output changes, the page is fixed, never the example
  loosened.
- The README roadmap follows the briefs in `dev/inbox/`.
- Personal data: the user's own cards, notes, decks, review history, the words
  they are learning, and their own setup (devices, paths, sync arrangements)
  never appear in user-facing docs. Examples use the sample lexicon's words and
  invented notes.

The section sits after `## Conventions`. It is a documentation rule set, not
an override of a global rule, so it needs no justification block.

---

## 15. Cross-cutting decisions

### 15.1 State and data lifecycle

- **Per example:** the scratch home is the unit. It is created whole before
  the first command (copy, chdir, environment, clock, network block) and
  discarded with `tmp_path`. Commands share it in order, and the first
  mismatch ends the example. Nothing crosses examples.
- **Template home:** written once per session by the real `harald-cli build`,
  then only read by `copytree`. The build publishes with an atomic rename and
  its staging is cleaned, so a finished template is a consistent snapshot. If
  the build fails, no template exists and every example errors.
- **Docs build:** read-only, apart from `site/` and `site-dev/`. mkdocs-click
  never invokes a command.
- **Deploy:** all or nothing through the Pages artifact, which is built only
  after the docs tests and the strict build pass.
- **GIF:** regenerating overwrites one committed binary, by hand, from a temp
  home.
- Nothing here needs to be reversible, replayable or audited. No write path in
  harald changes.

### 15.2 Error propagation

- **harald to checker:** the checker sees only text, the interleaved
  stdout/stderr of `main`. It never sees harald's error types, which keeps the
  page the contract. An exception escaping `main` is a bug, and it reaches
  pytest unchanged with its traceback (§5.6).
- **Checker to pytest:** page faults become problem strings, reported together
  by one test. A mismatch becomes failure text through
  `pytest.fail(pytrace=False)`. A failed template build is an assertion in the
  session fixture that carries the build's output.
- **Key tables:** structural faults are checker problems. Mismatches against
  bindings are assertions naming the page line and the screen class.
- **Sample builder:** returns `Result[None, str]`. The fixture asserts on it,
  and `python -m` exits with the error text.
- **Docs build:** an mkdocs-click import error, or any strict warning (nav,
  link, anchor), fails the build, and so the deploy. Nothing catches it.
- **CI:** a failing docs test ends the job before the build, so a red example
  blocks publishing exactly as a broken link does.

### 15.3 Concurrency and ownership

All of this is single-threaded. Examples run one after another in one pytest
process, and the project has no xdist. The build runs inline
(`build_workers = 0`), so no pool starts inside pytest. Its reader thread is
the build's own and finishes before `build()` returns.

The process-global state an example touches is `os.environ`, `sys.stdout`,
`sys.stderr` and Click's forced width (restored by `isolation`), the working
directory, `socket.socket.connect`, and the `time` attribute of two harald
modules (restored by `monkeypatch`). The template home is shared and
read-only. Under xdist, each worker would build its own template, and nothing
here would break. In CI, the two jobs are ordered by `needs:`, and deploys are
serialised by `concurrency`.

### 15.4 Reuse

| What already exists | How it is used |
|---|---|
| `harald.cli.main` | the runner and the sample build call the real entry point |
| `CliRunner.isolation` (Click) | capture, env and Click's width, without `invoke`'s standalone mode |
| `EN_FILENAME`, `DE_FILENAME`, `sidecar_path`, `sha256_file` | the sample layout and its sidecars |
| the `workspace` fixture's gzip-the-JSONL pattern | followed, with `mtime=0` added |
| markdown-it-py (locked through rich and textual) | fence and table parsing |
| `Binding.make_bindings`, `textual.keys.format_key` | expanding and comparing keys |
| kohle's checker shape (`parse_page` / `collect` / `run_example`, problems as strings, ids `page:line`, meta-tests), workflow and tape test | followed, adapted (§15.9) |
| `harald.core.option.Option`, `harald.core.result.Result` | the return types |

**Not reused, and why:**

- The `workspace` and `built` fixtures: they are function-scoped, carry
  absolute paths in their config, and use the test-shaped fixture (§7.1).
- `tests/smoke`'s subprocess `_harald`: the clock pin needs the process
  (§15.8).

**Introduced and reusable later:** the checker for any page; `KEY_SCREENS`, so
a new screen with a table is one entry; the sample builder for any future
demo; `docs_env`.

### 15.5 Extension points

- The `docs:` vocabulary is closed. A new word is an edit to the checker and
  its docstring.
- `KEY_SCREENS` is the place a new screen joins the key-table check. The
  contract is a name, a `Screen` class and the widget classes its `compose`
  constructs.
- The sample sources grow by adding lines. Phrase mode (018) adds Tatoeba
  samples and sidecars to the builder.
- No plugin, hook or MkDocs extension of our own is introduced. Nothing else
  is meant to be plugged into.

### 15.6 Build vs. buy

| Component | Decision | Evaluated, and what it could not do |
|---|---|---|
| Site generator | buy: MkDocs 1.6 + material | given by the spec |
| Command reference | buy: mkdocs-click | sphinx-click comes with Sphinx (a spec non-goal); a hand-written list is what drifts today |
| Example checker | **build** (~200 lines) | **pytest doctest / `--doctest-glob`**: runs Python `>>>` sessions, so pages would show Python, not `$ harald-cli`. **pytest-markdown-docs, phmdoctest**: run Python fences only. **cram / prysk**: transcripts through a real shell subprocess, so the build clock cannot be pinned without a production hook, and each command pays an interpreter start. **Sybil**: a framework in which we would still write the console parser, sample home and clock pin; it adds only the per-block plumbing that `parametrize` gives in a few lines, at the cost of a test dependency. **pytest-console-scripts**: runs entry points but parses no markdown. **kohle's `tests/docs_examples.py`**: copied in shape, not shared. There is no shared package between the projects, and its ledger, `KOHLE_DB` and `file`/`uses` machinery do not apply. |
| Fence and table parsing | reuse markdown-it-py | a line regex misses CommonMark fence rules (list items, `~~~`, fence length) and cannot tell a table from a paragraph |
| Key-table check | **build** (~60 lines) | nothing compares markdown tables with Textual bindings. Textual's `Footer` and `KeyPanel` show bindings at runtime only. Generating the tables was rejected (§15.8). |
| Sample lexicon | build it from shipped JSONL each session | a committed `lexicon.db` is binary, bound to `SCHEMA_VERSION`, and against the never-redistribute rule for the built file |
| GIF | buy: VHS | **asciinema + agg** records a live session, not scripted typing. **terminalizer** records interactively, then edits a config. VHS is built for "rerun the script". |
| Pages deploy | buy: `upload-pages-artifact` + `deploy-pages` | `mkdocs gh-deploy` pushes a `gh-pages` branch with a write token; artifacts are kohle's and s2s's choice |
| CI Python environment | uv (`setup-uv`) | `setup-python` + `pip` ignores `uv.lock`, and cannot install harald for mkdocs-click without a separate step |

### 15.7 Abstractions introduced

Each one is listed with the problem that forces it. Anything not listed was
collapsed.

1. **`Command` / `Example`.** The parametrised test, the meta-tests on
   synthetic pages and the failure text all need a parsed block that is
   separate from running it.
2. **`KeyRow` / `KeyTable`.** The key-table test verifies parsed tables
   against classes. The checker parses them, because `keys` is part of its
   vocabulary.
3. **`Parsed`.** One parse has three outputs. A named record reads better at
   every call site than a 3-tuple.
4. **The two option words.** Each answers named pages (§5.2).
5. **`KEY_SCREENS`.** It resolves a page's screen name to a class and to the
   widgets whose keys count. The declaration has to sit somewhere, and code is
   the only place class references can be checked (§9.2).
6. **`docs_env`.** It has two callers, the per-command isolation and the
   template build, and they must agree on every path.
7. **`tests/docs/sample.py` with a `__main__` guard.** It has two callers,
   the session fixture and the VHS tape, which must build the same lexicon.
8. **`FROZEN_CLOCK`.** The build prints `time.monotonic()` differences, and a
   pinned example needs them fixed.

**Not introduced:** a custom pytest collector or `Item`, a runner class, an
option parser beyond splitting on whitespace, an alias table for key names, an
MkDocs hook, an update-the-pages mode.

### 15.8 Alternatives rejected

- **Reusing or extending `tests/fixtures/*.jsonl`.** Whole-lexicon outputs
  would break pages on every test addition, and the fixture shows bad and
  foreign lines (§7.1).
- **Sample under `tests/fixtures/docs/`.** It invites the "add it to the
  fixture" rule and hides the page-to-sample pairing (§7.1).
- **Publishing `docs/examples/`.** No page links to it, so it adds nothing for
  readers.
- **A committed sample `lexicon.db`** (§15.6).
- **Building the sample per example.** It costs 0.3 s each. A copy costs
  milliseconds.
- **One shared sample home, not copied.** A `build` example writes to it, and
  isolation per example is the spec's starting state.
- **A subprocess per command,** as `tests/smoke` does. It cannot pin the build
  clock without a production hook, and pays an interpreter start per command.
- **`CliRunner.invoke(cli)`.** Standalone mode bypasses `main`'s error and
  exit-code mapping (§5.6).
- **A production clock hook** (`HARALD_CLOCK`-style). That is test-only code in
  production, the reason kohle rejected `KOHLE_TODAY`.
- **Patching `time.monotonic` globally.** It freezes every caller in the
  process, not only the build.
- **Normalising timings or dates with a regex.** That weakens "exact".
- **A guard test that scans `src/` for clock reads.** A new read already fails
  the example that shows it, loudly, on its first run.
- **`unknown` source dates** (no sidecars). Pages would show a warning and
  dates a real user never sees.
- **Empty Tatoeba stand-in files** to give Tatoeba a date. That would be fake
  sources for a mode that does not exist yet.
- **Options in the fence info string, or a custom language tag** (kohle
  §15.8). Renderers may refuse unknown info words, and a custom tag loses
  `console` highlighting.
- **A required run marker on every block.** A forgotten marker would silently
  uncheck a session.
- **A temporary exemption list for 029–032.** The spec says no exemptions, so
  visible `illustration` markers are used instead (§5.9).
- **Option words `width N`, `first-run` / `no-lexicon`, `file` / `uses`,
  `exit N`.** The spec pins 80 columns. No page shows a missing lexicon. No
  page applies a file it shows. Exit codes are not compared. Each is a small
  addition later.
- **`NAME=value` prefixes and ` \` continuations.** No page needs them.
- **Naming a table's screen in its heading or in a column.** It couples
  visible prose to the test and adds visible noise.
- **Generating key tables from `BINDINGS`.** The spec asks for hand-written
  tables. Binding descriptions ("Back", "Next") are too terse for readers, and
  widget keys are not in a screen's `BINDINGS`.
- **Declaring widget keys in the page** (`keys add-word widget=space`). A page
  could declare any key widget-handled and pass unchecked.
- **A `WIDGET_KEYS` attribute on each screen.** It is test-only metadata in
  production code.
- **Discovering keys at runtime with the pilot.** Every screen would need its
  own setup (a headword, due cards), and the active set depends on focus and
  state.
- **Textual's private `_merged_bindings`.** The public MRO walk gives the same
  set.
- **Requiring hidden bindings in tables.** The spec says visible.
- **CI without the docs tests,** the spec's literal gate. A page with a
  failing example could then be published (G7). **The whole suite in the docs
  workflow** was not chosen either: the guide's gate is the guide's own checks
  (user decision). **A separate test job** with `deploy: needs: [test, build]`
  would show both failures at once, but costs a second environment setup. One
  job, tests first, is enough.
- **mkdocs-click `:style: table`,** or restating `HARALD_CONFIG` in the help
  string (§8).
- **Publishing or CI-building `dev/docs/`; dev pages kept in `docs/` but out
  of the nav.** The spec forbids the first. The second would still copy them
  into the site.
- **Relative links from `dev/docs/` into `docs/`.** They fail strict (§4.3).
- **Generating the tape from the README.** The tape test is enough. **A shell
  copy of the sample build in the tape.** It could drift from the checked
  lexicon (§12).
- **`mkdocs gh-deploy`** (§15.6).
- **Admonitions or tabs in pages.** Their fences are invisible to the parser,
  and they do not read on GitHub.
- **An `--update-docs` mode that rewrites expected output.** It invites
  accepting output without reading it.

### 15.9 Where this departs from kohle

| kohle | here | why |
|---|---|---|
| README joins the checker in the README-cut slice (G11) | README scanned from 029, with a temporary marker | spec: "covers every page from the start" |
| `CliRunner.invoke(cli, obj=None)` | `isolation` + `harald.cli.main` | harald's `main` does the exit-code and error mapping |
| template ledger from `kohle-cli init` | template home from `harald-cli build` | the same idea for this app's data |
| `pin_today` patches `date` | frozen `monotonic` and sidecar dates | harald's CLI never reads today; it reads a monotonic clock and recorded dates |
| `file`, `uses`, `first-run`, `illustration` | `illustration`, `keys` | no page needs the others; key tables are new |
| `NAME=value` prefixes, ` \` continuations | neither | no page needs them |
| mkdocs-click `:style: table` | `:style: plain` | the env var is shown from Click's declaration |
| every push and PR | push to `main`, PRs to `main` | harald's existing triggers; the spec asks no more |
| CI runs the docs build and nothing else | CI also runs `pytest tests/docs`, before the build | user decision (G7): publish only a checked guide |
| `setup-uv` with no Python | `python-version: "3.12"` | harald has no Python pin |

---

## 16. Gaps, conflicts and readings

Each item records the decision taken. **[confirm]** marks the one still open.
The user decided G3, G4, G7, G9 and G14 on 2026-11-08. G1, G2, G5 and G6 are
being written into the issue files.

- **G1. Checker from the start, conversions later.** The spec says the
  machinery covers every page from the start with no exemptions, and 029
  converts only `lookup.md`. Decision: 029 marks every other `harald-cli`
  fence, and the README's Quick start, `illustration`, and 032 converts them
  (§5.9). The issues did not say so, and are being updated (2026-11-08).
- **G2. 031 depends on 029,** not only on 028, because `keys` is a checker
  option. Being added to issue 031.
- **G3. Key tables for lookup, entry and study do not exist.** The spec names
  five screens with tables, and the issues forbid prose changes on the two
  pages that describe them. **Decided by the user, 2026-11-08:** 031 adds the
  three tables, restating only the adjacent prose, and no existing prose
  changes. "Key-table markup" covers new tables.
- **G4. getting-started.md's `uv run` sentence** is new prose on a
  frozen-prose page. The spec requires both. **Decided by the user,
  2026-11-08:** 032 adds the one sentence under Install. There are no other
  prose changes on getting-started.md or study.md.
- **G5. The Pages deploy is missing from the spec's Order,** and 033's link to
  the published guide needs it live. Decision: 035 lands after 030 and before
  033. Being added to the issue files, with the sequence in §3.
- **G6. 036 depends on 028–035,** by its own AC, not only on 029 and 030.
  Being added to issue 036.
- **G7. Examples were not run in CI.** The only CI is the docs workflow, and
  the spec gates publishing on the strict build alone, so a page with a
  failing example could be published from `main`. **Decided by the user,
  2026-11-08:** the workflow runs `uv run --frozen pytest tests/docs` before
  the build in the same job, and the deploy is gated on it as well as on the
  strict build (§13). This goes beyond the spec's wording, which names only
  the strict build as the gate. It lands with 035.
- **G8. Pages prerequisites.** The Pages source must be set to "GitHub
  Actions" once by hand, and a private repository needs a paid plan. It stays
  a manual step, noted in 035 and in `dev/docs/guide.md`.
- **G9. Screens without tables.** Info (`esc`), the end-of-session summary
  (`enter`, hidden `esc`), and the Pick-entry (`esc`) and Note (`esc`, `enter`
  in its input) dialogs are outside the spec's five. **Decided by the user,
  2026-11-08:** they stay out of this sweep. **Follow-up:** key tables for
  them, each a `KEY_SCREENS` entry plus a table (§15.5). The Note dialog's
  keys stay in study.md's prose until then.
- **G10. Readings of the checker's rules.** "Ignoring trailing whitespace"
  includes trailing blank lines. The scratch home prints as `~`. Inline code
  in prose is not an invocation (§5.3).
- **G11. "A scratch learning.db".** No CLI command opens one today. The scratch
  path is guaranteed by the environment, and none is created (§5.5).
- **G12. Personal data the implementer cannot check.** Whether the note
  `to call someone on the phone` and the words in study.md's prose are the
  user's own. study.md's prose is frozen until the content pass, so the user
  says whether anything there must change sooner. The implementer never opens
  the real `learning.db`. **[confirm]**
- **G13. Tatoeba shows `unknown`** in the sample's `info` until phrase mode
  adds Tatoeba samples (§6.2).
- **G14. markdown-it-py in the `dev` group.** The checker imports it, and the
  spec keeps the *docs toolchain* out of `pyproject.toml`. The checker is test
  code run by pytest, so its parser is a test dependency, not docs toolchain
  (MkDocs uses Python-Markdown). It adds no package to the lock. **Decided by
  the user, 2026-11-08:** markdown-it-py goes into the `dev` dependency group
  in 029. mkdocs, material and mkdocs-click stay in `docs/requirements.txt`
  only.
- **G15. Option lists during the sweep.** lookup.md's synopsis is
  `illustration` in 029 and removed in 030, and build.md's synopsis and Flags
  section go in 030.
- **G16. README status notes** ("not yet verified on the phone", "built;
  awaiting confirmation") go to the roadmap, not the guide, which describes
  behaviour.
- **G17. `harald --config`** (the TUI) is not in the generated reference,
  which covers the `harald-cli` group as the spec says.
- **G18. mkdocs-click 0.9.0 with Click 8.5** is unverified. The implementer
  checks it on the first build in 030 (§8).
- **G19. The phone width is not shown in examples.** The spec pins 80, and the
  40-column behaviour stays prose, verified by the TUI and smoke tests.
- **G20. Developer pages' links into the guide** become repo paths (§4.3).
- **G21. Whole-lexicon outputs** (`info` coverage, `Also:`) change when the
  sample grows. That is accepted: pages and sample change in one PR (§7.2).
- **G22. dev/docs/testing.md's "no second fixture" rule** gains the docs
  sample as its one stated exception (§5.9).
