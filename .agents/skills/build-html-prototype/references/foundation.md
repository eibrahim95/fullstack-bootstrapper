# Step 2 foundation (lead model, three agents in sequence)

Subagent type `general-purpose` for all. Role named in each brief. `designer` and `ux reviewer` run no browser: you run the screenshot script, give them output.

## 2a designer
1. Download vendor libs and fonts (`brief/stack.md`). Check each file.
2. Run `impeccable init` seeded from PRD. Write `PRODUCT.md`. Report missing answers to orchestrator. Ask user only what PRD cannot answer.
3. Write `PRODUCT-RULES.md`: every testable rule in PRD user stories and edge cases, one line each, with story ID. Reviewer checks screens against it.
4. Run `impeccable shape` for home screen: task, one primary action, first-viewport content.
5. Write `DESIGN.md`: three choices, tokens, token mechanism that works with Tailwind browser build, responsive list from `brief/responsive.md`.
6. Write `assets/app.css`: tokens, `@font-face`, Basecoat token overrides, theme keyframes. Nothing else. Browser build cannot read it: also write `assets/tokens.css` (see `brief/stack.md`). Only an agent in the 2a role edits these. Tokens frozen after Step 2.

## 2b builder
1. Write `assets/data.js` and `assets/app.js` (Alpine store, prototype-controls drawer) per `brief/data-spec.md`.
2. Build app shell and one reference screen, the home screen: sidebar on desktop, bottom bar on phone, top bar, content area.
3. Build every fragment the inventory implies (modals, drawers, sheets) in `fragments/`. Write `fragments/manifest.json`. Step 3 screens link to these by path.
4. Write `index.html`: all screens grouped by journey, one link each.
5. Write `tools/`: generator for `assets/link-map.json` from inventory JSON, link checker, journey walker. Run generator.
6. Write screenshot script in `tools/`. Takes screen list and width list. Default mode: images at 390, 820, 1440 px. Sweep mode: 320 to 1920 px in steps of 100, plus portrait and landscape phone sizes. Sweep writes images and `sweep-report.json` into `screenshots/sweep/`. Report lists horizontal overflow and tap targets under 44 px, per screen and width.

## 2c gate
Separate agent from 2a and 2b, role ux reviewer. Reports, fixes nothing.
1. You run sweep script on reference screen first. Give agent image folder and `sweep-report.json`. Agent runs no browser. Criterion it could not see: "not verified".
2. Agent runs `impeccable critique` and `impeccable audit` on reference screen, from source, images, report.
3. One fix round. Findings on `assets/`, `DESIGN.md`, `PRODUCT.md`: new lead-model agent in 2a role. Findings on shell, reference screen, fragments, tools: 2b. Then sweep and a fresh 2c once more.
4. Blocker or major remains: do not start Step 3. Bad foundation gets copied into every screen.
