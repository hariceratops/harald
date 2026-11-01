# Harald v1

Flavor: minimal (single user, who is both operator and consumer).

## Overview

Harald is a personal, offline German vocabulary tool for a B1 learner who
learns from reading, TV and conversation rather than from a course. It has a
Textual TUI for studying and for browsing the dictionary, alongside plain CLI
commands for one-shot lookups and the scriptable desktop build.

It does two jobs. It makes looking things up fast: a German word, an English
word → German, or a phrase as German/English sentence pairs. And it turns
whatever the learner decides to keep into FSRS-scheduled cards.

The dictionary is built on a desktop from Wiktionary (kaikki.org wiktextract)
and Tatoeba data, then pushed one way to a phone. Studying happens on the
phone in Termux, in spare moments. The deck is built entirely from the
learner's own encounters.

Background: `dev/inbox/harald-data-and-modes.md` and
`german_learning_app_design.md`. Where either conflicts with this document,
this document wins. In particular, the brief's "CLI-first, no `textual` in
v1" is reversed here. The brief's rejection of a `Renderer` abstraction
still stands.

## Goals

**Interface**
- The Textual TUI covers studying, dictionary browsing and lookup, and phrase
  search.
- Plain CLI commands remain for:
  - one-shot `lookup`;
  - the desktop `build` (with `--fetch`), which must stay scriptable;
  - `check`.
- Everything, TUI included, works at 40 columns minimum (portrait phone);
  desktop and SSH use 80 or more. That includes conjugation displays.

**Dictionary mode**
- German lookup.
  - Inflected forms resolve to their lemma ("lief" finds laufen).
  - Results are always ranked fuzzily, so typos still find the word.
- English → German lookup.
  - Lists German words grouped by English sense, e.g. *use*: "employ" →
    benutzen/verwenden; "consume" → verbrauchen.
- An entry shows:
  - English glosses per sense, with register tags;
  - German-edition monolingual definitions, as their own block with their
    own sense numbering, not matched to the English-edition senses. When
    (word, pos) has several entries in either edition (e.g. Band: 3
    English-edition entries, 4 German-edition entries), the German
    definitions are grouped once per (word, pos) rather than repeated under
    each English-edition entry, because the two editions can't be reliably
    matched;
  - gender and plural;
  - conjugation and IPA;
  - English-edition examples, translated and listed per sense;
  - German-edition examples in a separate per-word block marked
    untranslated, with no attempt to match them to senses.
- Quotation examples are shown verbatim, typos included.

**Adding a word**
- This applies to every part of speech, nouns and adjectives included.
- The user picks senses from either edition, or both. The two pickers are
  separate because the editions number their senses differently.
- Each chosen English-edition sense yields two meaning cards:
  - German → English, self-graded;
  - English → German, prompted with that sense's gloss and labels. The
    user types the German word and Harald checks it.
- Each chosen German-edition sense yields a German → German card. It shows
  the German definition and the part of speech; the user types the German
  word and Harald checks it. There is no word → definition direction, since
  that would mostly duplicate the German → English card.
- A noun's gender comes from the chosen English-edition entry or, when only
  German-edition senses are chosen, from the German entry.
- Nouns get no separate article card. The article is part of the typed
  answer.
- When picking senses, the user can add a one-line note to a sense: a hint
  or mnemonic of their own, for example "to call someone on the phone". It
  is stored with that sense's cards. On English → German and German →
  English cards it is shown on both sides, so it is visible before
  answering. A note on a German definition is shown on its German → German
  card. Harald warns, but keeps the note, if it contains the word itself.
- A note can only be added when the sense's cards are created. Editing
  notes comes with card editing.
- Stammformen and conjugation cards take no note. Phrase notes are
  unchanged.
- Verbs also get one Stammformen card: 3rd person singular present,
  Präteritum, and Partizip II with its auxiliary.
- On request, per verb, Harald also creates per-(tense, person) cards for
  tenses the user chooses.
