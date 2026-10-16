---
name: build-html-prototype
description: Build clickable HTML prototype from spec, journeys, screen inventory via parallel subagents and impeccable. Use after wireframes. Writes html-prototype/ in project dir, throwaway.
---
# build-html-prototype

Static clickable prototype. Replaces Figma. User opens `OUT/index.html` straight from disk, no server, clicks every inventory screen. Looks like the real app: Basecoat components and tokens, Tailwind utilities. Plumbing is free: plain links, Alpine or plain JS. No Unpoly, no Django markers (`brief/stack.md`).
**You write no code.** Plan, spawn subagents, route findings, run commands, write Markdown. Read this file, `references/foundation.md`, `references/integration.md`, all of `references/brief/` before acting.

## 0 project
Per standard pipeline: arg `NN` or slug; none = the one unbootstrapped project, several = numbered list (id, title, state) and ask; none = say /new-project. Project dir `.bootstrap/projects/NN/`.
Precondition: step `wireframes` done (done = user approved, see /draw-wireframes). Prototype is the translation of those wireframes. Skipped: stop, say run /draw-wireframes NN (needs inventory). Not done: say run /draw-wireframes NN. Same for earlier unfinished steps.
Own step `html-prototype` done: ask overwrite. No: report skipped. Yes: redo, warn later steps may be stale.
Own step `running`: another thread owns it. Say so, show `thread` from step, stop. User says that thread is dead: run on.
Runs in parallel with /bootstrap-project. It needs nothing from bootstrap, and never waits for it.

## inputs
/project hands this skill to a background thread and puts the answers in the prompt: `models=<implementer>,<reviewer>`, `out=archive|wipe|stop` (only if `OUT` exists), `design=roll` or `design="<user direction>"`. Supplied: use, never ask. Not supplied: ask as below. `design` not supplied: background run = `roll`; attended run = ask once, recommend `roll`.

Paths, absolute in every subagent brief (subagents share no shell vars):
| Name | Value |
|---|---|
| `PRD` | `<project>/spec/spec.md` |
| `INV` | `<project>/wireframes/screen-inventory.{md,json}` |
| `WIREFRAMES` | `<project>/wireframes/` (`index.html` and `<id>.html`) |
| `JOURNEYS` | `<project>/journeys/` (yaml) |
| `OUT` | `<project>/html-prototype/` (entry `index.html`) |
| `BRIEF` | `<repo>/.agents/skills/build-html-prototype/references/brief/` |

Use step paths from `status.json`. Inventory missing: stop, run /draw-wireframes NN.

## requirements
- `impeccable` skill. Look in order: `<repo>/.agents/skills/impeccable`, `$HOME/.agents/skills/impeccable`, `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/impeccable`. Found = `${IMPECCABLE}`. None: stop, say `/ensure-installed impeccable`. Invent no install command.
- `python3` and headless browser (Playwright or Chrome): link check, screenshots, width sweeps. None: stop, say so.

## goal
Plain HTML. UI and UX good enough for product owner to judge product. No backend, DB, API calls, build step, real file rendering. Fake auth, payment, AI with convincing screens. Copy no design from Figma or any product. Throwaway: optimise learning speed and feel, not reuse.
Inventory decides which screens exist and where each links. Journey disagrees: follow inventory, log in `NOTES.md`. Wireframe HTML decides layout pattern, region placement, shell, and which action is primary. Each screen's `notes` are spec rules it must honor; `proposed` regions and `shell.proposed` nav are not in the spec, keep them unless the spec says otherwise. Leave PRD placeholders. Show invented values marked "(sample)", log them.

## 1 setup (before any subagent)
1. Two models (supplied in call, else ask user): implementer (builds screens), reviewer (reviews). Hardcode no names. Must differ, prefer different families. Same family: say review less independent, proceed only on confirmation. Pick effort per /delegate conventions (`.agents/skills/delegate/references/choose.md`): builders mid, reviewers by risk.
2. Probe both: one-line probe subagent per model via Agent `model` param. Unavailable: stop, report exact name. Never substitute.
3. Lead model = your own. Design, build, gate agents run on it. Pass `model` explicitly.
4. `OUT` exists: `out=` from call, else ask user: archive to `OUT.prev-<date>`, wipe, or stop. `stop`: report failed.
5. Read PRD, inventory (md + json), journeys, all of `BRIEF`.

## you may / may not
| May | May not |
|---|---|
| Spawn and message subagents | Create or edit `.html`, `.css`, `.js`, `.json`, `.py`, `.sh` |
| Run commands: downloads, headless browser, `impeccable detect`, tools a subagent wrote | Fix a subagent's code, even one line |
| Write Markdown: `README.md`, `NOTES.md` | Write a script. Ask lead-model agent. |
| Send findings to the agent owning the file | Reassign a file mid-phase without noting in `NOTES.md` |

## agent types
All `subagent_type: general-purpose`; state role in the brief. No role-typed agents here.
| Work | Role in brief |
|---|---|
| Foundation build, screens, fixes | frontend engineer |
| Design agent, design gate | UI designer |
| Reviewers | UX reviewer |
Reviewers report and fix nothing. Designer and reviewer run no browser: you run screenshot script, give output.

