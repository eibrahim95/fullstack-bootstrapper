# {Title} - Spec

## Problem Statement
Problem from the user's perspective. Who, when, cost of today's alternative.

## Solution
Solution from the user's perspective. The whole product.

## Goals
3-5 measurable outcomes.

## Non-Goals
Parts the user removed from the product.

## User Stories
Every flow of the product. Format:
`N. As a <actor>, I want <feature>, so that <benefit>`
Group by flow (one flow = one future journey). Number continuously across groups.

### Flow: {name}
1. As a ...
2. As a ...

Edge cases:
- {empty, error, permission, duplicate, offline case}

### Flow: {name}
...

## Requirements
Importance inside the finished product. Empty P1 or P2 is fine.
### P0 (must exist)
### P1 (should)
### P2 (user deferred)

## Implementation Decisions
Prose only, behavior and module level. Stack is `django+unpoly`; do not pick another.
- Modules built or changed, and their interfaces
- Data model: entities, key fields, relations
- Integrations and contracts
- Notable interactions
No file paths. No code.

## Success Metrics
### Leading (days-weeks)
### Lagging (weeks-months)
Lagging metrics may measure the kill-criteria thresholds.

## Out of Scope
What this document does not cover: ops, marketing, a different product.

## Open Questions
`TBD` entries with owner or next step. Never invent answers.

## Further Notes
Constraints (timeline, platforms, must-use integrations), risks, anything else.

### Validation notes
Smallest demo, if one was named. Kill criteria: the observation that would park the product later.
