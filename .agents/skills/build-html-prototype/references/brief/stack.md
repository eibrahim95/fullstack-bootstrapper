# Stack and build rules (every agent reads this)

The prototype must look like the real app, not run like it. The real product uses Basecoat (django-basecoat) and Tailwind for its look. The prototype uses the same two, so components and tokens carry over. How pages link and how widgets work is free: the simplest thing that runs from disk. Do not use Unpoly. Do not imitate Django, django-cotton, or django-unicorn.

| Piece | Use here |
|-------|----------|
| Basecoat CSS and JS (shadcn-style) | Required. Use its class names and tokens for buttons, cards, inputs, badges, dialogs, tabs, sidebar. |
| Tailwind CSS v4 | Required. Browser build, vendored. |
| Alpine.js v3 | Vendored. Use for state and widgets, or plain JS where simpler. |
| Navigation | Plain `<a href>` links between full pages. |

## Libraries and fonts

Download every library and font once into `assets/vendor/`. Load with relative paths so the prototype works offline.

- Libraries: Tailwind browser build (v4), Basecoat CSS and JS, Alpine.js (v3).
- Fonts: the families chosen in `DESIGN.md`. Use at most two. App screens may use one workhorse UI face for everything. Download `woff2` files into `assets/vendor/fonts/`. Declare them with `@font-face` in `assets/app.css`.
- Download each file with a real request. Check that it is not an HTML error page. If a path fails, search for the correct path. Do not invent one.
- Do not load anything from a CDN at run time.

## Opening

Every page opens over `file://`. No server, no `fetch`, no ES module imports. Data comes from `<script src="assets/data.js">`.

## CSS rule (strict)

No custom CSS in any screen or fragment.

- Style only with Tailwind utility classes and Basecoat classes.
- Forbidden in `screens/` and `fragments/`: `<style>` blocks, `style="…"` attributes, and hand-named classes. The theme block below is the only exception to the `<style>` ban.
- One exception: data-driven colours, such as entity images or avatars. Bind them with Alpine, for example `:style="{'--c1': item.c1, '--c2': item.c2}"`. Style them with utilities such as `bg-linear-to-br from-(--c1) to-(--c2)`.
- Only an agent in the 2a role edits `assets/app.css` and `assets/theme.css`.

## Tokens: values in one file

Tailwind's browser build compiles only inline `<style type="text/tailwindcss">` blocks, not linked files. Basecoat and Tailwind read CSS variables at run time. So:

- `assets/app.css` (linked by every page) holds every token value: colours, radius, font families, type sizes, on `:root` and `.dark`. Plus `@font-face`, Basecoat overrides, keyframes. A design change edits this file only.
- `assets/theme.css` holds one `@theme inline { … }` block that maps Tailwind names to those variables, for example `--color-page: var(--page);` and `--text-display: var(--text-display);`. Only `var(--x)` values, never a literal. It changes only when a token name is added.
- Every page carries one identical copy of `theme.css` inside `<style type="text/tailwindcss">`, wrapped in `<!-- theme:start -->` and `<!-- theme:end -->`. Builders paste it unchanged. The CSS checks ignore that marked region.
- Container queries use Tailwind's `@container` and `@md:` variants. Type sizes follow `brief/responsive.md`.
- If you need a style that no utility or Basecoat class gives, report it. Do not write CSS.

## Pages, dialogs, history

- Every page is a full valid HTML document with the same shell.
- Navigation is `<a href="…">` to another page. The browser back button is the history.
- Modals, drawers, sheets, and confirm dialogs use Basecoat dialog or sheet markup inside the page that opens them, opened with Alpine or the native `<dialog>` API. Copy the markup from `fragments/`, unchanged except for data.
- Use a modal only for a task that needs interruption or protected focus (confirm, limit reached, payment). Use a sheet, drawer, or inline panel for the rest.
- Do not write a router.

## Alpine rules

- Use `x-data` for local state. Use `x-show`, `x-model`, `@click`, `x-for`.
- Fake server state lives in `assets/data.js`. Prototype controls live in the store described in `data-spec.md`.
- Small inline `<script>` blocks for Alpine data are fine. No build step.

## Rules for every agent

1. Edit only the files you own. Do not touch another agent's files.
2. Read `PRODUCT.md`, `DESIGN.md`, `PRODUCT-RULES.md`, and the reference screen before you write.
3. Read the impeccable `reference/craft-floor.md` (your brief gives the path) before you write UI. Follow it. `PRODUCT.md` and `DESIGN.md` win over it.
4. Use the data in `data.js`. Do not invent a second set of entities or names.
5. Follow the CSS rule above.
6. No backend code, API calls, build steps, external images, or external fonts. Use inline SVG and Tailwind gradients.
7. Before you report, run `impeccable detect <your files>`. Fix every error. List each remaining warning in your report.
8. Never claim a check passed unless you ran it. Write "not verified" instead.
9. No AI attribution lines in any file.
10. Report: files written, what you faked, what you skipped and why, detector output.
