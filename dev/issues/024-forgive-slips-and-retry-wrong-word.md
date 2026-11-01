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
