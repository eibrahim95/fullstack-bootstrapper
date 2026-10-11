# stack: django+unpoly
Django (ASGI) + Celery + Channels + django-cotton + django-basecoat + Unpoly + Alpine.js + django-unicorn + Tailwind CSS v4, GCP-ready.
Server owns page. Unpoly swaps fragments. Alpine local state. django-unicorn only for high-interactivity parts. Celery = task queue, Channels = websockets, both on the one Redis.
Base = cookiecutter-django output, adapted by agent. Needs cookiecutter, uv, just, node/npm, running Docker daemon. Network: GitHub, PyPI, npm, Docker Hub.
Vars: `<title>`, `<one_liner>`, `<slug>` from status.json. `<pkg>` = slug, `-` -> `_`. `$R` = `<parent>/<slug>`. `<x>` below = answer to input x.

## inputs
Asked in bootstrap step 2 batch, one round, recommended answer each. Supplied as `key=value` in call: use, never ask. Supplied call missing one without default: report failed prereq.
| key | cookiecutter option | recommend |
|---|---|---|
| description | description | `<one_liner>` |
| author | author_name | `$SJ` github.login |
| email | email | `$SJ` github.email |
| domain | domain_name | none, always ask (e.g. `example.com`) |
| license | open_source_license | `Not open source`. Choices MIT, BSD, GPLv3, Apache Software License 2.0, Not open source |
| username | username_type | `email`. Choices username, email |
| pg | postgresql_version | major of `$SJ` postgres server (`show server_version`), must be 18/17/16/15/14 |
| mail | mail_service | `Other SMTP`. Choices Mailgun, Amazon SES, Mailjet, Mandrill, Postmark, Sendgrid, Brevo, SparkPost, Other SMTP |
| api | rest_api | `None` unless spec needs an API. Choices None, DRF, Django Ninja |
| ci | ci_tool | `Github`. Choices None, Travis, Gitlab, Github, Drone |

## source
`docker info` fails: stop, say run `/ensure-runnable-docker`, report failed prereq. Post-gen hook runs `uv` in a Docker image.
Temp config keeps user's `~/.cookiecutters` and `~/.cookiecutter_replay` untouched:
`T=$(mktemp -d) && printf 'cookiecutters_dir: %s/c\nreplay_dir: %s/r\n' $T $T > $T/c.yaml`
`cookiecutter --config-file $T/c.yaml --no-input -o <parent> https://github.com/cookiecutter/cookiecutter-django project_name="<title>" project_slug=<pkg> description="<description>" author_name="<author>" email=<email> domain_name=<domain> open_source_license="<license>" username_type=<username> postgresql_version=<pg> mail_service="<mail>" rest_api="<api>" ci_tool=<ci> use_docker=y use_async=y use_celery=y cloud_provider=GCP use_whitenoise=y frontend_pipeline=None mail_catcher=None use_sentry=n use_heroku=n keep_local_envs_in_vcs=n editor=None debug=n`
Then `mv <parent>/<pkg> $R` if names differ. `.venv` made before the `mv`: delete it, `uv sync` at `$R`. GitHub unreachable: template = `~/.cookiecutters/cookiecutter-django` if present, say so.
Pinned, never asked:
- use_docker=y: generates production Dockerfile, start scripts, compose files, justfile. Local dev still runs on host (`.venv`, justfile).
- use_async=y: ASGI app (uvicorn). Channels routes websockets.
- use_celery=y: Celery worker + beat on Redis.
- cloud_provider=GCP: media on GCS via django-storages. use_whitenoise=y: static from the container.
- frontend_pipeline=None: Tailwind, Basecoat, Unpoly come from npm here.
- sentry, heroku, editor, mail_catcher off. keep_local_envs_in_vcs=n: secrets only in `.env`.
- Postgres always on (template has no switch).

## docker policy
| generated | action |
|---|---|
| `docker-compose.local.yml`, `docker-compose.docs.yml`, `compose/local/`, `.devcontainer/` | keep, untouched. Unused locally, a teammate may use them |
| `docker-compose.production.yml`, `compose/production/traefik/`, `compose/production/postgres/` | keep as reference |
| `compose/production/django/` (Dockerfile, `start`, celery scripts) | keep. Deploy step adapts it for Cloud Run later, not bootstrap |
| justfile compose recipes | keep, add host recipes beside them |

