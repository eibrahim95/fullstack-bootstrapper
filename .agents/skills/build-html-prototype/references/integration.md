# Step 6 integration, output, done, report

## Step 6
1. Run link checker over every HTML file. Broken links go to owning agent. This fix does not count against round cap.
2. Confirm every inventory ID has a file, count matches inventory.
3. Run journey walker for every journey. Run screenshot script default mode into `screenshots/`, sweep mode into `screenshots/sweep/`. Name files `<screen-id>-<width>.png`. Sweep runs after Step 5 fixes.
4. Spawn lead-model `general-purpose` critic (role ux reviewer). Runs `impeccable critique` on five screens, from source, images, new `sweep-report.json`. No browser. Reports, fixes nothing. Five screens: home, core work surface, main creation flow, main detail screen, main conversion or payment screen.
5. Spawn one reviewer-model agent: compare five random screens against PRD acceptance criteria. Reports, fixes nothing.
6. One extra fix round. Finding on a screen from items 4 and 5: owning implementer. Finding on shell, home screen, `fragments/`, `tools/`: 2b. Finding on `assets/` or `DESIGN.md`: lead-model agent in 2a role. Finding needing a token change (colour, size, radius, font): lead-model agent in 2a role edits `assets/app.css` once, all such findings together, then rerun default screenshots. Log what remains.
7. Write `README.md` (how to open first, what is faked, screen map) and `NOTES.md` (gaps, assumptions, inventory disagreements, sample values, `EXTRA` items, anything not verified).

Stop after Step 6. Blocker remains: log in `NOTES.md`, finish.

## Output structure
```
OUT/
  PRODUCT.md  DESIGN.md  PRODUCT-RULES.md      design context (OUT root)
  README.md  NOTES.md  index.html
  assets/   app.css  theme.css  app.js  data.js  link-map.json  vendor/ (libs, fonts/)
  screens/  one folder per journey, one file per inventory ID, lowercase
  fragments/  manifest.json  ...                built in Step 2
  tools/    link-map generator, link checker, screenshot script, journey walker
  reviews/  screenshots/
```
Name each screen file by inventory ID. Do not rename IDs.

## Definition of done
- [ ] `index.html` lists every inventory screen. Each opens.
- [ ] Every journey clicks through end to end, no dead link.
- [ ] No horizontal page scroll from about 320 px to 1920 px, portrait and landscape, light and dark.
- [ ] `grep` finds no `<style` block and no `style=` attribute in `screens/` or `fragments/`. Colour binding and marked theme block exempt.
- [ ] At 1440 px: body text at most 16 px, typical controls 32-40 px, per `brief/responsive.md`.
- [ ] `impeccable detect` reports no errors on `screens/` and `fragments/`.
- [ ] Prototype-controls drawer works, state survives navigation and reload.
- [ ] Reviews exist in `reviews/`. Every blocker and major fixed or logged.
- [ ] `screenshots/` holds one image per screen at 390, 820, 1440 px.
- [ ] `README.md` and `NOTES.md` written.

## Final report to user, in order
1. Path to `OUT/index.html`. Open it in a browser, no server.
2. How many screens work, which do not.
3. What is faked.
4. Open issues and `EXTRA` items needing a decision.
5. Anything not verified, named plainly.
