# [feat] Article cards for nouns

Depends on 010. Superseded by 023 (2026-11-01): the article is now part of the typed English → German answer, and the article card type is removed. This issue is kept as the record of what was built.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- Adding a noun also creates an article card.
- The article card is answered with a single keypress for der / die / das.

## Status

Built. Both criteria are met in the pilot tests at 40x30, 40x12 and 100x30.
Open by hand in Termux: taps on der / die / das and Next, the 300 ms guard,
and the article feedback layout. Departures and discoveries are in design
§7.10.
