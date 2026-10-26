# Workflow

The repository carries its own spec, design and work breakdown under `dev/`.

| Path | Holds |
|---|---|
| `dev/specs/` | the frozen spec (`harald-v1.md`); revised only by moving it out first |
| `dev/inbox/` | unfrozen briefs and drafts |
| `dev/design/` | the design and the reasoning behind it |
| `dev/issues/` | one file per vertical slice, with acceptance criteria |

Where the brief and the spec disagree, the spec wins; where the spec and
the code disagree on a name, `AGENTS.md` wins (`lexicon.db`, `learning.db`).

## Conventions

- One vertical slice per commit, with its docs; the issue file is cited in a
  `Refs` trailer.
- Commit subjects are imperative, capitalised, at most 60 characters.
- Comments explain why, never what.
- A function whose "no value" is an expected outcome returns `Option`;
  failures with a reason return `Result`. See [Architecture](architecture.md).

## Adding a command

1. Write a use case class in `use_cases/` with an `execute()` returning a
   `Result`.
2. Add a click command in `cli.py` (the `harald-cli` entry point; the TUI is the separate `harald` entry point in `tui/main.py`) that loads the config, calls the use case
   and maps errors to exit codes (1 failed, 2 refused).
3. Render with `render.py`, which must fit 40 columns.
4. Add a smoke test and update the [user docs](../user/getting-started.md)
   and the [roadmap](../roadmap.md).
