# [feat] Forgive slips and offer one retry on a different word

Depends on 023. Brief: `dev/inbox/change3-typed-meaning-check.md`, decisions D22–D24.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- A slip that is not itself a German word or word form passes, graded Good, and the correct spelling is shown.
- A slip is one wrong, missing, extra or swapped letter in words of 5 to 9 letters, and up to two in longer words. Words of up to 4 letters allow none.
- Wrong capitalisation alone is such a slip, unless the other-case form is itself a German word (essen and Essen, arm and Arm, laut and Laut); then it is graded Again.
- The known-word test is one exact folded-key query against `lexicon.db`, returning the lemma, part of speech and kind.
- If the answer is another German word of the same part of speech, Harald shows the first letter and the length of the expected word and allows one more try. A right answer on that try is graded Hard. Anything else is graded Again.
- The retry state lives on screen only. A kill during a retry loses nothing that was graded.
- The retry and the shown spelling fit at 40x30, 40x12 and 100x30, with no vertical scrolling at 40x12.
- The lexicon measurements the brief names (F4: the guard's hit rate) are recorded in this issue.

## Measurements

F4, the known-word guard's hit rate, on the real `lexicon.db` (2026-11-02, read-only; 225,720 headwords, 1,121,453 German keys). Sample: 200 random single-word alphabetic lemmas of 5 to 9 letters (seed 24, from 67,245), and every 1-edit neighbour of each (deletion, substitution over a-z and äöüß, insertion, adjacent swap): 94,650 neighbours.
- 888 (0.94%) fold to a known German key, so a random one-letter typo is itself a word about once in 107.
- 601 (0.63%) reach a lemma other than the card's own; the rest are forms of the card's word or its own folded spelling.
- 57% of the sampled lemmas have at least one such neighbour. The guard decides rarely per typo, but a common word almost always has some neighbour it can catch.

## Status

Steps 1-2 (`known_words`, `check_meaning` rules 4-9 with `AnswerMeaning` and the lexicon) were committed earlier. Step 3, the retry in the study screen, is built in `src/harald/tui/study.py` and covered by pilots at 40x30, 40x12 and 100x30, a resize-during-retry pilot, and a smoke flow with a retry. Every criterion is met in tests; the Termux checks are open (below).

Built:
- `TryAgain` sets `_first_try` and `_retry` (screen state only; `_next()` resets both, Esc leaves the card ungraded). The field is cleared and keeps focus, and nothing is graded or written. The cue is computed in `_show` from the screen width, so a resize keeps it: `Another noun. Try: H _ _ _`, or `Another noun. Try: A... (22 letters)` when the blanks do not fit (width minus 2).
- `_meaning_verdict` now has the design's lines: `RIGHT, typo - graded Good`, `RIGHT, typo and article - graded Hard`, `RIGHT on the second try - graded Hard`, `WRONG, capitalisation - graded Again`. The old placeholder cue `H... (4)` is gone.
- The retry reuses Check/Enter and the 300 ms tap guard (the clock restarts on the retry).
- Measured at 40x12 with the Hund fixture: the retry takes 6 card rows (heading, gloss, part of speech, example, field, cue) of the 10 body rows, and the verdict after a second try takes 9, with no vertical scrolling.

Not in the design, chosen here:
- A `NoArticleStored` refusal on the second try replaces the cue with its message and drops the cue; the first try is kept.
- A second-try verdict follows the table's order, so a second try that passes with a wrong article reads `RIGHT on the second try - graded Hard`.

Unverified by hand in Termux: the retry cue and its wrap behaviour on a real phone with the soft keyboard up, the double-tap on Next landing on Check (enter), and that the slip's corrected spelling reads clearly under `you:`.
