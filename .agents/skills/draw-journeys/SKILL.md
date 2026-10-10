---
name: draw-journeys
description: Draw user journeys from the spec as YAML plus clickable HTML flow maps. Use after /write-spec. Writes journeys/ in project dir, sets journeys step.
---
# draw-journeys
Spec in, flow maps out. Source: technique from apexyard `/journey` (MIT).
Arg: project `NN` or slug.

## project
1. Pick project: arg. No arg: one non-bootstrapped project -> use it. Several -> numbered list (id, title, state), ask. None -> say run /new-project. Missing id -> error.
2. Need step `spec` done (skipped steps between ok). Else stop: "run /write-spec NN".
3. Step `journeys` already done: ask overwrite. No -> report skipped. Yes -> regenerate from spec, replace files. Warn: wireframes and later may be stale. Do not reset them.
Project dir = `.bootstrap/projects/NN/`. Read `status.json`, `spec/spec.md`.

## parse
Read spec: user stories, flows, edge cases. Map to pages and transitions per `references/schema.md`.
One yaml per major flow (`journeys/<flow>.yaml`). Single flow: slug = project slug.
Contents only from spec. No invented bullets.
Personas: only if spec names several roles.
Spec ambiguous (unclear target page, missing failure path, flow vs flow split): ask user. One question at a time, short, offer a default. Else decide silently.

## write
1. Write `journeys/<flow>.yaml` per schema. Quote strings (see schema).
2. Render: `uv run --with pyyaml python3 .agents/skills/draw-journeys/scripts/render.py .bootstrap/projects/NN/journeys`
   Validates, writes `<flow>.html` for each yaml plus `index.html`.
   ERROR: fix yaml, rerun. Over 12 pages or 30 transitions: split flow.
   WARN no success/error state: add from spec edge cases, or tell user.
3. Check: every yaml has html, counts match, no orphan, reachable.
HTML: single file, inline CSS and JS, box click opens modal, template in `references/html-template.html`. YAML is truth. Never hand-edit HTML.

## state
`status.json` step `journeys`: status done, path `journeys`, result = report line. Top-level `state` = `journey-drawn`. Edit only these. Failure: status failed, result = report line.

## report
Say: flows, pages, transitions, warnings, open `journeys/index.html`.
Last line, exactly one (NN = project id):
`draw-journeys: done NN journeys/`
`draw-journeys: failed <reason>`
`draw-journeys: skipped NN`
