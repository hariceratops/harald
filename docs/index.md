# Harald

A personal, offline German vocabulary tool for a learner who picks German up
from reading, TV and conversation. It does two jobs:

- **Look things up fast** — a German word, an English word → German, and
  (planned) a phrase as German/English sentence pairs.
- **Turn what is worth keeping into spaced-repetition cards** (planned).

## How this guide is organised

**User guide**

- **[Getting started](user/getting-started.md)** — install, build the lexicon,
  first lookup.
- **[Lookup](user/lookup.md)** — what `harald lookup` shows and how it matches.
- **[Building the lexicon](user/build.md)** — sources, fetching, determinism.
- **[Configuration](user/configuration.md)** — `config.toml` and file locations.
- **[Data and licences](user/data.md)** — where the data comes from and what you
  may do with it.
- **[Roadmap](roadmap.md)** — what works and what is next.

**Developer guide**

- **[Architecture](developer/architecture.md)** — layers, packages, error
  handling.
- **[Testing](developer/testing.md)** — test layers, fixtures, commands.
- **[Build internals](developer/build-internals.md)** — the task graph,
  determinism, schema versions.
- **[Workflow](developer/workflow.md)** — `dev/`, conventions, adding a
  command.

## Two databases

| File | Holds | Written by |
|---|---|---|
| `lexicon.db` | the dictionary: entries, translations, search keys | `harald build`; read-only otherwise |
| `learning.db` | cards, decks, review log (planned) | the study device only |

A rebuild replaces `lexicon.db` and never touches `learning.db`. The lexicon is
pushed one way from desktop to phone with Syncthing.

## Terminal width

Output adapts to the terminal: 40 columns minimum (a phone in portrait), 80 or
more on desktop and SSH.
