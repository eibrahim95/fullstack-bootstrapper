# stack: django+unpoly
Django + django-cotton + django-basecoat + Unpoly + Alpine.js + Tetra + Tailwind CSS v4.
Server owns page. Unpoly swaps fragments. Alpine local state. Tetra only server-backed widgets.
Base = cookiecutter-django output, adapted by agent. Needs cookiecutter, uv, just, node/npm. Network: GitHub, PyPI, npm.
Vars: `<title>`, `<one_liner>`, `<slug>` from status.json. `<pkg>` = slug, `-` -> `_`. `<login>`, `<email>` = `$SJ` github. `$R` = `<parent>/<slug>`.

## source
Temp config keeps user's `~/.cookiecutters` and `~/.cookiecutter_replay` untouched:
`T=$(mktemp -d) && printf 'cookiecutters_dir: %s/c\nreplay_dir: %s/r\n' $T $T > $T/c.yaml`
`cookiecutter --config-file $T/c.yaml --no-input -o <parent> https://github.com/cookiecutter/cookiecutter-django project_name="<title>" project_slug=<pkg> description="<one_liner>" author_name="<login>" email=<email> domain_name=example.com open_source_license="Not open source" username_type=email use_docker=n postgresql_version=18 cloud_provider=None mail_service="Other SMTP" rest_api=None use_async=n frontend_pipeline=None use_celery=n mail_catcher=None use_sentry=n use_whitenoise=y use_heroku=n ci_tool=None keep_local_envs_in_vcs=n editor=None debug=n`
Then `mv <parent>/<pkg> $R` if names differ. GitHub unreachable: template = `~/.cookiecutters/cookiecutter-django` if present, say so.
Why:
- use_docker=n: postgres/redis are local, from /setup.
- use_celery=n, use_async=n: no workers; non-reactive Tetra runs on WSGI.
- cloud_provider=None + use_whitenoise=y: template refuses None without whitenoise.
- mail_service="Other SMTP": no None choice; plain SMTP, no vendor.
- frontend_pipeline=None: Tailwind, Basecoat, Unpoly come from npm here.
- rest_api, sentry, heroku, ci, editor off: not in stack. keep_local_envs_in_vcs=n: secrets only in `.env`.
- Postgres always on (template has no switch). username_type=email, private license: user's past choices.

## goals
End state. How = agent's call. Run in `$R`. Before db exists prefix tests with `POSTGRES_DB= REDIS_HOST=`.
1. Python deps django, django-cotton, django-basecoat, tetra, channels, unpoly in pyproject + uv.lock. verify: `uv pip list | grep -ciE '^(django|django-cotton|django-basecoat|tetra|channels|unpoly) '` = 6
2. npm deps tailwindcss, @tailwindcss/cli, basecoat-css, unpoly, esbuild in package.json + package-lock.json. verify: `npm ls --depth=0` lists 5, no errors
3. Apps + middleware wired, `__tetra__/` routed. verify: `uv run python manage.py shell -c "from django.conf import settings as s; print(all(a in s.INSTALLED_APPS for a in ['tetra','django_cotton','django_basecoat']), [m for m in s.MIDDLEWARE if 'npoly' in m or 'etra' in m])"` -> True + both
4. Base layout: built Tailwind css, Unpoly JS+CSS, Basecoat JS, Tetra styles/scripts with Alpine (one Alpine only), `up-main`, Unpoly sends CSRF. verify: `just run`; every `/static/` css/js linked from `curl -s localhost:8000/` returns 200
5. Home `/` renders through a project cotton component, a django-basecoat component, a Tetra component. verify: a test asserts all three markers
6. Unpoly server protocol live. verify: `curl -s -D- -o/dev/null -H 'X-Up-Version: 3' -H 'X-Up-Target: main' localhost:8000/ | grep -i x-up-method`
7. Tailwind v4 build output has classes from django-basecoat templates and basecoat-css. verify: `just css`, then built css has `animate-spin` (from `<c-spinner>`) and `.btn-outline`
8. Settings read DB + Redis from env, `.env` loaded by default, real env wins. Host, port, user match `$SJ`, db name `<pkg>`. Empty DB var -> sqlite, empty redis host -> in-memory. verify: `uv run python manage.py shell -c "from django.conf import settings as s; from urllib.parse import urlsplit as u; d=s.DATABASES['default']; r=u(s.CACHES['default']['LOCATION']); print(d['HOST'], d['PORT'], d['USER'], d['NAME'], r.hostname, r.port)"` vs `jq '.postgres.host,.postgres.port,.postgres.username,.redis.host,.redis.port' $SJ`
9. Passwords only in `.env`, mode 600, written from `$SJ` without echo. Never cat, print, commit. `.env.example` = key names only. verify: `stat -c %a .env` = 600; `grep -c '=.' .env.example` = 0
10. `.gitignore` covers .env, node_modules, .venv, db.sqlite3, built css, vendored JS, tetra build output. verify: `git init -q -b main && git check-ignore --no-index <each path> | wc -l` = count
11. `uv run python manage.py check` -> `no issues`.
12. justfile has run, test, migrate (+ setup, css). `just test` builds what tests need. verify: `just --summary`; `POSTGRES_DB= REDIS_HOST= just test` -> all passed
13. AGENTS.md: stack, commands, layout, component ladder. README.md: title, one_liner, run steps. verify: `grep -nE '\.bootstrap|artifacts' AGENTS.md README.md` empty
14. No unused template leftovers (docs/sphinx, readthedocs, utility/, docker, celery, Bootstrap CSS, crispy). verify: `ls docs utility .readthedocs.yml docker-compose*.yml 2>/dev/null` empty; `grep -rliE 'bootstrap5|bootstrap\.min|crispy|celery' --exclude-dir=.venv --exclude-dir=node_modules .` empty

