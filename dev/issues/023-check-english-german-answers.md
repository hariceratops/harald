# [feat] Check English → German answers, with the article in the answer

Depends on 010, 013 and 014. Supersedes 011 (article cards). Brief: `dev/inbox/change3-typed-meaning-check.md`, decisions D6–D26 and D37–D40.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- On an English → German card, Enter checks the typed answer. German → English and phrase cards stay self-graded.
- The card shows the sense's gloss, its labels and the part of speech.
- The right word passes, graded Good. ae/oe/ue/ss are accepted for ä/ö/ü/ß, and a verb may be typed with a leading `sich`.
- A noun whose gender is known is typed with its article, and any of the word's genders counts. A wrong or missing article passes, graded Hard; if the previous answer on that card also had a wrong article, it is graded Again.
- A noun without gender data, plural-only nouns included, is typed without an article. If one is typed, Harald says none is stored and asks again, without grading.
- An empty answer or any other answer is graded Again. Easy is never given.
- Nouns get no separate article card: the article card type, its FSRS scope, its keypress UI and its tests are removed. `0001_initial.py` is edited in place, and the empty dev `learning.db` is recreated.
- Checking needs `lexicon.db` while studying. Study checks that it is present before the first card and refuses with a message otherwise.
- The checked card fits at 40x30, 40x12 and 100x30 with no vertical scrolling at 40x12, and the touch button reads `Check (enter)`.
- The docs that mention the article card (README, getting-started, roadmap) are updated.
