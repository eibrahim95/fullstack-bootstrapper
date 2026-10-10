# stack: cotton
Django + django-cotton + django-basecoat + Unpoly + Alpine.js + Tetra + Tailwind CSS v4.
Server owns the page. Unpoly swaps fragments. Alpine for local state. Tetra only for server-backed widgets.
Needs: uv, just, node/npm (all from /setup). Network for PyPI and npm.

Vars: `$R` = repo dir, `$S` = this skill dir, `<slug>`, `<title>`, `<one_liner>` from status.json.

## verified versions
Ran end to end 2026-10-11 on Linux x86_64, Python 3.13.5, uv 0.11.19, node/npm present.
Pinned on purpose. Newer: re-run every check below before bumping.

| piece | pin | via |
|---|---|---|
| Django | 6.1.2 | uv |
| django-cotton | 2.7.2 | uv |
| django-basecoat | 0.2.0 | uv (only release; built for basecoat-css 0.3.x) |
| tetra | 0.8.5 | uv |
| channels | 4.3.2 | uv (tetra imports it, does not declare it) |
| unpoly (python, server protocol) | 3.2.0 | uv |
| psycopg[binary] | 3.3.6 | uv |
| redis | 8.1.0 | uv |
| python-dotenv | 1.2.4 | uv |
| tailwindcss, @tailwindcss/cli | 4.3.3 | npm |
| basecoat-css | 0.3.11 | npm (1.x renamed API; django-basecoat 0.2.0 targets 0.3) |
| unpoly (JS/CSS) | 3.14.3 | npm |
| esbuild | 0.27.2 | npm (tetra builds component JS/CSS with it) |
| Alpine.js | bundled by tetra | `{% tetra_scripts include_alpine=True %}`. Never load a second Alpine. |

## gotchas (found while verifying)
- tetra 0.9.x wheels miss `components/default/link/link.html`: app fails to start (`Link is not a valid component`). Use 0.8.5 until a fixed wheel ships.
- tetra imports `channels` at startup even without reactive components. Install it; ASGI/channel layer only needed for reactive components.
- tetra needs esbuild: `TETRA_ESBUILD_PATH` points at `node_modules/.bin/esbuild`. Its auto-download into site-packages failed here.
- tetra writes built JS/CSS into `<app>/static/<app>/tetra/` on `tetrabuild`/`runserver`. Tests need `tetrabuild` first (`just test` does it). Gitignored.
- Tetra tag: `{% load tetra %}` then `{% component Counter / %}`. Library = `core/components/default.py`.
- Tailwind auto-detection skips gitignored `.venv`. `input.css` has explicit `@source` for django_basecoat templates. Verified: `animate-spin` from `<c-spinner>` lands in `app.css`.
- `.env` loaded by python-dotenv; real env vars win. `POSTGRES_DB=` (empty) -> sqlite, `REDIS_HOST=` (empty) -> in-memory cache.

## scaffold
Run in order. Any non-zero exit: stop, scaffold failed.
1. `mkdir -p $R && cd $R`
2. `uv init --bare --name <slug> --python 3.13 --vcs none`
3. `uv add "django==6.1.2" "django-cotton==2.7.2" "django-basecoat==0.2.0" "tetra==0.8.5" "channels==4.3.2" "unpoly==3.2.0" "psycopg[binary]==3.3.6" "redis==8.1.0" "python-dotenv==1.2.4"`
4. `uv run django-admin startproject config .` then `uv run python manage.py startapp core`
5. `python3 -I $S/scripts/render.py $S/references/stacks/cotton/files $R <slug> "<title>" "<one_liner>"`
   Overwrites `config/settings.py`, `config/urls.py`, `core/views.py`, `core/tests.py`; adds the rest of `files/`.
6. `npm install --no-audit --no-fund` (writes package-lock.json from pins in package.json)
7. `python3 -I $S/scripts/write-env.py <repo-root>/.bootstrap/setup.json $R <slug>`
   Writes `.env` mode 600 with postgres/redis host, port, user, password. Prints key names only. Never cat `.env`.
8. `just vendor css tetra`
9. `uv run python manage.py check` -> `System check identified no issues`.
10. Before DB exists: `POSTGRES_DB= REDIS_HOST= uv run python manage.py test` -> `OK` (sqlite, first page renders: title, Basecoat button, Unpoly, Tetra component).

## files/ (what render.py lays down)
- `config/settings.py`: env-driven. Apps: tetra (before staticfiles), django_cotton, django_basecoat, core. Middleware: UnpolyMiddleware, TetraMiddleware last.
- `config/urls.py`: `/` home, `admin/`, `__tetra__/`.
- `templates/base.html`: app.css, unpoly, `static/js/app.js` (CSRF header for Unpoly), basecoat `all.min.js`, tetra styles/scripts with Alpine. `<main up-main>`.
- `templates/pages/home.html`: first page. Cotton page header, Basecoat card + button, Alpine toggle, Tetra counter.
- `templates/cotton/page_header.html`: first project component.
- `core/components/default.py`: Tetra `Counter`. `core/tests.py`: home page test.
- `static/css/input.css`: Tailwind + basecoat-css + `@source` + empty `@theme`.
- `package.json`, `justfile` (setup, vendor, css, css-watch, tetra, run, migrate, check, test), `_gitignore` -> `.gitignore`, `.env.example`, `README.md`, `AGENTS.md`.
- New repo AGENTS.md states stack, run commands, layout, component ladder. Mentions nothing outside the repo.

## db
Connection from `.bootstrap/setup.json` `postgres`. One bash call each, password only via env, never echoed:
```bash
SJ=<repo-root>/.bootstrap/setup.json
PGPASSWORD="$(jq -r .postgres.password $SJ)" psql -h "$(jq -r .postgres.host $SJ)" -p "$(jq -r .postgres.port $SJ)" -U "$(jq -r .postgres.username $SJ)" -d postgres -tAc "select 1 from pg_database where datname='<slug>'"
PGPASSWORD="$(jq -r .postgres.password $SJ)" psql -h "$(jq -r .postgres.host $SJ)" -p "$(jq -r .postgres.port $SJ)" -U "$(jq -r .postgres.username $SJ)" -d postgres -c 'CREATE DATABASE "<slug>"'
```
Then in `$R`: `just migrate` -> all `OK`; `just test` -> `OK` (creates and drops `test_<slug>`; role has CREATEDB).
Not run against real postgres during verification (sqlite path verified). Redis cache config not exercised by tests.

## prototype -> app (future work, not done by bootstrap)
html-prototype is throwaway. Nothing is copied automatically. When building real screens:
- `<!-- c-component: entity-card  props: item -->...<!-- /c-component -->` -> `templates/cotton/entity_card.html` with `<c-vars item />`, used as `<c-entity-card :item="item" />`. Swap raw Basecoat markup for django-basecoat tags (`<c-card>`, `<c-button>`).
- `<!-- server: for item in recent_items -->` + Alpine `x-for` over `data.js` -> `{% for item in recent_items %}` fed by the view. `data.js` entities -> models.
- `up-follow` / `up-layer` links carry over as is; each target becomes a real URL returning a full page.
- Prototype `assets/app.css` tokens -> `@theme {}` in `static/css/input.css`. `assets/vendor/fonts/*.woff2` -> `static/fonts/` + `@font-face`.
- Theme toggle, dark mode, Basecoat re-init after Unpoly swaps: not wired yet.
