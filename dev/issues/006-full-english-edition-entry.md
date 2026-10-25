# [feat] Full English-edition entry

Complete the lexicon entry with the remaining English-edition data. Depends on 002.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- Lookup shows IPA and register tags on senses.
- Lookup shows translated English-edition examples listed per sense.
- Quotation examples are shown verbatim, typos included.

## Note 2026-10-24
- Example ids come from insertion order (shard order, then source order), not from an `example_off` offset like entries and senses (design §3.5, "ids come from rules"). The byte-identical-for-any-worker-count test passes, so output is stable. Open: add an offset, or record the exception in the design.
- Not added yet, because the criteria did not need them: `sense.context`, `sense.qualifier`, `entry.genitive`, `entry.discriminator` (design §3.1).
