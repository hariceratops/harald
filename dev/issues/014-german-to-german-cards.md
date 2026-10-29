# [feat] German → German cards

Depends on 007 and 010.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- When adding a word, a separate picker offers German-edition senses.
- Each picked German-edition sense yields a self-graded card that shows the German definition and asks for the German word. The learner types an attempt before the answer is revealed; it is stored with the review, and an empty attempt is graded Again.
- These cards share the meaning-card FSRS parameter scope.

## Status 2026-10-29
Built. The picker and card creation came with 010; this slice turned the
card face round (definition on the front, article and lemma on the back)
and tests it at 40x30, 40x12 and 100x30. Awaiting the user's hand check.

## Review 2026-10-29 (range e63293d..HEAD, covers 010, 014, 019)
- c2e122a bundled the study code, the user docs and a ~400-line design
  rewrite in one commit, and its body does not mention the design. Not
  rewritten; later slices should commit the design on its own.
- The commit skill names `Claude Opus 5` in the trailer; the session's
  attribution reminder asked for `Claude Sonnet 5.5`, which all five commits
  carry. The skill text and the trailer disagree; the user decides which.
- c2e122a, a15839d and 13fc268 have no `Refs` trailer; 28818ff's subject
  does not mention the README roadmap it also edits.
- Design §7.13 and §16 still said the 40x12 fold was open, asked for the
  `assert_inside` height check, and said 014 had to turn the card round.
  13fc268 and 7bbf142 did all three; 13fc268 dropped blank lines under
  `-short` rather than merging heading, word and part of speech. Design
  lines updated.
- Design §7.13's "Relayed by the main session ... already implemented" is
  process, not design. Reworded.
- `StudyScreen.action_reveal` sets `_revealed = True` before grading an
  empty attempt; if the write fails, `_grade` notifies without redrawing,
  so the card reads as revealed while the front is still shown. Enter
  retries. Open.
- `StudyScreen.BINDINGS` binds keys 1, 2 and 3 while the grade buttons are
  Again/Good only; key 3 serves article cards. Open.
- 019's typed-attempt criterion is wording only until 019 is built.

## Review 2026-10-29 (range 28818ff..6366971, follow-ups)
- Two bullets of "Review 2026-10-29 (range e63293d..HEAD)" are fixed, not
  open: `action_reveal` now undoes `_revealed` when the Again grade is not
  saved, and the key 3 binding has a comment saying why (both 33a881d).
- Trailer decision: commits carry the authoring model, `Claude Sonnet 5.5`,
  not the commit skill's `Claude Opus 5` (user's decision, 2026-10-29).
- Commits ab72617, f37c637, 3ba29f9, 3b117be, 68881a8 and 6366971 have no
  `Refs` trailer, and 33a881d also holds the key 3 comment, which is not
  part of the failed-write fix. Not rewritten.
- The conjugation wireframe line added in 6366971 read "ae/oe/ue/ss
  accepted for"; the card says "are accepted for". Reworded.
- Two lines in the guide and in design §7.13 ran past the wrapping used
  around them. Reflowed.
