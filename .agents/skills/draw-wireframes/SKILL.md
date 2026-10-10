---
name: draw-wireframes
description: Split journeys into screens, write screen inventory, draw wireframes. Use after /draw-journeys. Writes wireframes/ in project dir, sets wireframes step.
---
# draw-wireframes
Journey pages -> screens -> wireframes. Source: technique and scripts from apexyard `/wireframes` (MIT).
Arg: project `NN` or slug.
User may skip this step: /project handles it (marks `skipped`). This skill never skips itself.

## project
1. Pick project: arg. No arg: one non-bootstrapped project -> use it. Several -> numbered list (id, title, state), ask. None -> say run /new-project. Missing id -> error.
2. Need step `journeys` done. Else stop: "run /draw-journeys NN".
3. Step `wireframes` already done: ask overwrite. No -> report skipped. Yes -> redo. Warn: html-prototype and later may be stale. Do not reset them.
Project dir = `.bootstrap/projects/NN/`. Read `journeys/*.yaml` and `spec/spec.md`. Spec wins on scope and `TBD`.

## split
Page is its own screen when most hold:
- R1 user goal or task changes
- R2 primary action or option set changes
- R3 own navigation: back target, deep link, interruption, resume
- R4 layout substantially different
- R5 decision or commitment point: confirm, payment, permission, limit reached
Variant, not screen: same content and actions, only data or status change (loading, skeleton, empty, inline validation, selected, toast, dropdown, tooltip). Modal = screen only with own flow or decision.
Close call: one screen plus variant, set `"debatable": true`.

## ids
Page repeated across journeys (home, details): one screen, id `hub-<area>-NN`, others reference it.
Journey-only: `<journey>-sNN`. Interrupts any journey (offline, sign-in, limit): `X-NN`, listed once.
Write dedupe map: yaml page id -> screen ids.

## define
Per screen: id, name, parent page, rules hit, entry_from, exit_to, platform, kind (`primary` | `state-screen`), 3-8 regions, variants.
Regions only from spec and journey text. `TBD` stays `TBD`. Uncertainty words ("may") stay.
Screen source never defines: `"grounded": "no"` (gap-derived proposal). List every such gap.

## inventory
Write `wireframes/screen-inventory.md` (people) and `wireframes/screen-inventory.json` (contract read by /build-html-prototype; keep schema exact):
```json
{"title": "...", "sections": [{"key": "rc1", "title": "...", "subtitle": "...", "color": "#d3f9d8", "ids": ["rc1-s01"]}],
 "screens": [{"id": "rc1-s01", "journey": "rc1", "name": "...", "parent_page": "...", "kind": "primary",
   "platform": "both", "regions": ["..."], "variants": ["..."], "entry_from": ["..."], "exit_to": ["..."],
   "debatable": false, "grounded": "yes"}]}
```
`sections` optional: scripts group hubs, cross-cutting, then per journey.
md opens with counts per journey, unique total after dedupe, five most debatable calls with fallback.

## render
Tools `mcp__excalidraw__*` present (ToolSearch `excalidraw`): Excalidraw. Else Mermaid. Say choice in one line.
Excalidraw missing: tell user `/ensure-mcp excalidraw` can add it. Continue with Mermaid.
Excalidraw:
1. `describe_scene`. Canvas has content: never clear. `snapshot_scene`, set `--origin-x` 400+ past its right edge. Empty: 0.
2. `python3 -I .agents/skills/draw-wireframes/scripts/gen_excalidraw.py --inventory <dir>/screen-inventory.json --out <dir>/wireframes.excalidraw --title "<title>" --origin-x X --origin-y Y`
3. `import_scene` (mode merge, filePath). Server reads only its allowed dir: copy file there, import, delete copy. Never inline hundreds of elements.
4. `get_canvas_screenshot`, save `overview.png`. Check crop: text fits, tags show, no overlap.
Mermaid: `python3 -I .agents/skills/draw-wireframes/scripts/gen_mermaid.py --inventory <dir>/screen-inventory.json --out-dir <dir>/mermaid --title "<title>"` -> `index.md` + one md per section.
Structural wireframes, not page layout. Say so.

## verify
- rendered screen count = inventory count
- every screen shows regions, variants, From, To
- every source `TBD` still `TBD`
Render not viewed: say so, not "checked".

## state
`status.json` step `wireframes`: status done, path `wireframes`, result = report line. Top-level `state` = `wireframes-created`. Edit only these. Failure: status failed, result = report line.

## report
Say: unique screens, per-journey counts, renderer, debatable calls, gaps, files.
Last line, exactly one (NN = project id):
`draw-wireframes: done NN wireframes/`
`draw-wireframes: failed <reason>`
`draw-wireframes: skipped NN`
