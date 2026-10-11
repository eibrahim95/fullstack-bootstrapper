# stack: django+unpoly
Django + django-cotton + django-basecoat + Unpoly + Alpine.js + django-unicorn + Tailwind CSS v4.
Server owns page. Unpoly swaps fragments. Alpine local state. django-unicorn only for high-interactivity parts.
Base = cookiecutter-django output, adapted by agent. Needs cookiecutter, uv, just, node/npm. Network: GitHub, PyPI, npm.
Vars: `<title>`, `<one_liner>`, `<slug>` from status.json. `<pkg>` = slug, `-` -> `_`. `<login>`, `<email>` = `$SJ` github. `$R` = `<parent>/<slug>`.

## source
Temp config keeps user's `~/.cookiecutters` and `~/.cookiecutter_replay` untouched:
`T=$(mktemp -d) && printf 'cookiecutters_dir: %s/c\nreplay_dir: %s/r\n' $T $T > $T/c.yaml`
`cookiecutter --config-file $T/c.yaml --no-input -o <parent> https://github.com/cookiecutter/cookiecutter-django project_name="<title>" project_slug=<pkg> description="<one_liner>" author_name="<login>" email=<email> domain_name=example.com open_source_license="Not open source" username_type=email use_docker=n postgresql_version=18 cloud_provider=None mail_service="Other SMTP" rest_api=None use_async=n frontend_pipeline=None use_celery=n mail_catcher=None use_sentry=n use_whitenoise=y use_heroku=n ci_tool=None keep_local_envs_in_vcs=n editor=None debug=n`
Then `mv <parent>/<pkg> $R` if names differ. GitHub unreachable: template = `~/.cookiecutters/cookiecutter-django` if present, say so.
Why:
- use_docker=n: postgres/redis are local, from /setup.
- use_celery=n, use_async=n: no workers; django-unicorn runs on WSGI.
- cloud_provider=None + use_whitenoise=y: template refuses None without whitenoise.
- mail_service="Other SMTP": no None choice; plain SMTP, no vendor.
- frontend_pipeline=None: Tailwind, Basecoat, Unpoly come from npm here.
- rest_api, sentry, heroku, ci, editor off: not in stack. keep_local_envs_in_vcs=n: secrets only in `.env`.
- Postgres always on (template has no switch). username_type=email, private license: user's past choices.

