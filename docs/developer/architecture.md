# Architecture

## Layers

```text
cli.py, tui/                 front-ends (harald-cli, harald)
  └─ use_cases/              one class per action, with execute()
       └─ lexicon/, learning/, build/
            └─ infrastructure/, db/, core/
```

Front-ends call only use cases. Only the per-database packages touch a
session, a connection or a file.

## Packages

| Package | Role |
|---|---|
| `harald.cli` | click commands; exit codes |
| `harald.tui` | Textual app: home, lookup, entry and info screens |
| `harald.render` | width-adaptive rendering with rich |
| `harald.use_cases` | `BuildLexicon`, `QueryLexiconInfo`, `LookUpGerman`, `LookUpEnglish` |
| `harald.lexicon` | schema, models, lookup, fuzzy matching over `lexicon.db` |
| `harald.build` | the importer: sources, fetch, parsers, task graph, writer, publish |
| `harald.core` | `Result` and `Option` |
| `harald.db` | connections |

## Errors: `Result` and `Option`

Failures that carry a reason return `Result`; a "no value" that is an expected
outcome (a lookup that finds nothing, a parser skipping a line) returns
`Option`. Fields that map to nullable columns stay `X | None`, converted at the
boundary. Broad `except Exception` is allowed only at a few named seams where
arbitrary failure is converted to an `Err` and partial state is rolled back or
deleted; everywhere else explicit types are caught.

## The importer is the only module that knows the data's origin

It maps wiktextract's flat `forms` list of `{form, tags[]}`, drops
bookkeeping rows and finds gender in sense tags or the head template. The rest
of Harald reads Harald's own schema.

## No stable upstream identity

kaikki has no stable entry or sense ids, and (lemma, pos) is not unique (Bank,
Band, See, Leiter). So a card will keep its own copy of what it teaches, and
its link to the lexicon is re-resolved after a rebuild. `harald-cli check`
(planned) will surface cards whose entry changed.

## Further reading

See also [Testing](testing.md), [Build internals](build-internals.md) and
[Workflow](workflow.md).

The authoritative spec and design are `dev/specs/harald-v1.md` and
`dev/design/harald-v1.md` in the repository.
