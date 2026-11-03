# [feat] Check German → German answers

Depends on 023 and 014. Brief: `dev/inbox/change3-typed-meaning-check.md`, decisions D17–D24, D37 and D20.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- On a German → German card, Enter checks the typed answer with the same rules as 023, and with 024's slip and retry rules once that has landed.
- The card shows the German definition and the part of speech; the card stores the sense's labels.
- Gender comes from the entry the card's own sense came from: a German definition takes the German entry's gender, even when English senses of a homograph are picked in the same add.
- A German → German card created before this change keeps studying: it reads as having no stored labels and still works.
- The checked card fits at 40x30, 40x12 and 100x30, with no vertical scrolling at 40x12 for the test fixtures.
- Before this issue is built, the brief's measurement of German definitions that contain their own lemma (F4) is recorded here.

## Measurement (F4, P19), 2026-11-02

Real `lexicon.db` (read-only): of 242,678 German-edition senses that can be picked (those with a `sense_index`), 3,035 (1.25%) contain their own lemma as a whole word, case-insensitively, in 2,565 headwords. By part of speech: nouns 1.0% (1,537 of 150,941), verbs 1.0%, adjectives 1.1%, proper nouns 3.2% (682 of 21,373), phrases 0.8%. This is a lower bound: inflected forms of the lemma (`Mauern` for `Mauer`) and compound family members are not counted.

Examples (lemma: definition):
- Mauer: `Hindernis, das in seiner Gestaltung einer Mauer nachempfunden wurde`
- Chardonnay: `Wein, der aus Trauben der Rebsorte Chardonnay ([1]) hergestellt wurde`
- Zittergras: `speziell das heimische gewöhnliche Zittergras (Briza media)`
- Schilling: `eine Münze mit dem Wert 1 Schilling. Schillinge`

What it implies: about one definition in 80 gives its answer away, and it is concentrated in proper nouns. That is rare enough that the design asks for no masking, so none is added. Revisit only if the Termux trial shows the cards are common in what the learner actually adds.

## Status

Built (content, then the study screen). Every criterion is met in component, pilot and smoke tests; the Termux checks are open.

- `learning/content.py`: `meaning_de_de` content gains `labels`, and its `gender` comes from the card's own German entry label (`das Band` -> `n`, `der/das Liter` -> `mn`, a bare lemma or a label with an unknown article -> `""`), via `_german_entry_gender`. English senses still take the chosen English entry's gender. A card made before this has no `labels` key; nothing reads the key, so it still studies and checks.
- `tui/study.py`: `meaning_de_de` joins `_CHECKED_MEANING`. The front shows the definition and the part of speech (no labels: the design stores them but does not show them in v1); the field is `Art. + noun` or `Word`; verdicts, retry and article rules are `AnswerMeaning`'s, which needed no change.
- Measured at 40x12 with the Fernweh fixture: the front takes 6 body rows, the retry 5 and the verdict after a second try 7 of the 10, with no scrolling.
- Existing de_de cards on a dev `learning.db` do not match a later plan of their sense (content gained keys, design §7.14), so the picker will not mark them "(has cards)" and could add a duplicate.
- Not verified by hand on Termux.