## goals
End state. How = agent's call. Run in `$R`. Before db exists prefix tests with `POSTGRES_DB= REDIS_HOST=`.
1. Python deps django, django-cotton, django-basecoat, django-unicorn, unpoly in pyproject + uv.lock. Python = template pin. verify: `uv pip list | grep -ciE '^(django|django-cotton|django-basecoat|django-unicorn|unpoly) '` = 5; `.venv/bin/python -V` matches `requires-python`
2. npm deps tailwindcss, @tailwindcss/cli, basecoat-css, unpoly, alpinejs, @alpinejs/morph in package.json + package-lock.json. verify: `npm ls --depth=0` lists 6, no errors
3. Apps + middleware wired, unicorn URLs routed, `UNICORN` setting (alpine morpher, `APPS` = project app). verify: `uv run python manage.py shell -c "from django.conf import settings as s; from django.urls import reverse; print(all(a in s.INSTALLED_APPS for a in ['django_unicorn','django_cotton','django_basecoat']), [m for m in s.MIDDLEWARE if 'npoly' in m], reverse('django_unicorn:message'), s.UNICORN)"` -> True, unpoly middleware, `/unicorn/message`, alpine
4. Base layout: built Tailwind css, Unpoly JS+CSS, Basecoat JS, Alpine + morph plugin from npm (one Alpine only), `{% unicorn_scripts %}` once in `<head>`, `up-main`, Unpoly sends CSRF, `{% csrf_token %}` input inside `<main>` for unicorn. verify: `just run`; every `/static/` css/js linked from `curl -s localhost:8000/` returns 200; test asserts unicorn script once, one `csrfmiddlewaretoken`
5. Home `/` renders through a project cotton component and a django-basecoat component. verify: a test asserts both markers
6. Unpoly server protocol live. verify: `curl -s -D- -o/dev/null -H 'X-Up-Version: 3' -H 'X-Up-Target: main' localhost:8000/ | grep -i x-up-method`
7. Tailwind v4 build output has classes from django-basecoat templates, basecoat-css and unicorn component templates. verify: `just css`, then built css has `animate-spin` (from `<c-spinner>`), `.btn-outline`, and a utility used only in the demo unicorn template
8. Settings read DB + Redis from env, `.env` loaded by default, real env wins. Host, port, user match `$SJ`, db name `<pkg>`. Empty DB var -> sqlite, empty redis host -> in-memory. verify: `uv run python manage.py shell -c "from django.conf import settings as s; from urllib.parse import urlsplit as u; d=s.DATABASES['default']; r=u(s.CACHES['default']['LOCATION']); print(d['HOST'], d['PORT'], d['USER'], d['NAME'], r.hostname, r.port)"` vs `jq '.postgres.host,.postgres.port,.postgres.username,.redis.host,.redis.port' $SJ`
9. Passwords only in `.env`, mode 600, written from `$SJ` without echo. Never cat, print, commit. `.env.example` = key names only. verify: `stat -c %a .env` = 600; `grep -c '=.' .env.example` = 0
10. `.gitignore` covers .env, node_modules, .venv, db.sqlite3, built css, vendored JS. verify: `git init -q -b main && git check-ignore --no-index <each path> | wc -l` = count
11. `uv run python manage.py check` -> `no issues`.
12. justfile has run, test, migrate (+ setup, css). `just test` builds what tests need. verify: `just --summary`; `POSTGRES_DB= REDIS_HOST= just test` -> all passed
13. AGENTS.md: stack, commands, layout, component ladder. README.md: title, one_liner, run steps. verify: `grep -nE '\.bootstrap|artifacts' AGENTS.md README.md` empty
14. No unused template leftovers (docs/sphinx, readthedocs, utility/, docker, celery, Bootstrap CSS, crispy). verify: `ls docs utility .readthedocs.yml docker-compose*.yml 2>/dev/null` empty; `grep -rliE 'bootstrap5|bootstrap\.min|crispy|celery' --exclude-dir=.venv --exclude-dir=node_modules .` empty
15. Lint + types gate: pre-commit hooks installed, every hook passes, no hooks for removed parts. verify: `git init -q -b main && git add -A && uv run pre-commit install && uv run pre-commit run --all-files` exit 0 (rerun once after autofix); `uv run mypy <pkg>` -> no issues
16. Coverage: `just test` runs pytest under coverage + report, `fail_under = 80` in pyproject. Reached by real tests (pages, components, settings), `omit` only migrations + tests. verify: `POSTGRES_DB= REDIS_HOST= just test` TOTAL >= 80; `uv run coverage report --fail-under=100` exits non-zero
17. Dark mode light/dark/system: `<html data-theme>` set by inline `<head>` script before first stylesheet (no flash), choice in localStorage via Alpine store, Tailwind `dark:` follows `data-theme`, Basecoat dark palette follows too, toggle component on every page. verify: test asserts script before stylesheet + 3 choices; built css has `where([data-theme=dark]` and no `:is(.dark *)`
18. Unpoly/Alpine glue: `app.js` loads `defer` before Alpine, registers stores in `alpine:init`, `Alpine.initTree` on `up:fragment:inserted`, page scripts via `up.compiler()` returning cleanup, Unpoly cache evicted when a unicorn component is inserted. Modal page opened by `up-href` + `up-layer="new"`, full document with `<main up-main>`. verify: test asserts app.js before alpinejs, `up-layer="new"` on home, modal URL 200; headless Chrome if present: Alpine + unicorn demo react after an Unpoly swap of `main`, inside the modal, after history back; Alpine state inside the component survives a re-render; one Alpine script; theme toggles. No browser: say not verified
19. AGENTS.md also: component ladder basecoat -> cotton -> alpine -> unicorn, unicorn bounded: only when Unpoly + Alpine cannot do it simply (live server state, many interdependent fields, polling-heavy UIs), its endpoint returns JSON; demo component named as the example; every django-basecoat component (from the package `templates/cotton/`, not memory), Unpoly/Alpine/unicorn/theme rules, `@theme` tokens named by function, rules: no hand-written migrations, no `# noqa`, no narrating comments, lint + test before commit. verify: each `ls <site-packages>/django_basecoat/templates/cotton/*.html` name (`_` -> `-`) greps in AGENTS.md; `grep -ciE 'migrations by hand|noqa|narrate|lint' AGENTS.md` >= 4; `grep -cE 'unicorn.*JSON|JSON.*unicorn' AGENTS.md` >= 1; demo component file name greps; 13 still empty
20. Templates: `cotton/ layouts/ partials/ pages/ unicorn/` (+ error pages, app overrides), no root `base.html`. Pages render. verify: `just run`; `/`, `/about/`, each project page -> 200, `grep -cE '\{\{|\{%|<c-[a-z]|TemplateSyntaxError'` = 0
21. Hygiene: no `ATOMIC_REQUESTS`, python-slugify gone, `.venv` built at `$R`, deploy check clean. verify: `grep -r ATOMIC_REQUESTS config` + `grep slugify pyproject.toml` empty; `head -1 .venv/bin/pytest` starts `#!$R/.venv/`; `env -i PATH=$PATH HOME=$HOME DJANGO_READ_DOT_ENV_FILE=False DJANGO_SETTINGS_MODULE=config.settings.production DJANGO_SECRET_KEY=<random 50> DJANGO_ADMIN_URL=x/ uv run python manage.py check --deploy` -> no issues
22. `just superuser` = `createsuperuser --noinput` from `.env` `DJANGO_SUPERUSER_EMAIL` (= `<email>`) + generated `DJANGO_SUPERUSER_PASSWORD` (keys in `.env.example`). Never printed, not run by bootstrap. verify: `grep -c '^DJANGO_SUPERUSER_\(EMAIL\|PASSWORD\)=.' .env` = 2; on throwaway sqlite (`POSTGRES_DB= REDIS_HOST= just migrate superuser`, then `rm db.sqlite3`) output `grep -cFf <(sed -n 's/^DJANGO_SUPERUSER_PASSWORD=//p' .env)` = 0
23. django-unicorn demo: one clearly named component (e.g. `live-counter`: `core/components/live_counter.py` + `templates/unicorn/live-counter.html`) on a secondary page (the modal page of 18), not home. verify: a test GETs that page, POSTs a callMethod to `/unicorn/message/<name>` -> 200, new state in `data` and `dom`

