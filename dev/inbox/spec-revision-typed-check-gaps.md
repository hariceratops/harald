# Spec revision: four gaps in the typed meaning check

Raised by the design step for issues 023 to 027 (2026-11-01). The user decided all four on the recommendations. The spec is frozen, so the user applies this after moving it out of `dev/specs/`. The design already follows these readings, and the issues do too.

## Adding a word

Replace the bullet "A noun's gender comes from the chosen English-edition entry or, when only German-edition senses are chosen, from the German entry." with:

- A card takes a noun's gender from the entry its own sense came from: an English sense from its English entry, a German definition from its German entry. This holds even when senses of two homographs, such as das Band and der Band, are picked in one add.

## Checked meaning answers

Replace the bullet "A noun whose gender is known is typed with its article (`der Hund`). Any of the word's genders counts. ..." with:

- A noun whose gender is known is typed with its article (`der Hund`). Any of the word's genders counts. der, die, das, ein, eine, einen, einem, einer, eines, den, dem and des are recognised as articles in any case. A wrong or missing article still passes, graded Hard; if the previous answer on that card also had a wrong article, it is graded Again.
- A proper noun may be typed with or without its article, and the article never changes the grade.

## Study and card management

Replace "Sibling cards (from the same word or phrase, and of the same card type) are buried for the day." with:

- Sibling cards (from the same word or phrase, and of the same card type: German → English, English → German, German → German, Stammformen, conjugation or phrase) are buried for the day.

## Checked answers audit

Replace "After 200 checked reviews or two weeks, the checked answers are audited against the user's own judgement. If more than 5% were failed wrongly, a way to claim a right answer is reconsidered." with:

- After 200 checked reviews or two weeks, an audit shows each failed checked answer with the expected one, and the user marks the ones they were right on. The marks are not stored. If more than 5% of the checked reviews were failed wrongly, a way to claim a right answer is reconsidered.
