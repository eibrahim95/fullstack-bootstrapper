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
- R2 primary action or option set changes. A mode that swaps the toolbar or main actions (read vs annotate, view vs edit) is its own screen.
- R3 own navigation: back target, deep link, interruption, resume
- R4 layout substantially different
- R5 decision or commitment point: confirm, payment, permission, limit reached
Variant, not screen: same content and actions, only data or status change (loading, skeleton, empty, inline validation, selected, toast, dropdown, tooltip). Modal = screen only with own flow or decision.
Every journey gets at least one screen of its own, or a line in the dedupe map naming the screen it shares and why.
Close call: one screen plus variant, set `"debatable": true`.

## ids
Page repeated across journeys (home, details): one screen, id `hub-<area>-NN`, others reference it.
Journey-only: `<journey>-sNN`. Interrupts any journey (offline, sign-in, limit): `X-NN`, listed once.
Write dedupe map: yaml page id -> screen ids.

## define
Spec and journeys say what must be true. They do not say what is on screen. Translate.
Per screen:
- `layout`: the closest pattern in `references/layouts/` (list, grid, detail, form, canvas, chat, settings, dashboard, checkout, state). Pick by the screen's job, the way common apps do it.
- `chrome`: `app` (app bar + tab bar on phone, sidebar on desktop), `focus` (app bar with back, no tabs: reader, editor, checkout, wizard), `none` (sign-in, splash, full-screen state). `nav`: the shell nav item it belongs to, if any.
- `regions`: 3-8 UI parts a person would point at, named in at most 6 words ("Search", "Shelf list", "Pen tools", "Card entry (processor TBD)"). A region is a component, never a sentence.
- `notes`: each spec or journey rule the screen must honor, word for word, with the story numbers it covers. Rules, limits, data facts, "never", "only", "may" go here, not on the frame.
- `covers`: spec story numbers (`### Flow` lists in spec.md) this screen serves.
- `variants`: visual states only (empty, loading, error, limit, success, selected), at most 6 words each. A rule ("X never shows Y") is a note, not a variant.
- `proposed`: regions the spec does not ask for but the screen needs to work (back, nav, filter). Drawn dashed.
- `platform`: `phone`, `desktop`, or `both`. Decide from the spec (admin-only screens are usually desktop). Do not default everything to both.
- Also: id, name, parent page, rules hit, entry_from, exit_to, kind (`primary` | `state-screen`).
`TBD` stays `TBD` in the label or note that carries it. Screen source never defines: `"grounded": "no"` (gap-derived proposal, may cover nothing). List every such gap.
App shell, once per project: `shell.nav` 3-5 top-level destinations from the spec's main areas, `shell.brand`. Items the spec does not name go in `shell.proposed` and in the gaps.
Every spec story is in some screen's `covers` or note `covers`. List the story numbers in top-level `stories`.

## inventory
Write `wireframes/screen-inventory.md` (people) and `wireframes/screen-inventory.json` (contract read by /build-html-prototype; keep schema exact). Worked example: `fixtures/sample-inventory.json`.
```json
{"title": "...", "stories": [1, 2, 3],
 "shell": {"brand": "...", "nav": ["Library", "Catalog", "Account"], "proposed": ["Account"]},
 "sections": [{"key": "rc1", "title": "...", "subtitle": "...", "color": "#d3f9d8", "ids": ["rc1-s01"]}],
 "screens": [{"id": "rc1-s01", "journey": "rc1", "name": "...", "parent_page": "...", "kind": "primary",
   "platform": "both", "layout": "list", "chrome": "app", "nav": "Library", "covers": [1, 2],
   "regions": ["Search", "Book list", "Upload"], "variants": ["Empty library", "No results"],
   "notes": [{"text": "<spec sentence, word for word>", "covers": [2]}], "proposed": [],
   "entry_from": ["..."], "exit_to": ["..."], "debatable": false, "grounded": "yes"}]}
```
`regions` and `variants` stay lists of strings. `sections` optional. When absent or empty, the render script groups hubs (`id` starts `hub-`), then journey `cross-cutting`, then one section per other journey. Each screen once. HTML ignores section `color`.
md opens with counts per journey, unique total after dedupe, the shell (marking proposed nav), five most debatable calls with fallback, the dedupe map, stories each screen covers.
`round: N` on its own line in the md. Not a json field. The script does not read it. First render: N = 1.

