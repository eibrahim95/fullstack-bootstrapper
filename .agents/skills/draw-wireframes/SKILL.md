---
name: draw-wireframes
description: Split journeys into screens, write screen inventory, draw wireframes. Use after /draw-journeys. Writes wireframes/ in project dir, sets wireframes step.
---
# draw-wireframes
Journey pages -> screens -> wireframes.
Arg: project `NN` or slug.
User may skip this step: /project handles it (marks `skipped`). This skill never skips itself.

## project
1. Pick project: arg. No arg: one non-bootstrapped project -> use it. Several -> numbered list (id, title, state), ask. None -> say run /new-project. Missing id -> error.
2. Need step `journeys` done. Else stop: "run /draw-journeys NN".
3. Step `wireframes` already done: ask overwrite. No -> report skipped. Yes -> delete every `wireframes/*.html`, then redo. Needs new approval. Warn: html-prototype and later may be stale. Do not reset them.
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
`sections` optional. When absent or empty, the render script groups hubs (`id` starts `hub-`), then journey `cross-cutting`, then one section per other journey. Each screen once. HTML ignores section `color`.
md opens with counts per journey, unique total after dedupe, five most debatable calls with fallback.
`round: N` on its own line in the md. Not a json field. The script does not read it. First render: N = 1.

## render
Picture is page layout, grayscale, not visual design.
Pass `round: N` from `screen-inventory.md`.
Run: `python3 -B -I .agents/skills/draw-wireframes/scripts/render_wireframes.py --inventory <dir>/screen-inventory.json --out <dir> --round N`
`<dir>` = `wireframes/`.
Script copies `references/wireframe.css` onto `<dir>/wireframe.css`. Leave that file to the script.
Script writes `<dir>/index.html` (title, screen count, sections in order, one link per screen id) and `<dir>/<id>.html` per screen.
Shell: banner `Wireframe, not the product. Round N. <YYYY-MM-DD>.`, stylesheet `wireframe.css`, link to `index.html`.
Screen page also shows its id and name, From / To links to `<other-id>.html`, and one phone frame. `platform` `both` also gets a desktop frame beside it.
First render writes an empty `<div data-slot="frame"></div>`. Script writes no regions into the slot.
An id in `sections` that is not a screen is an error. A screen with no section is an error. An entry or exit id that is not a screen id is an error. An existing screen page with no `data-slot="frame"` is an error.
Fill only the inside of each slot. Use classes from `references/wireframe.css`. Then run the checker.
Inside the slot:
- Place header, body, footer. A list is one example row, not a sentence that says "list".
- Every region is an element with `data-region` equal to the exact region string.
- Every variant shown has `data-variant` equal to the exact variant string.
- Spec wording stays. `TBD` stays `TBD`.
- Class `unset` is a gray bar only where the spec has no words for that block.
- At most one `primary` in the phone slot, one in the desktop slot, and one in each variant frame.
- An image is a crossed box (class `image`), not a file or URL.
- When `platform` is `both`, the script writes an empty desktop frame beside the phone. Fill that slot only when the layouts differ. Leave it empty when they match. A filled desktop slot ends with class `why`, saying why.
- A variant whose layout changes (empty, error, limit) is class `frame` inside the slot.
- Toast, inline validation, tooltip, and selected stay labels on the main frame, still with `data-variant`.

## verify
Run: `python3 -B -I .agents/skills/draw-wireframes/scripts/check_wireframes.py --inventory <dir>/screen-inventory.json --dir <dir>`
Done when it prints `ok screens=N` and exits 0. On failure, fix the reported file and rerun.
The checker requires `TBD` in the visible text of a region or variant that contains it. It does not read the spec. Agent confirms each spec `TBD` is still `TBD`, and each `unset` bar is a block the spec does not word. Say what the script did not check.
Headless browser present: screenshot `wireframes/index.html` and one screen from each journey. Absent: say `not viewed`.

## approve
/build-html-prototype translates these wireframes into HTML. Unapproved wireframes must not feed it. Step is `done` only after user approves.
1. Show: unique screen count, per-journey counts, debatable splits (with fallback each), flagged gaps, where to look (`wireframes/index.html`).
2. Ask: `Approve wireframes? (y, or say what to change)`.
3. Changes: add, drop, merge, split, rename screens, resolve a gap, change regions. Edit `screen-inventory.json` and `.md` only, never `spec/` or `journeys/` (spec wrong: say run /write-spec NN). Edit the affected slots. Re-render, verify again, show the delta, ask again.
   Re-render: bump `round: N`. Delete `<id>.html` for a screen you dropped. Run the render script, then the checker. The script overwrites shells and keeps slot inner HTML, including `data-slot="frame-desktop"` when the page already has it.
   Max 3 change rounds, then ask: keep going or stop here. Stop here: leave step pending, say rerun resumes review.
4. Approved: write `approved: <date>` line at top of `screen-inventory.md`. Go to state.
Step pending and `wireframes/` exists (earlier run stopped before approval): offer to resume at 1 with existing inventory, or redo.

## state
Only after approve. `S` = `python3 -I .agents/skills/project/scripts/status.py .bootstrap/projects/NN`. `S step wireframes status=done path=wireframes result="<report line>"` (sets `state` wireframes-created). Failure: `S step wireframes status=failed result="<report line>"`. Not approved yet: write nothing.

## report
Say: unique screens, per-journey counts, HTML wireframes, debatable calls, gaps, files. Open `wireframes/index.html`.
Last line, exactly one (NN = project id):
`draw-wireframes: done NN wireframes/` (approved)
`draw-wireframes: pending NN` (user stopped before approval)
`draw-wireframes: failed <reason>`
`draw-wireframes: skipped NN`