- Conjugation answers are typed and checked exactly, except that ae/oe/ue/ss
  are always accepted for ä/ö/ü/ß.
- On English → German and German → German cards, Enter checks the typed
  answer. German → English and phrase cards stay self-graded: Enter shows
  the answer and the user grades it.
- A checked meaning answer is graded as follows:
  - An empty answer is graded Again.
  - The right word passes, graded Good. ae/oe/ue/ss are always accepted for
    ä/ö/ü/ß, and a verb may be typed with a leading `sich`.
  - A noun whose gender is known is typed with its article (`der Hund`).
    Any of the word's genders counts. A wrong or missing article still
    passes, graded Hard; if the previous answer on that card also had a
    wrong article, it is graded Again.
  - A noun without gender data is typed without an article. This includes
    plural-only nouns (`Leute`). If an article is typed, Harald says that
    none is stored and asks again, without grading.
  - A slip that is not itself a German word or word form passes, graded
    Good, and the correct spelling is shown. A slip is one wrong, missing,
    extra or swapped letter in words of 5 to 9 letters, and up to two in
    longer words. Words of up to 4 letters allow none.
  - Wrong capitalisation alone counts as such a slip, unless the other-case
    form is itself a German word (essen and Essen, arm and Arm, laut and
    Laut); then it is graded Again.
  - If the answer is another German word of the same part of speech, Harald
    shows the first letter and the length of the expected word and allows
    one more try. A right answer on that try passes, graded Hard. Anything
    else is graded Again.
  - Any other answer is graded Again.
- Checked meaning answers are graded Again, Hard or Good. Hard comes only
  from the article and from the second try. Easy is never given.
- Checking needs `lexicon.db` while studying, to tell a slip from another
  real word.
- Checked grading applies from the first review. After 200 checked reviews
  or two weeks, the checked answers are audited against the user's own
  judgement. If more than 5% were failed wrongly, a way to claim a right
  answer is reconsidered.
- Per-(tense, person) cards: the user picks tenses per verb, and each
  picked tense makes one card per person: ich, du, er/sie/es, wir, ihr and
  sie/Sie. The formal Sie is not a separate person, because sie/Sie shares
  the 3rd person plural form. There are 14 tenses: the indicative Präsens,
  Präteritum, Perfekt, Plusquamperfekt, Futur I and Futur II; Konjunktiv I
  in the present, Perfekt, Futur I and Futur II; and Konjunktiv II in the
  preterite, Plusquamperfekt, Futur I and Futur II. There is no imperative.
  The card shows `infinitive - hint`, the tense and one person. The user
  types the form without the pronoun, and any form the data lists for that
  slot is accepted.
- Separable verbs use the form the language uses: split in simple tenses
  (`rufe an`) and joined in compound tenses (`habe angerufen`). Stammformen
  cards use the same forms (`ruft an`, `rief an`, `hat angerufen`). Neither
  card type shows a "trennbar" badge or hint, because knowing that the verb
  is separable is part of what the user must recall. Typing the form
  without the prefix counts as wrong.
- If the data lacks a form for a (tense, person), only that card is
  refused, and the confirm step names it (for example `Präsens (ich, du,
  wir, ihr)`). The other cards are still created.
- If the forms a card type needs are missing from the data, Harald refuses
  that card type and says which forms are missing.

**Phrase mode**
- Two-way search of Tatoeba German/English sentence pairs, with input in
  either language.
- Matching must find the construction even when the exact wording misses.
  For example, "repeats itself" must find "Geschichte wiederholt sich."
- A found pair can be saved.
- When search misses, the user writes a pair in `$EDITOR` from a template
  with English, German and an optional note, as `git commit` does.
  - In the TUI, the app suspends while the editor runs.
  - Saving the template empty or unchanged cancels.
  - Saving it with one side missing reopens the editor with the error at the
    top and the user's text kept.
- Phrase cards are English → German production, self-graded.

**Study and card management**
- By default study covers everything that is due; a deck filter narrows it.
- Sibling cards (from the same word or phrase, and of the same card type)
  are buried for the day.