## render
Picture is page layout, grayscale, not visual design. It shows how the page works: what is where, how big, what is pressed.
Pass `round: N` from `screen-inventory.md`.
Run: `python3 -B -I .agents/skills/draw-wireframes/scripts/render_wireframes.py --inventory <dir>/screen-inventory.json --out <dir> --round N [--fills <dir>/fills.html]`
First run without `--fills` seeds each page from its layout template; read the seeds, then write `fills.html`.
`<dir>` = `wireframes/`. Add `--reset-slots` to throw away every slot and re-seed from templates (old round from before layouts, or a screen changed `layout`).
Script copies `references/wireframe.css` onto `<dir>/wireframe.css`. Leave that file to the script.
Script draws per screen page: id, name, layout line, From / To links, the phone frame with shell (app bar, tab bar) from `chrome`, the notes panel numbered from `notes`, and for `both` a 1024 px desktop frame with sidebar. `index.html` shows every screen as a small phone preview, by section, arrows in journey order.
Slots the agent fills, nothing else. Write them all in one file, `<dir>/fills.html`: one `<template data-screen="<id>" data-fill="frame|states|frame-desktop">...</template>` block per slot (format: `fixtures/filled-slots.html`). Render with `--fills <dir>/fills.html`; a block replaces that slot. Later rounds: edit `fills.html`, re-render. Do not hand-edit screen pages.
- `frame`: screen content. Seeded from `references/layouts/<layout>.html`. Each seed block carries `data-todo`; replace it with real parts and drop the attribute.
- `states`: one mini frame (class `state`, first child `trigger` saying when it shows) per variant not drawn as a tag in `frame`. Seeded with placeholders.
- `frame-desktop`: only when the wide layout truly differs. Empty: the script mirrors `frame` into the desktop frame, and `cols`, `side`, `grid` reflow at 600 px (side becomes a column, grid gets 4 across). Filled: ends with class `why`.
Before filling, read `fixtures/filled-slots.html` (filled slots for the sample inventory: cart list, checkout, reader canvas, annotate mode, offline state; match that density) and `references/wireframe.css` (class list at top).
Inside `frame`:
- Draw the real thing small: toolbar with icons, a page canvas, 3 example rows, a search pill, chips, tabs, toggles, a bottom sheet. A list is 2-3 rows with `lines` for text, not a sentence that says "list".
- Every region is an element with `data-region` equal to the exact region string. Put the label on the control ("Upload", "Pen", "Search"), not a description.
- Text on the frame is labels and sample values, at most 14 words per element. Body copy is `lines`. Rules go to `notes`.
- Pin each note where it applies: `<i class="pin" data-note="N">N</i>`, N = its number in `notes`.
- Most important content gets most of the space. Main action in thumb reach (bottom, or `fab`).
- At most one `primary` in `frame`, one in `frame-desktop`, one in each `state` or `frame`.
- Image or cover is a crossed box (class `image`, `cover`), never a file or URL.
- A `proposed` region carries class `proposed`.
- Small states (toast, selected, inline validation) can stay in `frame` as class `tag` with `data-variant`. All other variants are mini frames in `states` with `data-variant`.
- `TBD` stays visible in the label that carries it.

## verify
Run: `python3 -B -I .agents/skills/draw-wireframes/scripts/check_wireframes.py --inventory <dir>/screen-inventory.json --dir <dir>`
Done when it prints `ok screens=N` and exits 0. Changed a script, the CSS, or a layout: also run `python3 -B -I .agents/skills/draw-wireframes/scripts/selftest.py`. On failure, fix the reported file and rerun. After editing `fills.html`, re-render with `--fills` (refreshes slots, mirror and index), then check.
Checker: every story covered, labels at most 6 words, no `data-todo` left, every note pinned, no sentence-length text on a frame, proposed marked, shell matches chrome, slots match regions and variants, `TBD` visible where a label has it. It does not read the spec. Agent confirms each spec `TBD` is still `TBD` and each note is spec wording.
Then look. Screenshot every screen page and `index.html` (`google-chrome --headless=new --hide-scrollbars --window-size=1500,1700 --screenshot=<out>.png file://<abs path>`; or chromium). Per screen check: reads as a screen of a real app at a glance; main content has most of the space; one obvious primary; nav present when `chrome` is `app`; no wall of text; desktop uses the width. Fix and re-render what fails. No headless browser: say `not viewed`.

## approve
/build-html-prototype translates these wireframes into HTML. Unapproved wireframes must not feed it. Step is `done` only after user approves.
1. Show: unique screen count, per-journey counts, the shell (proposed nav), debatable splits (with fallback each), flagged gaps, where to look (`wireframes/index.html`, then any screen for desktop, states, notes).
2. Ask: `Approve wireframes? (y, or say what to change)`.
3. Changes: add, drop, merge, split, rename screens, resolve a gap, change regions, layout, shell. Edit `screen-inventory.json` and `.md` only, never `spec/` or `journeys/` (spec wrong: say run /write-spec NN). Edit the affected blocks in `fills.html`. Re-render, verify again, show the delta, ask again.
   Re-render: bump `round: N`. Delete `<id>.html` for a screen you dropped. Run the render script, then the checker. The script overwrites shells and keeps slot inner HTML (`frame`, `frame-desktop`, `states`). A screen that changed `layout`: delete its `<id>.html` so it is re-seeded.
   Max 3 change rounds, then ask: keep going or stop here. Stop here: leave step pending, say rerun resumes review.
4. Approved: write `approved: <date>` line at top of `screen-inventory.md`. Go to state.
Step pending and `wireframes/` exists (earlier run stopped before approval): offer to resume at 1 with existing inventory, or redo.
Inventory has no `layout` (made before layout templates): it cannot resume. Redo define and inventory, render with `--reset-slots`, needs new approval.

## state
Only after approve. `S` = `python3 -I .agents/skills/project/scripts/status.py .bootstrap/projects/NN`. `S step wireframes status=done path=wireframes result="<report line>"` (sets `state` wireframes-created). Failure: `S step wireframes status=failed result="<report line>"`. Not approved yet: write nothing.

## report
Say: unique screens, per-journey counts, shell, HTML wireframes, debatable calls, gaps, what you viewed, files. Open `wireframes/index.html`.
Last line, exactly one (NN = project id):
`draw-wireframes: done NN wireframes/` (approved)
`draw-wireframes: pending NN` (user stopped before approval)
`draw-wireframes: failed <reason>`
`draw-wireframes: skipped NN`
