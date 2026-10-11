# __TITLE__

__ONE_LINER__

## Stack
Django (server owns the page), django-cotton (components), django-basecoat (Basecoat/shadcn UI as cotton components), Unpoly (navigation, layers, fragment updates), Alpine.js (local state, loaded by Tetra), Tetra (interactive server components), Tailwind CSS v4 (CSS-first `@theme`, no config file).

## Run
`just setup` once, then `just run`, `just test`, `just migrate`, `just check`.
Config in `.env` (gitignored, see `.env.example`). Never commit it.
Built CSS and vendored JS are gitignored; `just run`/`just test` rebuild them.

## Layout
- `config/` settings, urls.
- `core/` first app. `core/components/` Tetra components.
- `templates/base.html` layout. `templates/pages/` pages. `templates/cotton/` project components.
- `static/css/input.css` Tailwind entry. `static/js/app.js` Unpoly config and `up.compiler()`s.

## Component ladder (lightest that works)
1. django-basecoat component (`<c-button>`, `<c-card>`, `<c-dialog>`, ...).
2. Own cotton component in `templates/cotton/`, composed of Basecoat.
3. Alpine `x-data` for local UI state.
4. Tetra component only for server-backed interactivity.

## Rules
- Every URL returns a full HTML page; Unpoly swaps `<main up-main>`. No JSON endpoints for UI.
- Init JS in `up.compiler()`, not `DOMContentLoaded`.
- Style with Tailwind utilities and Basecoat classes, tokens in `@theme`.
- Run `just test` before every commit.
