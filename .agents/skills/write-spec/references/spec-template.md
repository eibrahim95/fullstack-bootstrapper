---
name: write-spec
description: Write product spec from idea and validation, one round of gap questions. Use after /validate-idea. Writes spec/spec.md, sets spec step.
---
# write-spec

Source: apexyard write-spec and ai-hero to-spec (MIT), adapted.
Synthesize first, ask only gaps.

## project
Arg `NN` (or slug). No arg: one project not bootstrapped -> use it; several -> numbered list (id, title, state), ask; none -> say run /new-project.
Dir: `.bootstrap/projects/NN/`. Missing id: error.
Precondition: step `validation` is `done` (GREEN, YELLOW proceed, or RED overridden; result tells). Else stop: "run /validate-idea NN". Failed RED: also mention `override`.
Step `spec` already `done`: ask overwrite. No: report skipped. Yes: redo, warn later steps may be stale.

## read
`idea` in `status.json`, `idea/idea.md`, `validation/validation.md`, root `README.md` stack section.
Target stack is `django+unpoly` (Django, django-cotton, Unpoly, Alpine.js, django-basecoat, django-unicorn for high-interactivity parts only, Tailwind). Spec never picks another stack. Decisions stay at behavior and module level: no file paths, no code.

## draft
Synthesize full draft from what is known. No re-interview for anything already answered (target user, alternative, smallest version, kill criteria, build/buy/rent).
Template: [references/spec-template.md](references/spec-template.md). Unknown value: `TBD`, never invent.
Seed from validation: smallest version -> P0 scope; kill criteria -> lagging metrics; current alternative -> problem framing.
Also from validation.md: `Decisions` (added, cut, changed) are binding; cuts go to Non-Goals. `Accepted risks` -> Further Notes. `Open assumptions` -> Open Questions with their check. Read `idea` fields from status.json: validation may have amended them.

## gaps
ONE round. Single message, numbered. Each question has a recommended answer, phrased so "yes" accepts. Ask only what draft cannot fill:
- success metrics
- constraints: timeline, platforms, must-use integrations
- non-goals confirmation
- anything validation left unclear
Nothing missing: skip round, say so. Apply answers. Still unknown: `TBD` in Open Questions.

## review
Show draft summary (problem, goals, story count per flow, P0 list, open questions), ask what to adjust.
Max 2 revision rounds. Then finalize.

## write
`spec/spec.md` in project dir.
User stories: grouped by flow that can become a journey. Later skills derive journeys, screens, prototype rules from them. Each flow ends with short `Edge cases` list.

## status
Edit only step `spec` + top-level `state`. Keep other keys.
Done: step done, path `spec`, result `write-spec: done NN spec/`, state `spec-created`.
Failure (user abandons): step failed, result `write-spec: failed <reason>`.
Name `/draw-journeys NN` as next. Do not run it.

## report
Last line, exactly one: `write-spec: done NN spec/` or `write-spec: failed <reason>`.

## never
Interview for known facts. Choose other stack. Put file paths or code in spec. Invent metrics or dates. Write outside `spec/` and own step.