## hints
All verified 2026-10-11 (cookiecutter-django 4b9d477, Python 3.14), may be stale, re-check.
- tetra 0.9.x (0.9.2 too) wheel misses `components/default/link/link.html`: `manage.py check` -> `Link is not a valid component`. 0.8.5 works.
- tetra imports channels, does not declare it. Needs `TETRA_ESBUILD_PATH` = `node_modules/.bin/esbuild`.
- `local.py` puts `whitenoise.runserver_nostatic` first; tetra overrides runserver too -> RecursionError on `runserver`. tetra must come before it.
- basecoat-css 1.x default bundle lacks 0.x classes django-basecoat 0.2.0 emits (`btn-outline`, `alert-destructive`). 0.3.x works. 1.x `basecoat-css/compat` export untested.
- Tailwind skips gitignored `.venv`: needs `@source` to django_basecoat templates. Glob `lib/*/site-packages` matched nothing; literal `lib/python3.14/site-packages` worked.
- `tetrabuild` before tests.
- Template `base.py` reads `.env` only if `DJANGO_READ_DOT_ENV_FILE`, has no sqlite fallback, `.gitignore` lacks `.env`.
- sites migration 0003 runs postgres-only sequence SQL: sqlite tests fail until guarded on `connection.vendor`.
- Template ships Bootstrap CDN in `base.html`, crispy in allauth element templates + user form: restyle with Basecoat.
- pytest-django: home test needs `django_db` mark (session, allauth).
- Template pins `requires-python ==3.14.*`; post-gen hook runs `uv` (downloads python, locks). Run ~20s.

## versions
Current compatible releases. Pin only where a hint says a version is bad. Resolved versions live in `uv.lock`, `package-lock.json`.

## db
Password only via env, never echoed. `SJ=<repo-root>/.bootstrap/setup.json`:
`PGPASSWORD="$(jq -r .postgres.password $SJ)" psql -h "$(jq -r .postgres.host $SJ)" -p "$(jq -r .postgres.port $SJ)" -U "$(jq -r .postgres.username $SJ)" -d postgres -tAc "select 1 from pg_database where datname='<pkg>'"`
Same with `-c 'CREATE DATABASE "<pkg>"'`. Then `just migrate` -> all OK, `just test` passes on postgres (role has CREATEDB).

## prototype -> app (later, not bootstrap)
html-prototype is throwaway. `<!-- c-component: x -->` blocks -> `templates/cotton/x.html`. `<!-- server: for ... -->` -> view context. `up-*` attrs carry over. Prototype tokens -> `@theme {}` in Tailwind input css.
