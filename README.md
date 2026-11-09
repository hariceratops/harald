# Harald

A personal, offline German vocabulary tool for a learner who picks German up
from reading, TV and conversation rather than a course. Look a word up fast,
keep what is worth keeping as a spaced-repetition card.

<!-- The demo tape mirrors this block; keep them the same. -->
```console
$ harald-cli lookup lief
lief → laufen (verb)
laufen  verb
läuft / lief / ist gelaufen
1. to walk; to jog; to run
          Präsens Präteritum Perfekt
ich       laufe   lief       bin gelaufen
du        läufst  liefst     bist gelaufen
er/sie/es läuft   lief       ist gelaufen
wir       laufen  liefen     sind gelaufen
ihr       lauft   lieft      seid gelaufen
sie/Sie   laufen  liefen     sind gelaufen
Imperativ: lauf, laufe! / lauft!
$ harald-cli lookup --en use
use (verb)
  employ, apply
    benutzen
    verwenden
  to exhaust the supply of, to consume
    verbrauchen
  to exploit
    ausnutzen
    zum Vorwand nehmen  (use as a pretext)
use (noun)
  act of using
    die Benutzung
    der Gebrauch
  die Anwendung
```

## Guide

Read the guide at <https://hariceratops.github.io/harald/>. It covers
installing, building the lexicon, lookup, cards and study, and the command
reference.

To read it locally, with a live-reloading site on <http://127.0.0.1:8000>:

```sh
uv run --with-requirements docs/requirements.txt mkdocs serve -f docs/mkdocs.yml
```

## Roadmap

- [ ] Study on the phone: the TUI and the typed checks verified in Termux
      (built; the phone checks are outstanding)
- [ ] Typed checking of meaning answers, and notes on senses (built; awaiting
      confirmation), then an audit of the checked answers after 200 reviews
      or two weeks
- [ ] New-card cap and sibling burying; editing a card's note;
      `harald-cli check` after a rebuild, keeping notes and labels
- [ ] Phrase mode: Tatoeba phrase search, saving a pair as a card, and writing
      your own pair when a search misses
- [ ] `harald-cli backup --to PATH`, the one way a copy of `learning.db`
      leaves the device
- [ ] Decks as an import/export format
- [ ] Rust rewrite of hot paths (later)

## Licence and data

The code is licensed under the Apache License 2.0 (see [`LICENSE`](LICENSE)).
Dictionary data comes from Wiktionary
(CC BY-SA 4.0, via wiktextract/kaikki.org) and Tatoeba (CC BY 2.0 FR). The
built `lexicon.db` is never redistributed. See
[Data and licences](docs/user/data.md).
