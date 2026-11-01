# [feat] Add a note to a sense when adding a word

Depends on 023 and 025, so the checked faces exist. Brief: `dev/inbox/change3-typed-meaning-check.md`, decisions D27–D36 and D41–D44.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- On an English or German sense picker row, `h` opens a one-line note box. Enter stores the note, the row shows `+ note`, and the row is ticked.
- The box reads `Shown before you answer, both sides`. When the note contains the word itself, it reads `Contains the word - Enter keeps it`. That is the only warning, and it never refuses the note.
- A note is capped to one row, about 36 characters.
- Rows that already have cards (`has cards`) refuse a note. Notes can only be added when a sense's cards are created.
- Both cards of an English sense (German → English and English → German) carry the note, and so does a German → German card.
- The note shows on both sides of those cards, under the part of speech and above the German example, and stays visible through the reveal, the check and the retry.
- Cards without a note look as they did before. Stammformen and conjugation cards take no note, and phrase notes are unchanged.
- Duplicate detection ignores `note`.
- The picker footer shows `h Note` when it fits at 40 columns, and falls back to dropping `esc Cancel` if it does not.
- At 40x12 the German → English front fits with a three-row example. The after-reveal screen is measured with and without a note, at a short and a three-row example, and the overflow in rows is recorded here. About a row of scrolling is accepted; the front's example is dropped under `-short` only if the measurement shows worse (P64).
- Pilot tests cover the list in the brief's D44, at 40x12, 40x30 and 100x30.
- The note box with the soft keyboard up and taps on `h Note` are added to issue 009's Termux checklist.
