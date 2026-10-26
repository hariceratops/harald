# [feat] Stammformen cards for verbs

Depends on 010.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- Adding a verb also creates one Stammformen card: 3rd person singular present, Präteritum, Partizip II with its auxiliary.
- Answers are typed and checked exactly, with ae/oe/ue/ss accepted for ä/ö/ü/ß.
- If a needed form is missing from the data, Harald refuses the card type and says which forms are missing.

## Status

Built. All three criteria are met in unit, component and pilot tests at
40x30, 40x12 and 100x30. Open by hand in Termux: typing in the three Inputs
with the soft keyboard, and the feedback layout at 40x12. Departures and
discoveries are in design §7.11.
