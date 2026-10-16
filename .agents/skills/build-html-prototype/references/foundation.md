# Step 2 foundation (lead model, three agents in sequence)

Subagent type `general-purpose` for all. Role named in each brief. `designer` and `ux reviewer` run no browser: you run the screenshot script, give them output.

## 2a designer
1. Download vendor libs and fonts (`brief/stack.md`). Check each file.
2. Follow impeccable `init` seeded from PRD. Write `PRODUCT.md`. Report missing answers to orchestrator. Ask user only what PRD cannot answer. PRD analogies and competitor descriptions go in as facts, never as the visual world or brand. No visual identity in PRD: write that, invent none.
3. Write `PRODUCT-RULES.md`: every testable rule in PRD user stories and edge cases, one line each, with story ID. Reviewer checks screens against it.
4. Follow impeccable `shape` for home screen: task, one primary action, first-viewport content.
5. Direction, per `design=` from the brief (`SKILL.md` design section):
   - `design="<user direction>"`: build it. Record it word for word.
   - `design=roll`: follow impeccable `new-work.md` steps 1-4: list seven grounded directions, then run `${IMPECCABLE}/scripts/impeccable concept-seed --scope direction --mode <mode>` in `OUT` (needs `PRODUCT.md`). Mode from the home screen's register, usually `operate`. Build the assigned index, fused with challengers per `new-work.md`. Re-roll only on named factual grounds, never taste.
   - Attended run: stop here and return the assigned direction card (world, palette, type, signature, risk) to the orchestrator. It asks the user: accept, or re-roll with `--from <key>` eliminated. Max two re-rolls, then ask what is missing.
   - Never take a world, palette, font or signature from a previous `OUT`, `OUT.prev-*`, or the orchestrator's brief.
6. Write `DESIGN.md`. First section `## Direction`: source (`roll` with seed key and assigned index, or the user's words), the world in one line. Then three choices, tokens, token mechanism, responsive list from `brief/responsive.md`.
7. Write `assets/app.css`: `@font-face`, every token value on `:root` and `.dark`, Basecoat token overrides, keyframes. Write `assets/theme.css`: the `@theme inline` block that maps Tailwind names to those variables, `var(--x)` only, no literal values (`brief/stack.md`). Only an agent in the 2a role edits these.

## 2b builder
1. Write `assets/data.js` and `assets/app.js` (Alpine store, prototype-controls drawer) per `brief/data-spec.md`.
2. Build app shell and one reference screen, the home screen: sidebar on desktop, bottom bar on phone, top bar, content area.
3. Build every fragment the inventory implies (modals, drawers, sheets) in `fragments/` as Basecoat `dialog` or sheet markup (`brief/stack.md`). Write `fragments/manifest.json`: id, file, what opens it. Step 3 screens copy a fragment's markup inline and open it there.
4. Write `index.html`: all screens grouped by journey, one link each.
5. Write `tools/`: generator for `assets/link-map.json` from inventory JSON, link checker, journey walker. Run generator.
6. Write screenshot script in `tools/`. Takes screen list and width list. Default mode: images at 390, 820, 1440 px. Sweep mode: 320 to 1920 px in steps of 100, plus portrait and landscape phone sizes. Sweep writes images and `sweep-report.json` into `screenshots/sweep/`. Report per screen and width: horizontal overflow; targets under 44 px below 768 px; targets under 24 px from 768 px; body text size and median control height at 1440 px. Pages open over `file://`, no server.

## 2c gate
Separate agent from 2a and 2b, role ux reviewer. Reports, fixes nothing.
1. You run sweep script on reference screen first. Give agent image folder and `sweep-report.json`. Agent runs no browser. Criterion it could not see: "not verified".
2. Agent follows impeccable `critique` and `audit` on reference screen, from source, images, report. Also checks: desktop density at 1440 px per `brief/responsive.md`; `DESIGN.md` direction source is `roll` with a seed key or the user's words, not an invented pin.
3. One fix round. Findings on `assets/`, `DESIGN.md`, `PRODUCT.md`: new lead-model agent in 2a role. Findings on shell, reference screen, fragments, tools: 2b. Then sweep and a fresh 2c once more.
4. Blocker or major remains: do not start Step 3. Bad foundation gets copied into every screen.
