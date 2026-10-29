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