## goals
End state. How = agent's call. Run in `$R`. Tests always run on `config.settings.test` (sqlite, no Postgres or Redis needed). Goals that start the app (`just run`/`just asgi`/`just worker`) need the db created and migrated: db skipped -> those checks not verified.
1. Python deps django, django-cotton, django-basecoat, django-unicorn, unpoly, celery, channels, channels-redis, django-storages, uvicorn in pyproject + uv.lock. Python = template pin. verify: `uv pip list | grep -ciE '^(django|django-cotton|django-basecoat|django-unicorn|unpoly|celery|channels|channels-redis|django-storages|uvicorn) '` = 10; `.venv/bin/python -V` matches `requires-python`
2. npm deps tailwindcss, @tailwindcss/cli, basecoat-css, unpoly, alpinejs, @alpinejs/morph in package.json + package-lock.json. verify: `npm ls --depth=0` lists 6, no errors
3. Apps + middleware wired, unicorn URLs routed, `UNICORN` setting (alpine morpher, `APPS` = project app), `channels` app, `ASGI_APPLICATION = "config.asgi.application"`, `CHANNEL_LAYERS` = `channels_redis.core.RedisChannelLayer` with hosts from `REDIS_URL`. verify: `uv run python manage.py shell -c "from django.conf import settings as s; from django.urls import reverse; print(all(a in s.INSTALLED_APPS for a in ['django_unicorn','django_cotton','django_basecoat','channels']), [m for m in s.MIDDLEWARE if 'npoly' in m], reverse('django_unicorn:message'), s.UNICORN, s.ASGI_APPLICATION, s.CHANNEL_LAYERS['default']['BACKEND'])"` -> True, unpoly middleware, `/unicorn/message`, alpine, asgi, RedisChannelLayer
4. Base layout: built Tailwind css, Unpoly JS+CSS, Basecoat JS, Alpine + morph plugin from npm (one Alpine only), `{% unicorn_scripts %}` once in `<head>`, `up-main`, Unpoly sends CSRF, `{% csrf_token %}` input inside `<main>` for unicorn. verify: `just run`; every `/static/` css/js linked from `curl -s localhost:8000/` returns 200; test asserts unicorn script once, one `csrfmiddlewaretoken`
5. Home `/` renders through one project cotton component holding a django-basecoat button, card and dropdown menu, plus one Tailwind class. verify: a test asserts the component and the three Basecoat markers
6. Unpoly server protocol live. verify: `curl -s -D- -o/dev/null -H 'X-Up-Version: 3' -H 'X-Up-Target: main' localhost:8000/ | grep -i x-up-method`
7. Tailwind v4 build output has classes from django-basecoat templates, basecoat-css and unicorn component templates. verify: `just css`, then built css has `animate-spin` (from `<c-spinner>`), `.btn-outline`, and a utility used only in the demo unicorn template
8. Settings read DB + Redis from env, `.env` loaded by default, real env wins. Host, port, user match `$SJ`, db name `<pkg>`. No sqlite fallback: DB env missing -> settings error. `config/settings/test.py` hardcodes sqlite (`{"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}`, `BASE_DIR` imported explicitly, no `# noqa`), plus locmem cache, `InMemoryChannelLayer`, Celery eager. verify: `uv run python manage.py shell -c "from django.conf import settings as s; from urllib.parse import urlsplit as u; d=s.DATABASES['default']; r=u(s.CACHES['default']['LOCATION']); print(d['HOST'], d['PORT'], d['USER'], d['NAME'], r.hostname, r.port)"` vs `jq '.postgres.host,.postgres.port,.postgres.username,.redis.host,.redis.port' $SJ`; `env -i PATH=$PATH HOME=$HOME DJANGO_READ_DOT_ENV_FILE=False uv run python manage.py check` fails on the DB env (no sqlite); `DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py shell -c "from django.conf import settings as s; print(s.DATABASES['default']['ENGINE'], s.CHANNEL_LAYERS['default']['BACKEND'], s.CELERY_TASK_ALWAYS_EAGER)"` -> sqlite3, InMemoryChannelLayer, True
9. Passwords only in `.env`, mode 600, written from `$SJ` without echo. Never cat, print, commit. `.env.example` = key names only. verify: `stat -c %a .env` = 600; `grep -c '=.' .env.example` = 0
10. `.gitignore` covers .env, node_modules, .venv, db.sqlite3, vendored JS. Built tailwind css NOT ignored (committed, see 26). verify: `git init -q -b main && git check-ignore --no-index <each path> | wc -l` = count; `git check-ignore --no-index <built css>` exits 1
11. `uv run python manage.py check` -> `no issues`.
12. justfile keeps compose recipes, adds host ones: run (runserver), asgi (`uv run uvicorn config.asgi:application --reload`, serves websockets), worker + beat (`uv run celery -A config.celery_app ...`, not compose), css + css-watch, test, migrate, setup. `just test` builds what tests need. verify: `just --summary` has all; `DATABASE_URL=postgres://x@127.0.0.1:1/x REDIS_URL=redis://127.0.0.1:1/0 just test` -> all passed (tests touch no Postgres or Redis)
13. AGENTS.md: stack, commands, layout, component ladder. README.md: title, one_liner, run steps (Postgres + Redis on host, then run/asgi/worker/beat/css-watch). verify: `grep -nE '\.bootstrap|artifacts' AGENTS.md README.md` empty
14. No Bootstrap CSS or crispy leftovers; generated docker, compose, celery, docs files kept (docker policy). verify: `grep -rliE 'bootstrap5|bootstrap\.min|crispy' --exclude-dir=.venv --exclude-dir=node_modules .` empty; `ls justfile compose/production/django/Dockerfile compose/production/django/start docker-compose.local.yml` all exist
15. Lint + types gate: pre-commit hooks installed, every hook passes. verify: `git init -q -b main && git add -A && uv run pre-commit install && uv run pre-commit run --all-files` exit 0 (rerun once after autofix); `uv run mypy <pkg>` -> no issues
16. Coverage: `just test` runs pytest under coverage + report, `fail_under = 80` in pyproject. Reached by real tests (pages, components, settings, task, consumer), `omit` only migrations + tests. verify: `just test` TOTAL >= 80; `uv run coverage report --fail-under=100` exits non-zero
17. Dark mode light/dark/system: `<html data-theme>` set by inline `<head>` script before first stylesheet (no flash), choice in localStorage via Alpine store, Tailwind `dark:` follows `data-theme`, `color-scheme` on `:root` matches, Basecoat dark palette follows too, toggle component on every page. verify: test asserts script before stylesheet + 3 choices; built css has `where([data-theme=dark]`, `color-scheme`, no `:is(.dark *)`
18. Unpoly/Alpine glue: `app.js` loads `defer` before Alpine, registers stores in `alpine:init`, `Alpine.initTree` on `up:fragment:inserted`, page scripts and Basecoat widget re-binding via `up.compiler()` returning cleanup, no `showModal()` inside a layer, Unpoly cache evicted when a unicorn component is inserted. Every URL returns a full document, no fragment-only responses. Modal page opened by one `<c-button up-href up-follow up-layer="new">` (no button inside `<a>`), full document with `<main up-main>`, modal box is the only frame (no card inside, background from surface token). verify: test asserts app.js before alpinejs, `up-layer="new"` on home, no `<a>` wrapping a button, modal URL 200; headless Chrome if present: Alpine + unicorn demo + Basecoat dropdown react after an Unpoly swap of `main`, inside the modal, after history back; Alpine state inside the component survives a re-render; one Alpine script; theme toggles. No browser: say not verified
19. AGENTS.md also: component ladder basecoat -> cotton -> alpine -> unicorn, unicorn bounded: only when Unpoly + Alpine cannot do it simply (live server state, many interdependent fields, polling-heavy UIs), its endpoint returns JSON; demo component named as the example; no second component library, never hand-roll what Basecoat ships; every django-basecoat component (from the package `templates/cotton/`, not memory), Unpoly/Alpine/unicorn/theme rules, Celery for background work, Channels for websockets (`just asgi` to serve them), `@theme` tokens named by function, rules: no hand-written migrations, no `# noqa`, no narrating comments, no commit trailers, rebuild and commit tailwind css after template or CSS change, lint + test before commit. verify: each `ls <site-packages>/django_basecoat/templates/cotton/*.html` name (`_` -> `-`) greps in AGENTS.md; `grep -ciE 'migrations by hand|noqa|narrat|trailer|lint|tailwind' AGENTS.md` >= 6; `grep -cE 'unicorn.*JSON|JSON.*unicorn' AGENTS.md` >= 1; demo component file name greps; 13 still empty
20. Templates: `cotton/ layouts/ partials/ pages/ unicorn/` (+ error pages, app overrides), no root `base.html`. Pages render. verify: `just run`; `/`, `/about/`, each project page -> 200, `grep -cE '\{\{|\{%|<c-[a-z]|TemplateSyntaxError'` = 0
21. Hygiene: no `ATOMIC_REQUESTS`, python-slugify gone, `USE_DOCKER` defaults False in `config/settings/local.py`, `.venv` built at `$R`, deploy check clean. verify: `grep -r ATOMIC_REQUESTS config` + `grep slugify pyproject.toml` empty; `grep -n USE_DOCKER config/settings/local.py` shows default False; `head -1 .venv/bin/pytest` starts `#!$R/.venv/`; `env -i PATH=$PATH HOME=$HOME DJANGO_READ_DOT_ENV_FILE=False DJANGO_SETTINGS_MODULE=config.settings.production DJANGO_SECRET_KEY=<random 50> DJANGO_ADMIN_URL=x/ DATABASE_URL=postgres://x@127.0.0.1/x REDIS_URL=redis://127.0.0.1:6379/0 <each other key production.py reads without default, dummy value> uv run python manage.py check --deploy` -> no issues
22. `just superuser` = `createsuperuser --noinput` from `.env` `DJANGO_SUPERUSER_EMAIL` (= `<email>`) + generated `DJANGO_SUPERUSER_PASSWORD` (keys in `.env.example`). Never printed, not run by bootstrap. verify: `grep -c '^DJANGO_SUPERUSER_\(EMAIL\|PASSWORD\)=.' .env` = 2; on throwaway sqlite (`DJANGO_SETTINGS_MODULE=config.settings.test` migrate + superuser, then `rm db.sqlite3`) output `grep -cFf <(sed -n 's/^DJANGO_SUPERUSER_PASSWORD=//p' .env)` = 0
23. django-unicorn demo: one clearly named component (e.g. `live-counter`: `core/components/live_counter.py` + `templates/unicorn/live-counter.html`) on a secondary page (the modal page of 18), not home. verify: a test GETs that page, POSTs a callMethod to `/unicorn/message/<name>` -> 200, new state in `data` and `dom`; browser click works under `just asgi` too
24. Celery: trivial task `ping` -> `"pong"`. verify: test runs it eagerly; `just worker` boots against `$SJ` Redis and `uv run celery -A config.celery_app call <pkg>...ping` result `pong` (or `inspect ping` replies); `just beat` starts without error
25. Channels: `<pkg>/consumers.py` consumer on `ws/ping/` replies `pong`, routes in `<pkg>/routing.py`, `config/asgi.py` = `ProtocolTypeRouter` (`http` = Django ASGI app, `websocket` = `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(...)))`), generated sys.path + settings lines kept. verify: test with `channels.testing.WebsocketCommunicator` sends, gets `pong`; `just asgi` then a websocket client to `ws://localhost:8000/ws/ping/` gets `pong`
26. Built tailwind css committed. CI (`ci` input) rebuilds it and fails when the committed file is stale: `npm ci`, `uv sync`, `just css`, `git diff --exit-code <built css>`. `ci=None`: no CI, say not verified. verify: CI file has the step; after first commit `just css && git diff --exit-code <built css>` exits 0; Github: `actionlint` if installed, else say not verified

