# [feat] Edit, suspend and delete cards

Depends on 010.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- A card's content can be edited. This includes its `note` (issue 026), also when adding one to cards that have none. Duplicate detection ignores `note`.
- A card can be suspended and unsuspended; suspended cards are not studied.
- Delete removes a card from study and from every listing, but its review history is kept.
