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
