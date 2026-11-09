# Checked guide

Every `console` fence in `docs/**/*.md` and `README.md` is run by the test
suite. A renamed command or changed output fails the build instead of waiting
for someone to read the page.

## Where things are

| Path | What it is |
|---|---|
| `tests/docs/checker.py` | parser, invocation lint and runner. Its module docstring is the syntax reference for page authors. |
| `tests/docs/sample.py` | builds the sample home with the real `harald-cli build`; `python -m tests.docs.sample DIR` builds it by hand |
| `tests/docs/test_docs_examples.py` | one test per example, a well-formedness test and the checker's own tests |
| `tests/docs/test_key_tables.py` | one test per key table, checked against its screen's bindings |
| `docs/examples/` | the hand-cut sample sources, kept out of the published site |

Run only these tests with

```sh
uv run pytest tests/docs
```

and one page with `-k lookup`. A test id is `page:line` of the opening fence.

## Reading a failure

A failing example prints `page:line: command printed something else`, then a
unified diff of the page against the actual output. Fix the page when the
change is intended, the code when it is not. A malformed page is reported by
`test_docs_pages_are_well_formed`, which lists every problem at once with the
fix.

## Key tables

A table headed `Key | Does` names its screen on the line above it:

```markdown
<!-- docs: keys add-word -->
| Key | Does |
|---|---|
| `space` | tick or untick a row |
```

The screen is one of `home`, `lookup`, `entry`, `add-word`, `study`, each named
by exactly one table. Write each key in backticks; `esc` and `/` match
Textual's `escape` and `slash`. Two things fail the test: a row whose key the
screen does not handle, and a visible (`show=True`) binding of the screen or
the app that has no row. Hidden bindings may be listed and need not be.

Some keys belong to a widget, not to the screen's `BINDINGS`: `enter` submits
an `Input` and selects in an `OptionList`, `space` ticks a `SelectionList`
row. `KEY_SCREENS` in `tests/docs/checker.py` declares those widgets per
screen, and the test requires each to be built in the screen's `compose()`.
A new screen, or a new widget whose keys a table lists, is an edit there.

The Info screen, the end-of-session summary and the two pop-up dialogs have no
table yet; that is a recorded follow-up.

## The sample

The sample is separate from `tests/fixtures/` on purpose: several outputs
(`info`'s coverage lines, `build`'s counts, the `Also:` line of a fuzzy
lookup) depend on the whole lexicon, and the test fixture changes for test
reasons. To show a new word, add its wiktextract line to
`docs/examples/en-edition.jsonl` (or `de-edition.jsonl`) in the same change as
the page. Adding a word can change `info` and `Also:` lines on other pages;
the checker names the ones that moved.

Use dictionary words chosen for the page, never words from a real deck.

## Pinned environment

Each example runs in a scratch copy of the sample home, offline, at 80
columns. Source dates read 2026-11-01 because the sample writes each source's
`.meta.json` sidecar with that date, and build timings read 0.0 s because
`harald.build.run` and `harald.build.graph` see a frozen clock. A new
clock read in a CLI command shows up as a failing example; extend the pin in
`tests/docs/checker.py`.
