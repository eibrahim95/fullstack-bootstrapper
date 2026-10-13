# Journey YAML schema

One file per `### Flow:` heading in spec User Stories: `journeys/<flow>.yaml`. Single flow: slug = project slug. Not one file per story. `## Goals` is not a flow.

```yaml
version: 1
flow: <kebab-case slug, = filename>      # `feature:` accepted as alias
project: <project slug>
title: <human title>
description: <one sentence>
generated_at: <ISO-8601>
generated_by: /draw-journeys
personas: []                              # optional, e.g. [guest, member]
entry: <page-id>                          # first page user lands on
pages:                                    # nodes
  - id: <kebab-case>
    title: <Display Name>
    persona: <persona id, optional>
    description: <one line>
    contents:                             # bullets from spec only
      - <what is on the page>
    success_state: <what success looks like, optional>
    error_state: <error / empty / edge, optional>
    image: <relative path or URL, optional>
transitions:                              # directed edges
  - from: <page-id>
    to: <page-id>
    trigger: <user-readable, e.g. clicks "Pay">
notes: |                                  # optional
  Global notes, prerequisites.
```

## Spec to YAML mapping
| spec.md cue | becomes |
|---|---|
| `### Flow:` heading | one journey file |
| stories and edge cases under that heading | pages, transitions, success_state, error_state |
| numbered step, screen, "user sees X" | page |
| "click X -> Y", "then", "after X goes to Y" | transition (trigger = action) |
| acceptance criteria Given/When/Then | success_state, error_state, transition |
| edge case, failure, empty state | error_state, or an error page when it has its own exit |
| "as a <role>" | persona |
Contents bullets come from the spec only. No spec line: description only, no invented bullets.

## Validation (script enforces; errors block render)
- every `from`, `to`, `entry` is a page id; ids unique
- every page reachable from entry
- no orphan: each page has an in or out transition (single-page flow exempt)
- caps: 12 pages, 30 transitions. More: split into two flows
- warn: no page has `success_state`; no page has `error_state`

YAML safety: single-quote every string that starts with a quote or contains `: ` or `#`. Double any inner single quote.
