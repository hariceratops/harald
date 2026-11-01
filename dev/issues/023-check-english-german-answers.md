# [feat] Check English → German answers, with the article in the answer

Depends on 010, 013 and 014. Supersedes 011 (article cards). Brief: `dev/inbox/change3-typed-meaning-check.md`, decisions D6–D26 and D37–D40.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- On an English → German card, Enter checks the typed answer. German → English and phrase cards stay self-graded.
- The card shows the sense's gloss, its labels and the part of speech.
- The right word passes, graded Good. ae/oe/ue/ss are accepted for ä/ö/ü/ß, and a verb may be typed with a leading `sich`.
- A noun whose gender is known is typed with its article, and any of the word's genders counts. der, die, das, ein, eine, einen, einem, einer, eines, den, dem and des are recognised as articles in any case. A wrong or missing article passes, graded Hard; if the previous answer on that card also had a wrong article, it is graded Again.
- A noun without gender data, plural-only nouns included, is typed without an article. If one is typed, Harald says none is stored and asks again, without grading.
- An empty answer or any other answer is graded Again. Easy is never given.
- Nouns get no separate article card: the article card type, its FSRS scope, its keypress UI and its tests are removed. `0001_initial.py` is edited in place, and the empty dev `learning.db` is recreated.
- Checking needs `lexicon.db` while studying. Study checks that it is present before the first card and refuses with a message otherwise.
- The checked card fits at 40x30, 40x12 and 100x30 with no vertical scrolling at 40x12 for the test fixtures, and the touch button reads `Check (enter)`.
- Gender comes from the entry the card's own sense came from. A proper noun accepts an article but never penalises its absence or a mismatch.
- The share of English senses that carry labels is measured on the real lexicon and recorded in this issue.
- The docs that mention the article card (README, getting-started, roadmap) are updated.

## Status

Commit step (4) of design 7.14 is built (the earlier steps landed before it); the issue is not closed.

Built in `src/harald/tui/study.py` and `harald.tcss`:
- `meaning_en_de` cards are checked through `AnswerMeaning`; Enter in the field and the `#check` button (`Check (enter)`, in Show answer's place) both run it. German -> English, German -> German and phrase cards stay self-graded.
- The front shows `[labels] gloss`, the part of speech and the example translation; `labels` and `pos` are read leniently, so an older card still renders. The field is `Art. + noun` for a noun with a gender and `Word` otherwise.
- After the check: one verdict line, `you: <answer>`, the expected word from `MeaningGraded.expected`, and the example. Hard and Again use the design's lines, including `Wrong article twice - graded Again`. `NoArticleStored` shows its message in the digraph row, grades nothing and keeps the front, the text and the focus.
- The 300 ms tap guard covers every study button; its clock is `_shown_at`.
- `StudyScreen.on_mount` runs `QueryLexiconInfo` first; on an error it toasts `Checking answers needs lexicon.db: <error>` and pops to Home.
- Measured at 40x12 with the Hund fixture: after the check the card takes 9 of the 10 body rows (design: 9); the first card's front takes 6 card rows plus the field and the digraph row, because of the first-card quirk's two blank lines.

Not built, by design (issue 024): the retry state and cue (`TryAgain`), slip and other-word verdict lines, and the second-try line. `_answer_meaning` asserts `MeaningGraded` because `check_meaning` cannot return `TryAgain` yet.

Unverified by hand: everything on Termux and a real touch screen (the `Check (enter)` tap, the guard's feel, the layout with the soft keyboard up). The pilots cover 40x30, 40x12 and 100x30.
