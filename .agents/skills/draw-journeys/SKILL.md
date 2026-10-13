---
name: draw-journeys
description: Draw user journeys from the spec as YAML plus clickable HTML flow maps. Use after /write-spec. One YAML per spec Flow heading. Writes journeys/ in project dir. Step stays pending until the user approves.
---
# draw-journeys
Spec in, flow maps out.
Arg: project `NN` or slug.

## project
1. Pick project: arg. No arg: one non-bootstrapped project -> use it. Several -> numbered list (id, title, state), ask. None -> say run /new-project. Missing id -> error.
2. Need step `spec` done (skipped steps between ok). Else stop: "run /write-spec NN".
3. Step `journeys` already done: ask overwrite. No -> report skipped. Yes -> regenerate from spec, replace files, needs new approval. Warn: wireframes and later may be stale. Do not reset them. Before replacing files: `S step journeys status=pending`.
4. Step not done and `journeys/*.yaml` exists: offer resume at approve with those files, or redo from spec.
Project dir = `.bootstrap/projects/NN/`. Read `status.json`, `spec/spec.md`.
`S` = `python3 -I .agents/skills/project/scripts/status.py .bootstrap/projects/NN`. Never edit `status.json` by hand.

## parse
Read spec User Stories. One yaml per `### Flow:` heading (`journeys/<flow>.yaml`). Slug from that heading. Single flow: slug = project slug. Not one file per story. `## Goals` is not a flow. Priority is importance inside the finished product, not a reason to drop a flow. Non-Goals and Validation notes are not flows.
Stories and edge cases under that heading become pages and transitions per `references/schema.md`.
Contents only from spec. No invented bullets.
Personas: only if spec names several roles.
Spec ambiguous (unclear target page, missing failure path, two headings that are one flow): ask user. One question at a time, short, offer a default. Else decide silently.

## write
1. Write `journeys/<flow>.yaml` per schema. Quote strings (see schema).
2. Render: `uv run --with pyyaml python3 .agents/skills/draw-journeys/scripts/render.py .bootstrap/projects/NN/journeys`
   Validates, writes `<flow>.html` for each yaml plus `index.html`.
   ERROR: fix yaml, rerun. Over 12 pages or 30 transitions: split flow.
   WARN no success/error state: add from spec edge cases, or tell user.
3. Check: every yaml has html, counts match, no orphan, reachable.
HTML: single file, inline CSS and JS, box click opens modal, template in `references/html-template.html`. YAML is truth. Never hand-edit HTML.

## approve
Step is `done` only after the user approves. Unapproved journeys must not feed /draw-wireframes.
1. Show: flows, pages, transitions, warnings, open `journeys/index.html`.
2. Ask: `Approve journeys? (y, or say what to change)`.
3. Changes: edit the yaml to match what the user said, re-render, check again, show the delta, ask again. Never hand-edit HTML. Spec wrong: say run /write-spec NN. Do not edit `spec/`.
   Max 3 change rounds, then ask: keep going or stop here. Stop here: leave step pending, say rerun resumes review.
4. Approved: go to state.

## state
Only after approve. `S step journeys status=done path=journeys result="<report line>"` (sets `state` journey-drawn).
Failure: `S step journeys status=failed result="<report line>"`.
Not approved yet: write nothing, unless this run already set `pending` to clear a previous `done`. That stays `pending`.

## report
Say: flows, pages, transitions, warnings, open `journeys/index.html`.
Last line, exactly one (NN = project id):
`draw-journeys: done NN journeys/` (approved)
`draw-journeys: pending NN` (user stopped before approval)
`draw-journeys: failed <reason>`
`draw-journeys: skipped NN`