- There is a configurable daily cap on new cards.
- Each session ends with a short summary: how many cards were reviewed and
  how many were answered correctly.
- Decks are for organisation only. An item can be in several decks, and the
  scheduler ignores decks.
- Cards can be edited, suspended (reversible) and deleted.
  - Delete removes a card from study and from every listing, but its review
    history is kept.
- There is no undo of the last grade.

**Scheduling**
- FSRS through the `fsrs` PyPI package, with default parameters.
- Parameters are scoped per card type: meaning, conjugation, phrase.
  - German → German cards count as meaning cards, like German → English and
    English → German. One scope for all meaning-recall directions keeps the
    split consistent, and leaves each scope with more reviews to optimise
    from later. Splitting them out would be a one-line change if
    optimisation later suggests it.
- The full review log is kept, so the parameters can be optimised later.

**Data build (desktop)**
- Builds `lexicon.db` from locally kept source files.
- Downloads new sources only on explicit request (`--fetch`). The most recent
  download is kept.
- Records the source dates it was built from.
- Harald displays the sources, their dates and their attribution:
  - Wiktionary: CC BY-SA 4.0;
  - Tatoeba: CC-BY.
- Reports how complete the data is, for information only:
  - verbs with complete Stammformen;
  - nouns with a gender;
  - senses with a translated example.
- Records the tag sets the importer could not map.
- The built database is never redistributed.

**Testable criteria**
- `lookup lief` shows laufen, including läuft / lief / ist gelaufen. All
  lookup output, CLI and TUI, fits the terminal width down to 40 columns.
- Rebuilding twice from the same local files leaves the existing
  `lexicon.db` byte-for-byte untouched, so Syncthing has nothing to resend.
- Suppose an entry that cards were built from disappears or splits in a
  rebuild. Those cards still study correctly from their own content, and
  `harald check` lists them.
- Killing the process mid-session loses at most the card on screen. Every
  earlier grade persists.
- On the phone, in Termux, the TUI suspends for `$EDITOR`, reopens
  afterwards, and saves the phrase.

## Non-Goals

- No GUI, web app or audio.
- No two-way sync and no studying on more than one device.
- No offline machine translation. When search misses, the learner supplies
  the German.
- No built-in curated decks.
- No Anki import/export.
- No cloze cards.
- No noun-declension tables, no adjective-declension drills and no
  comparative/superlative drills. Nouns and adjectives get meaning cards
  like any word.
- No typed checking of German → English or phrase answers. They have too
  many right answers.
- No linking between phrases and words. A word lookup does not show saved
  phrases that contain it.
- No matching of German-edition examples or definitions to English-edition
  senses.
- No seed CSV of irregular verbs.
- No SM-2, no Scheduler abstraction of Harald's own, no per-deck FSRS
  parameters.
- No `Renderer` abstraction over the UI. The Rust rewrite would redo the UI
  anyway.
- Not in v1:
  - an FSRS parameter-optimisation command;
  - a `stats` command;
  - leech flagging;
  - undo of the last grade.
- No Rust rewrite in v1. The name Harald is free on PyPI and crates.io for
  when it comes.
- No hand-written Wikitext parser. Running or forking wiktextract comes
  first, and a parser of our own is the last fallback.

## Technical Approach

**Stack.**
- Python 3.12+, packaged with uv.
- Textual for the TUI, plus plain CLI subcommands.
- Third-party packages are fine if they are good quality and maintained
  (e.g. `fsrs`, `textual`, a fuzzy matcher, a stemmer).
- Storage is SQLite.

**Two databases, two machines.**
- `lexicon.db`
  - Read-only at runtime.
  - Built on the desktop.
  - Pushed one way to the phone by Syncthing, which is send-only on the
    desktop.
  - A rebuild replaces it and never touches `learning.db`.
  - About 1 GB is acceptable.
