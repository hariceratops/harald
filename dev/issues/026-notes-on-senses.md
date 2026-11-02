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

## Status

Steps 1 (content and dedupe), 2 (`h` and the note box) and 3 (the card faces on the study screen, D42's measurement) are built.

Step 2, in `src/harald/tui/addword.py`:
- `NoteScreen`, a `ModalScreen[str | None]` like `PickEntryScreen`: a bordered `Input(max_length=36)` titled `Note for this sense`, with `Shown before you answer, both sides` below it. When the note contains the lemma as a whole word (folded, case-insensitive) the line reads `Contains the word - Enter keeps it`. It never refuses. Enter dismisses with the stripped text (empty clears), Esc with `None`.
- `h` on the English and German steps opens it for the highlighted row. Enter stores the note, ticks the row and shows `  + note` after the label; the highlight stays on the row. A `(has cards)` row toasts `This sense has cards - notes come with card editing` and opens nothing. A German heading or gloss-only row ignores `h`. Notes are passed to `PlanWordCards` on the confirm screen and on create; an unticked row keeps its note but the plan ignores it.
- Footer on the picker steps: `n Next  h Note  b Back  esc Cancel`, measured at 31 cells (design estimate: 34), so the fallback of dropping `esc Cancel` is not needed. `h Note` is absent on the tense and confirm steps.
- Pilots at 40x30, 40x12 and 100x30 in `tests/tui/test_add_word.py` cover both pickers, the marker, ticking, Enter, Esc and empty Enter, the wording both ways, the warning keeping the note, the 36-character cap, the refusal, the footer, and the stored card content.

Step 3, in `src/harald/tui/study.py`: `_note_line` adds the card's `note` as one dim row `(note)` after the part of speech and before the example, on German -> English, English -> German and German -> German fronts. The front stays on screen through the reveal, check, retry and verdict, so the note shows on both sides. A note wider than the body (`size.width - 2`, 38 at 40 columns, so a 36-character note fits whole) is cut with `...`. Cards without a note, Stammformen, conjugation and phrase cards render as before. Pilots in `tests/tui/test_study_screen.py` at 40x30, 40x12 and 100x30.

D42's measurement, `test_note_on_german_english_after_reveal_at_40x12` (German -> English after the reveal at 40x12; body is 10 rows; rows used = sum of the displayed children's heights in `#body`; overflow = rows used - 10, equal to `max_scroll_y`; it does not use `assert_inside`, which fails on scrolling):

| Example | Without a note | With a note |
|---|---|---|
| short (the fixture's one row) | 8 rows, overflow 0 | 9 rows, overflow 0 |
| three rows | 12 rows, overflow 2 (`max_scroll_y` 2) | 13 rows, overflow 3 (`max_scroll_y` 3) |

The note adds exactly one row in both. P64: the numbers favour the reading that "about a row" is what the note adds, not the screen's total overflow: a long example already scrolls 2 rows without a note, so the note is not the cause of the scrolling. The front's example is therefore not dropped under `-short`; with a short example nothing scrolls at all. (The three-row front with a note fits 40x12 without scrolling.)

Not verified by hand in Termux: the note box with the soft keyboard up, and taps on `h Note` in the footer (to go on issue 009's checklist).
