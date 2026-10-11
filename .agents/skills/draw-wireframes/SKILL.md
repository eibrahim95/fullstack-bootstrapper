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
3. Step `wireframes` already done: ask overwrite. No -> report skipped. Yes -> redo, needs new approval. Warn: html-prototype and later may be stale. Do not reset them.
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
Mermaid: `python3 -I .agents/skills/draw-wireframes/scripts/gen_mermaid.py --inventory <dir>/screen-inventory.json --out <dir>/wireframes.md --title "<title>"` -> ONE md file: contents, then per section a flow diagram and every screen.
Structural wireframes, not page layout. Say so.
One artifact only: ALL screens in one Excalidraw scene (`wireframes.excalidraw`, one canvas) or in one md file (`wireframes.md`). Never one file per screen or section.

## verify
- rendered screen count = inventory count
- every screen shows regions, variants, From, To
- every source `TBD` still `TBD`
Render not viewed: say so, not "checked".

## approve
/build-html-prototype translates these wireframes into HTML. Unapproved wireframes must not feed it. Step is `done` only after user approves.
1. Show: unique screen count, per-journey counts, debatable splits (with fallback each), flagged gaps, where to look (canvas, or `wireframes/wireframes.md`).
2. Ask: `Approve wireframes? (y, or say what to change)`.
3. Changes: add, drop, merge, split, rename screens, resolve a gap, change regions. Edit `screen-inventory.json` and `.md` only, never `spec/` or `journeys/` (spec wrong: say run /write-spec NN). Re-render, verify again, show the delta, ask again.
   Excalidraw re-render: new copy past the right edge of the old one (generator ids are not stable, never delete elements you cannot identify). Tell user the older copy is superseded. Mermaid: files overwritten.
   Max 3 change rounds, then ask: keep going or stop here. Stop here: leave step pending, say rerun resumes review.
4. Approved: write `approved: <date>` line at top of `screen-inventory.md`. Go to state.
Step pending and `wireframes/` exists (earlier run stopped before approval): offer to resume at 1 with existing inventory, or redo.

## state
Only after approve. `S` = `python3 -I .agents/skills/project/scripts/status.py .bootstrap/projects/NN`. `S step wireframes status=done path=wireframes result="<report line>"` (sets `state` wireframes-created). Failure: `S step wireframes status=failed result="<report line>"`. Not approved yet: write nothing.

## report
Say: unique screens, per-journey counts, renderer, debatable calls, gaps, files.
Last line, exactly one (NN = project id):
`draw-wireframes: done NN wireframes/` (approved)
`draw-wireframes: pending NN` (user stopped before approval)
`draw-wireframes: failed <reason>`
`draw-wireframes: skipped NN`