- `learning.db`
  - Holds decks, cards, phrases and the review log.
  - Lives on the phone, which is its only writer.
  - Is never synced two ways.
  - A consistent copy goes one way from the phone to the desktop as a
    backup, and is never read back automatically.

**Sources.**
- English edition: `raw-wiktextract-data.jsonl.gz` (2.8 GB gz), streamed.
  The build keeps two things from it:
  - all `lang_code == "de"` entries;
  - from `lang_code == "en"` entries, the German translations grouped by
    sense. English → German lookup depends on these.
- German edition: `de-extract.jsonl.gz`. It supplies:
  - monolingual definitions (glosses) with its own sense numbering;
  - extra untranslated examples.
  Both are related to English-edition words by (word, pos), never per sense.
- Tatoeba German/English sentence pairs.

The deprecated postprocessed per-language files
(`kaikki.org-dictionary-German.jsonl` and the like) must not be used
(wiktextract issue #1178).

**The importer is the only module that knows where the data came from.** It
maps the flat `forms` list of `{form, tags[]}` and drops the bookkeeping
rows. It finds gender in sense tags or the head template.

**Rebuild guarantees.** These are requirements; how to meet them is the
architect's decision.
- A build is deterministic. A rebuild with nothing new leaves the existing
  file untouched.
- An interrupted build (Ctrl-C, crash, disk full) leaves the previous
  `lexicon.db` intact, and a partial file never reaches the phone.
- If the Harald version and the schema of `lexicon.db` don't match,
  Harald refuses to start and names both versions.

**No stable upstream identity.** kaikki has no stable entry ids or sense ids,
in either edition. (lemma, pos) is not unique: Bank, Band, See, Leiter,
umfahren and übersetzen all have more than one entry. Positional numbering
(`etymology_number`, `sense_index`) shifts when Wiktionary is edited. So:
- A rebuild never loses or corrupts cards or review history.
- Each card keeps its own copy of what it teaches: lemma, gender, the chosen
  gloss or German definition, and the forms. Each saved Tatoeba pair keeps
  its own copy too. Both stay studyable whatever happens upstream.
- The link from a card to `lexicon.db` is re-resolved after a rebuild.
  - One input to consider is a hint key of (lemma, pos, discriminator), where
    the discriminator is gender plus plural for nouns and the participle for
    verbs.
- Cards whose entry changed, disappeared or became ambiguous are surfaced
  only by a user-run command, `harald check`. There the user repairs or
  adapts them locally. Nothing is shown automatically at startup.
  - A matched card keeps its own copy until the user repairs it. Upstream
    content is never taken over silently.

**Durability.** Each grade is stored as soon as it is given. Android may kill
Termux at any time.

**Early risks.** Verify these on the phone before building on them; they
are not assumptions.
- Textual suspending for `$EDITOR` and resuming cleanly inside Termux.
- Textual's startup time and rendering at 40 columns (portrait) in
  Termux. One-shot `lookup` from the shell stays available partly for speed.

## Open Questions

1. **Plain-file export/import of the user's own deck.** It would be an escape
   route beyond the one-way backup, but the user hasn't accepted or rejected
   it. It is not in the requirements.
2. **Does kaikki keep older dated dumps?** If it doesn't, the locally kept
   copy is the only way to pin a version. Either way, design for the local
   copy.
3. **How complete is the data?** The first build's report will tell us
   (Stammformen, gender, translated examples). The result is informational
   and does not gate the design. If coverage turns out poor, scope may need
   revisiting.
4. ~~`harald check` repair actions.~~ Resolved: `check` is in the CLI and
   the TUI, with three repair actions (relink, accept upstream, keep own
   copy); see design §8.
5. ~~Per-(tense, person) cards.~~ Resolved; see the requirements on
   per-(tense, person) cards and separable verbs above.
6. ~~Backup details.~~ Resolved: after each session and on exit, plus
   `harald backup`, keeping 10 copies; see design §10.
7. ~~Defaults.~~ Resolved: the daily cap on new cards is 20. Fuzzy ranking
   applies to German lookup and to English → German lookup, not to phrase
   search.
