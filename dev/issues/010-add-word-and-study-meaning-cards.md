# [feat] Add a word and study its meaning cards

The first full learning loop: pick senses, create cards in `learning.db`, study them with FSRS. Depends on 009.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- From a lookup, the user picks English-edition senses of any part of speech. Each picked sense yields a German → English and an English → German meaning card.
- Each card stores its own copy of what it teaches (lemma, gender, chosen gloss) in `learning.db`, independent of `lexicon.db` row ids.
- The TUI study screen shows due cards and accepts a 1–4 self-grade. Scheduling uses the `fsrs` package with default parameters scoped per card type.
- Every review is appended to the review log. Each grade is stored immediately: killing the process mid-session loses at most the card on screen.
- The session ends with a summary of cards reviewed and answered correctly.
- `learning.db` is created and upgraded through Alembic, with a backup written before any upgrade.

## Status

Built in two stages. All criteria are met except hands-on use: the 9-column
grade buttons, the 300 ms tap guard and taps-as-clicks still need a run in
Termux. Departures from the design are in design §7.9. Open for later
slices: a use case returning the "has cards" marks in one call, due/new
counts for the study header and Home, and a preflight for `learning.db`.