## hints
All verified 2026-10-11 (cookiecutter-django 4b9d477, Python 3.14.0), may be stale, re-check. Verified with use_docker=n, use_async=n, no celery, no GCP: hints touching those may differ now.
- basecoat-css 1.x default bundle lacks 0.x classes django-basecoat 0.2.0 emits (`btn-outline`, `alert-destructive`). 0.3.x works. 1.x `basecoat-css/compat` export untested.
- Tailwind skips gitignored `.venv`: needs `@source` to django_basecoat templates. Glob `lib/*/site-packages` matched nothing; literal `lib/python3.X/site-packages` works, X = venv python. Project `templates/unicorn/` found without `@source`. CI must `uv sync` before `just css` or the build drops Basecoat classes.
- Template `base.py` reads `.env` only if `DJANGO_READ_DOT_ENV_FILE`, `.gitignore` lacks `.env`.
- sites migration 0003 runs postgres-only sequence SQL: sqlite tests fail until guarded (`if created and not is_sqlite`, sqlite from db engine).
- Template ships Bootstrap CDN in `base.html`, crispy in allauth element templates + user form: restyle with Basecoat.
- pytest-django: page tests need `django_db` mark (session, allauth).
- Template pins `requires-python ==3.14.*`. Slow PyPI can stall `uv add` on lxml download: kill, `uv sync` resumes.
- pre-commit `--all-files` sees only files git knows: `git add -A` first. djlint + ruff-format rewrite on first run. Ruff in tests: `HTTPStatus.OK` (PLR2004), generated secrets (S106). Template's own `# noqa` lines stay. test.py star import: import `BASE_DIR` explicitly (F405).
- Basecoat 0.3 dark = `.dark` class + `@custom-variant dark (&:is(.dark *))`. Own `@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *))` after `@import "basecoat-css"` wins, also in Basecoat's `@apply dark:`. Token block stays on `.dark`: theme script sets `data-theme` and `.dark`.
- Unpoly 3 modal box is element `up-modal-box`, not a class; unpoly.css paints it white: link unpoly css before app.css, style `up-modal-box`.
- Alpine from npm: vendor `alpinejs/dist/cdn.min.js` + `@alpinejs/morph/dist/cdn.min.js`, all `defer` in order app.js -> morph -> alpine. Auto-starts; `initTree` on `up:fragment:inserted` does not double-init.
- Cotton in tests: `engines["django"].from_string('{% load cotton %}{% cotton name a="b" %}{% endcotton %}')`. `<c-x>` in from_string not compiled; `django_cotton.utils.render_component` crashes with template debug on.
- Settings tests: `importlib.reload(config.settings.base)` with `DJANGO_READ_DOT_ENV_FILE=False`, reload again on teardown.
- `.env` read puts keys in `os.environ`: `DJANGO_SUPERUSER_*` breaks template `test_createsuperuser_command`. Autouse conftest fixture `delenv`s them.
- `.venv` made before `mv`: scripts keep old shebang, `uv run pytest` silently runs another pytest from PATH. `uv sync --reinstall` fixes.
- `check --deploy` needs `DJANGO_SECRET_KEY`, `DJANGO_ADMIN_URL` plus what production.py reads (GCP: bucket name; mail service keys).
- No `unpoly_mixins.py`: only TemplateView pages, `unpoly` middleware covers protocol. Add with first form/overlay view (form, layer, delete mixins).
Added 2026-10-11 (django-unicorn 0.67.0, lxml 6.1.3, orjson 3.13.0, Alpine + morph 3.17.4, unpoly 3.14.3), may be stale, re-check:
- Python 3.14.0 works for the whole stack incl. django-unicorn: check, tests, mypy, pre-commit, deploy check, browser. Keep template pin.
- unicorn JS reads CSRF from cookie, else first `csrfmiddlewaretoken` input. Template sets `CSRF_COOKIE_HTTPONLY = True`: put `{% csrf_token %}` inside `<main up-main>` (fresh on every swap), else `CSRF token is missing`.
- 0.67 inits components from `unicorn:id` attrs via MutationObserver, no inline init script: works in Unpoly swaps + modals as is.
- Unpoly cache replays page HTML with the same `unicorn:id`; unicorn store keeps the old component bound to the detached root: clicks dead (modal of a page visited <15s before, history back). Fix: `up.compiler("[unicorn\\:id]", () => up.cache.evict("*"))`.
- Default morpher morphdom wipes Alpine state inside components. `UNICORN = {"MORPHER": {"NAME": "alpine"}, "APPS": ["<pkg>.core"]}` + morph plugin before Alpine keeps it (proved in browser).
- `{% unicorn_scripts %}` once in `<head>`: DEBUG -> ES modules, else classic `unicorn.min.js` with global `const url` (twice = redeclare error). Both builds proved in browser.
- `{% unicorn 'live-counter' %}` -> `<app>.components.live_counter.LiveCounterView`, template `unicorn/live-counter.html`. Root attrs: `unicorn:data='{"count":0}'` single-quoted.
- Round trip test, no plugin or pytest config: GET page, regex `unicorn:(id|data|meta)=(["'])(.*?)\2`, POST JSON `{"id","data","meta":"<checksum>::1","actionQueue":[{"type":"callMethod","payload":{"name":"increment"}}]}` to `/unicorn/message/<name>`; response `data` + `dom`. Unit: `LiveCounterView(component_id="t1", component_name="live-counter")`.
- No `py.typed`: `UnicornView` is Any to mypy; template `ignore_missing_imports` keeps mypy clean without ignores. Component state cached in `default` cache (Redis; locmem in test.py).

## versions
Current compatible releases. Pin only where a hint says a version is bad. Resolved versions live in `uv.lock`, `package-lock.json`.

## db
Password only via env, never echoed. `SJ=<repo-root>/.bootstrap/setup.json`:
`PGPASSWORD="$(jq -r .postgres.password $SJ)" psql -h "$(jq -r .postgres.host $SJ)" -p "$(jq -r .postgres.port $SJ)" -U "$(jq -r .postgres.username $SJ)" -d postgres -tAc "select 1 from pg_database where datname='<pkg>'"`
Same with `-c 'CREATE DATABASE "<pkg>"'`. Then `just migrate` on Postgres -> all OK. Tests stay on test.py sqlite.

## prototype -> app (later, not bootstrap)
html-prototype is throwaway. `<!-- c-component: x -->` blocks -> `templates/cotton/x.html`. `<!-- unicorn: x -->` blocks -> unicorn component `x` (Alpine fake dropped). `<!-- server: for ... -->` -> view context. `up-*` attrs carry over. Prototype tokens -> `@theme {}` in Tailwind input css.