## design: use impeccable
`impeccable` flows `init`, `shape`, `critique`, `audit`, `clarify`, `onboard`, `harden` are reference files, not CLI verbs: "run `impeccable <flow>`" in this skill means follow `${IMPECCABLE}/reference/<flow>.md`. Real CLI: `${IMPECCABLE}/scripts/impeccable detect|concept-seed`. Work with `OUT` as cwd.
- Design agents (lead model): load skill via Skill tool, else read `${IMPECCABLE}/SKILL.md`.
- Builders, reviewers: no full skill. Read `PRODUCT.md`, `DESIGN.md`, `${IMPECCABLE}/reference/craft-floor.md` by path, run `impeccable detect <files>`. Put resolved craft-floor path in each brief.
- `PRODUCT.md`, `DESIGN.md` live in `OUT` root. They win over the skill, except the direction rule below.
- Verify in bounded passes, not loops. Use caps below.
Fixed pressure: read PRD problem, name what current alternatives get wrong; prototype answers that first. Mobile first, desktop dense (`brief/responsive.md`). WCAG AA contrast, visible focus. Light and dark via Basecoat tokens.
Direction (visual world, palette, type, signature) comes from one source only:
- `design="<user direction>"`: the user's words are the pin. Build them. Fill gaps by impeccable's rules.
- `design=roll`: `concept-seed` assigns it (`references/foundation.md` 2a). Background run builds the assigned direction, never re-rolls on taste. Attended run shows the assigned direction to the user, who accepts or re-rolls.
- Never: the designer's own top pick, a direction you or the orchestrator write into a brief, or "the opposite of the last run". A previous `OUT` or `OUT.prev-*` is not input to the direction.
- PRD analogies and competitor descriptions ("a book on a desk") are product facts, not visual metaphors.
- A face on impeccable's training-data defaults list (`${IMPECCABLE}/reference/new-work.md`, Commit the world) needs a written reason other than subject association. App screens may use one workhorse UI face for everything.
Write three choices in `DESIGN.md`: accent, font pairing, signature element. Real copy only. No progress ring as signature (craft floor lists it as default to avoid).

## 2 foundation
Read `references/foundation.md`. Run 2a designer, 2b builder, 2c gate, in sequence, lead model. No Step 3 until no blocker or major.

## 3 build (implementer model, parallel)
Group inventory screens by journey. One `general-purpose` per group, max six. Merge small journeys. Split a journey holding over a third of all screens. Disjoint file sets. No agent edits files it does not own. No one edits reference screen, `fragments/`, `assets/`: report to you. `assets/` change: lead-model agent in 2a role. Shell, `fragments/`, `tools/` change: 2b.
Every screen ID has exactly one owner. Unowned: lightest agent, log it. Hardest screen (usually core work surface): own group.
Brief short, paths not pasted text:
- Read `BRIEF/stack.md`, `BRIEF/responsive.md`, `PRODUCT.md`, `DESIGN.md`, `PRODUCT-RULES.md`, `assets/data.js`, `assets/link-map.json`, `fragments/manifest.json`, craft-floor path, reference screen. Match its shell, spacing, components.
- Owned screen IDs, inventory rows pasted.
- Read `WIREFRAMES/<id>.html` for owned screens: phone frame, desktop frame, states, numbered notes. Keep layout, region placement, and which action is primary. Visual design stays free. Log every deviation in `NOTES.md`.
- Report format: `BRIEF/stack.md` rule 10.

## 4 review (reviewer model, parallel)
Before start, run screenshot script sweep mode over every screen. Reviewers read images and `sweep-report.json`, no browser.
One UX reviewer per implementer. Reads `BRIEF/review-checklist.md`, reviews only that builder's files. Check not run = "not verified".

## 5 fix (implementer model)
Send each implementer its own review. Fix all blockers and majors, minors if cheap. Report fixed and left, with reason. Fix-round cap: this round plus the one in Step 6 item 6.

## 6 integration
Read `references/integration.md`. Run its Step 6 (link check, ID count, walker, screenshots, critic, PRD compare, one extra fix round, README + NOTES). Then check definition of done there.

## creative latitude
Brief fixes content, links, rules, stack, not design. Silent: decide, be bold and specific. Generic prototype fails. Propose one or two extras PRD does not ask for, mark `EXTRA` in `NOTES.md`. None may break `PRODUCT-RULES.md`.

## state
Another thread writes `status.json` at the same time (bootstrap). Never edit it by hand. Only through `S` = `python3 -I .agents/skills/project/scripts/status.py <project> ...`, which locks, re-reads, and recomputes `state`.
- After 0 checks pass, before 1: `S step html-prototype status=running path=html-prototype`.
- Done: `S step html-prototype status=done path=html-prototype result="<report line>"`.
- Failure: `S step html-prototype status=failed result="<report line>"`.
- User declines whole step: `S step html-prototype status=skipped`.
- After done: read `artifacts_path` and `repo_path` in `status.json`. Both set = bootstrap already moved the other artifacts. Move this one too: `python3 -I .agents/skills/bootstrap-project/scripts/move-artifacts.py <project> <artifacts_path> <repo_path> --late`. Not set: nothing, bootstrap moves it later.

## rules
1. No code from orchestrator. Delegate every script and fix.
2. Models asked, never hardcoded. Reviewer model reviews every implementer-model screen. No agent reviews own output. Critic or gate reports, different agent fixes.
3. No custom CSS outside `assets/app.css` and marked token block (`brief/stack.md`). Reviewer greps.
4. No AI attribution lines in any file.
5. Never claim a check passed unless it ran. Write "not verified".
6. Advisory output. Prototype gates nothing.

## report
Last line, exactly one:
`build-html-prototype: done NN html-prototype/`
`build-html-prototype: failed <reason>`
`build-html-prototype: skipped NN`