## hints
All verified 2026-10-11 (cookiecutter-django 4b9d477, Python 3.14.0), may be stale, re-check.
- basecoat-css 1.x default bundle lacks 0.x classes django-basecoat 0.2.0 emits (`btn-outline`, `alert-destructive`). 0.3.x works. 1.x `basecoat-css/compat` export untested.
- Tailwind skips gitignored `.venv`: needs `@source` to django_basecoat templates. Glob `lib/*/site-packages` matched nothing; literal `lib/python3.X/site-packages` works, X = venv python. Project `templates/unicorn/` found without `@source`.
- Template `base.py` reads `.env` only if `DJANGO_READ_DOT_ENV_FILE`, has no sqlite fallback, `.gitignore` lacks `.env`.
- sites migration 0003 runs postgres-only sequence SQL: sqlite tests fail until guarded on `connection.vendor`.
- Template ships Bootstrap CDN in `base.html`, crispy in allauth element templates + user form: restyle with Basecoat.
- pytest-django: page tests need `django_db` mark (session, allauth).
- Template pins `requires-python ==3.14.*`; post-gen hook runs `uv` (downloads python, locks, no `.venv`). Run ~10-20s. Slow PyPI can stall `uv add` on lxml download: kill, `uv sync` resumes.
- pre-commit `--all-files` sees only files git knows: `git add -A` first. djlint + ruff-format rewrite on first run. Ruff in tests: `HTTPStatus.OK` (PLR2004), generated secrets (S106). Template's own `# noqa` lines stay.
- Basecoat 0.3 dark = `.dark` class + `@custom-variant dark (&:is(.dark *))`. Own `@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *))` after `@import "basecoat-css"` wins, also in Basecoat's `@apply dark:`. Token block stays on `.dark`: theme script sets `data-theme` and `.dark`.
- Unpoly 3 modal box is element `up-modal-box`, not a class; unpoly.css paints it white: link unpoly css before app.css, style `up-modal-box`.
- Alpine from npm: vendor `alpinejs/dist/cdn.min.js` + `@alpinejs/morph/dist/cdn.min.js`, all `defer` in order app.js -> morph -> alpine. Auto-starts; `initTree` on `up:fragment:inserted` does not double-init.
- Cotton in tests: `engines["django"].from_string('{% load cotton %}{% cotton name a="b" %}{% endcotton %}')`. `<c-x>` in from_string not compiled; `django_cotton.utils.render_component` crashes with template debug on.
- Settings tests: `importlib.reload(config.settings.base)` with `DJANGO_READ_DOT_ENV_FILE=False`, reload again on teardown.
- `.env` read puts keys in `os.environ`: `DJANGO_SUPERUSER_*` breaks template `test_createsuperuser_command`. Autouse conftest fixture `delenv`s them.
- `.venv` made before `mv`: scripts keep old shebang, `uv run pytest` silently runs another pytest from PATH. Plain `uv sync` keeps them; `uv sync --reinstall` fixes.
- `check --deploy`: needs only `DJANGO_SECRET_KEY`, `DJANGO_ADMIN_URL` (allowed hosts default example.com).
- No `unpoly_mixins.py`: only TemplateView pages, `unpoly` middleware covers protocol. Add with first form/overlay view.
Added 2026-10-11 (django-unicorn 0.67.0, lxml 6.1.3, orjson 3.13.0, Alpine + morph 3.17.4, unpoly 3.14.3), may be stale, re-check:
- Python 3.14.0 works for the whole stack incl. django-unicorn: check, tests, mypy, pre-commit, deploy check, browser. Keep template pin.
- unicorn JS reads CSRF from cookie, else first `csrfmiddlewaretoken` input. Template sets `CSRF_COOKIE_HTTPONLY = True`: put `{% csrf_token %}` inside `<main up-main>` (fresh on every swap), else `CSRF token is missing`.
- 0.67 inits components from `unicorn:id` attrs via MutationObserver, no inline init script: works in Unpoly swaps + modals as is.
- Unpoly cache replays page HTML with the same `unicorn:id`; unicorn store keeps the old component bound to the detached root: clicks dead (modal of a page visited <15s before, history back). Fix: `up.compiler("[unicorn\\:id]", () => up.cache.evict("*"))`.
- Default morpher morphdom wipes Alpine state inside components. `UNICORN = {"MORPHER": {"NAME": "alpine"}, "APPS": ["<pkg>.core"]}` + morph plugin before Alpine keeps it (proved in browser).
- `{% unicorn_scripts %}` once in `<head>`: DEBUG -> ES modules, else classic `unicorn.min.js` with global `const url` (twice = redeclare error). Both builds proved in browser.
- `{% unicorn 'live-counter' %}` -> `<app>.components.live_counter.LiveCounterView`, template `unicorn/live-counter.html`. Root attrs: `unicorn:data='{"count":0}'` single-quoted.
- Round trip test, no plugin or pytest config: GET page, regex `unicorn:(id|data|meta)=(["'])(.*?)\2`, POST JSON `{"id","data","meta":"<checksum>::1","actionQueue":[{"type":"callMethod","payload":{"name":"increment"}}]}` to `/unicorn/message/<name>`; response `data` + `dom`. Unit: `LiveCounterView(component_id="t1", component_name="live-counter")`.
- No `py.typed`: `UnicornView` is Any to mypy; template `ignore_missing_imports` keeps mypy clean without ignores. Component state cached in `default` cache (Redis, or locmem when `REDIS_HOST=`).

## versions
Current compatible releases. Pin only where a hint says a version is bad. Resolved versions live in `uv.lock`, `package-lock.json`.

## db
Password only via env, never echoed. `SJ=<repo-root>/.bootstrap/setup.json`:
`PGPASSWORD="$(jq -r .postgres.password $SJ)" psql -h "$(jq -r .postgres.host $SJ)" -p "$(jq -r .postgres.port $SJ)" -U "$(jq -r .postgres.username $SJ)" -d postgres -tAc "select 1 from pg_database where datname='<pkg>'"`
Same with `-c 'CREATE DATABASE "<pkg>"'`. Then `just migrate` -> all OK, `just test` passes on postgres (role has CREATEDB).

## prototype -> app (later, not bootstrap)
html-prototype is throwaway. `<!-- c-component: x -->` blocks -> `templates/cotton/x.html`. `<!-- unicorn: x -->` blocks -> unicorn component `x` (Alpine fake dropped). `<!-- server: for ... -->` -> view context. `up-*` attrs carry over. Prototype tokens -> `@theme {}` in Tailwind input css.
