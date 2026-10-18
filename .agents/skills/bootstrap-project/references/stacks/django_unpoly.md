# Stack: django+unpoly
A server-rendered Django app that feels like a single-page app, ready to deploy on Google Cloud.

| part | role |
|---|---|
| Django (ASGI) | routing, data, auth, pages. The server owns every page. |
| Unpoly | swaps page fragments, opens modals, so navigation feels instant |
| django-basecoat + django-cotton | UI components (Basecoat = shadcn/ui look without React) and our own components |
| Alpine.js | small local state in the browser (toggles, theme) |
| django-unicorn | only for highly interactive parts (live server state, many linked fields, polling) |
| Tailwind CSS v4 | styling, built by the standalone Tailwind binary. No Node anywhere. |
| Celery | background tasks |
| Channels | websockets |
| Postgres, Redis | run on the host, from /setup. Redis serves cache, Celery and Channels. |

The base is the output of cookiecutter-django. The agent then adapts it until every goal below passes.
Network: GitHub, PyPI, jsDelivr, Docker Hub.

## Names used below
| name | means |
|---|---|
| `<title>`, `<one_liner>`, `<slug>` | from the project's status.json |
| `<pkg>` | the Python package name: slug with `-` replaced by `_` |
| `<parent>`, repo folder | the parent folder the user chose, and `<parent>/<slug>` |
| setup.json | `.bootstrap/setup.json` in the bootstrapper repo (Postgres, Redis, GitHub account) |
| `<x>` | the answer to input `x` from the table below |

## Tools
| tool | check | fix |
|---|---|---|
| uv | `command -v uv` | `/ensure-installed uv` |
| just | `command -v just` | `/ensure-installed just` |
| curl | `command -v curl` | install curl with the system package manager |
| docker | `docker info` | /ensure-runnable-docker |

## Inputs
| key | cookiecutter option | recommend |
|---|---|---|
| description | description | `<one_liner>` |
| author | author_name | setup.json `github.login` |
| email | email | setup.json `github.email` |
| domain | domain_name | no default, always ask (example: `example.com`) |
| license | open_source_license | `Not open source`. Choices: MIT, BSD, GPLv3, Apache Software License 2.0, Not open source |
| username | username_type | `email`. Choices: username, email |
| pg | postgresql_version | major version of the Postgres server in setup.json (`show server_version`). Must be 18, 17, 16, 15 or 14. |
| mail | mail_service | `Other SMTP`. Choices: Mailgun, Amazon SES, Mailjet, Mandrill, Postmark, Sendgrid, Brevo, SparkPost, Other SMTP |
| api | rest_api | `None`, unless the spec needs an API. Choices: None, DRF, Django Ninja |
| ci | ci_tool | `Github`. Choices: None, Travis, Gitlab, Github, Drone |

## Source: how the repo is generated
1. Docker must run: cookiecutter's post-generation hook resolves the Python dependencies inside a Docker image. On slow PyPI it takes about 5 minutes and is not hung. If `docker info` fails, stop and tell the user to run /ensure-runnable-docker.
2. cookiecutter is not installed: `uvx` runs it in a throwaway environment, so it needs only uv. Use a temporary cookiecutter config, so the user's own `~/.cookiecutters` and `~/.cookiecutter_replay` stay untouched:
   ```
   T=$(mktemp -d) && printf 'cookiecutters_dir: %s/c\nreplay_dir: %s/r\n' $T $T > $T/c.yaml
   ```
3. Generate:
   ```
   uvx cookiecutter --config-file $T/c.yaml --no-input -o <parent> https://github.com/cookiecutter/cookiecutter-django \
     project_name="<title>" project_slug=<pkg> description="<description>" author_name="<author>" email=<email> \
     domain_name=<domain> open_source_license="<license>" username_type=<username> postgresql_version=<pg> \
     mail_service="<mail>" rest_api="<api>" ci_tool=<ci> \
     use_docker=y use_async=y use_celery=y cloud_provider=GCP use_whitenoise=y frontend_pipeline=None \
     mail_catcher=None use_sentry=n use_heroku=n keep_local_envs_in_vcs=n editor=None debug=n
   ```
   If GitHub is unreachable and `~/.cookiecutters/cookiecutter-django` exists, use that copy as the template and say so.
4. Cookiecutter names the folder `<pkg>`. If that differs from the slug, rename it to the repo folder. Then run `uv sync` in the repo folder: the hook writes `uv.lock` but no `.venv`.

Options we fix, and why:
| option | why |
|---|---|
| `use_docker=y` | gives the production Dockerfile, start scripts, compose files and justfile. Local development still runs on the host, not in Docker. |
| `use_async=y` | ASGI app served by uvicorn, so Channels can route websockets |
| `use_celery=y` | Celery worker and beat on Redis |
| `cloud_provider=GCP`, `use_whitenoise=y` | media files on Google Cloud Storage, static files served from the container |
| `frontend_pipeline=None` | no Node pipeline. Tailwind runs as a standalone binary and browser libraries are vendored. |
| `keep_local_envs_in_vcs=n` | secrets live only in `.env`, never in git |
| sentry, heroku, editor, mail_catcher off | not part of this stack |
Postgres is always on; the template has no switch for it.

## What happens to the Docker files
| generated files | what we do |
|---|---|
| `docker-compose.local.yml`, `docker-compose.docs.yml`, `compose/local/`, `.devcontainer/` | keep untouched. We don't use them locally, but a teammate may. |
| `docker-compose.production.yml`, `compose/production/traefik/`, `compose/production/postgres/` | keep as reference |
| `compose/production/django/` (Dockerfile, `start`, Celery scripts) | keep. A later deploy step adapts it for Cloud Run; bootstrap does not. |
| compose recipes in the justfile | keep, and add host recipes next to them |

## Baseline: in the first commit
These go into the first commit on `main`, so its first CI run is green on plain uv, with no Docker. Everything else waits for the Goals branch.
Traps last verified 2026-10-11 with cookiecutter-django 4b9d477, Python 3.14.0, django-unicorn 0.67.0, Unpoly 3.14.3, Alpine 3.17.4, basecoat-css 0.3.11, Tailwind 4.3.3, django-tailwind-cli 4.8.1, Channels 4.3.2.

**B1. CI without Docker.** The template's tests already run on Postgres from the environment; only its CI runs them through Docker Compose. CI (from the `ci` input) keeps the template's linter job, which needs no Docker, and its pytest job runs `uv run pytest` directly on the runner. Every other generated file stays as it is: settings, `pyproject.toml`, migrations. The workflow sets `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` and `POSTGRES_PASSWORD` once, at workflow level, for the runner's Postgres. The pytest job starts that Postgres, installs `libpq-dev`, installs uv and runs pytest; no `makemigrations` or `migrate` step (pytest-django creates `test_<db>` itself). No Docker, compose, `services:` containers or `.env`. If `ci=None`, there is no CI: report this goal as not verified.
```
git diff --stat <generated tree>                                                              # only the CI file
grep -niE 'docker|compose|services:|\.envs' <CI file>                                        # nothing
POSTGRES_HOST="$(jq -r .postgres.host <setup.json>)" POSTGRES_PORT="$(jq -r .postgres.port <setup.json>)" POSTGRES_USER="$(jq -r .postgres.username <setup.json>)" \
  POSTGRES_PASSWORD="$(jq -r .postgres.password <setup.json>)" POSTGRES_DB=<pkg> REDIS_URL=redis://127.0.0.1:1/0 uv run pytest   # the pytest job, run on setup.json's Postgres
```
For GitHub, lint the workflow with `actionlint`, or `docker run --rm -v $PWD:/repo -w /repo rhysd/actionlint` if it is not installed.

Traps:
- GitHub's `ubuntu-latest` image ships PostgreSQL with the service stopped: `sudo systemctl start postgresql.service`, then `sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres'"`, because TCP logins on the runner need a password. Its major version is whatever the image ships, which may differ from the `pg` input.
- The image has no `libpq-dev`, and `uv sync` builds `psycopg[c]` from source: `sudo apt-get update && sudo apt-get install -y libpq-dev` before uv runs.
- `makemigrations --check` loads local settings, which need `USE_DOCKER`; leave it out.

**B2. pre-commit installed.** The git hook is installed and every hook passes on all files.
```
uv run pre-commit install && git add -A && uv run pre-commit run --all-files   # exit 0 (run once more after autofixes)
test -x .git/hooks/pre-commit                                                    # exit 0
```

## Goals
Tests always run on `config.settings.test`: Postgres from `.env`, no Redis. Checks that start the app (`just run`, `just asgi`, `just worker`) need the database created and migrated.
A browser check means using the browser tools available to you, the way a person would: open the page, click, look. Never write a script that drives a browser. With no browser tools, report that goal as not verified.

### Dependencies
**1. Python packages.** `pyproject.toml` and `uv.lock` have django, django-cotton, django-basecoat, django-unicorn, unpoly, celery, channels, channels-redis, django-storages, uvicorn and django-tailwind-cli. Python stays at the template's pinned version.
Every package is added with `uv add <pkg>` (`uv add --dev <pkg>` for dev tools) and removed with `uv remove <pkg>`. Never write a dependency into `pyproject.toml` by hand and never type a version: `uv add` picks the newest compatible release, writes `<pkg>>=<version>` and updates `uv.lock`. Only a trap that names a bad version may add a bound, and then through `uv add "<pkg><bound>"`. Packages the template already brings (django, celery, uvicorn, django-storages...) keep the `==` pins its hook wrote, also through `uv add`.
```
grep -E '^\s*"(django-cotton|django-basecoat|django-unicorn|unpoly|channels|channels-redis|django-tailwind-cli)(\[[^]]*\])?>=' pyproject.toml | wc -l   # 7: written by uv add
uv lock --check                                                                          # lock matches pyproject
uv pip list | grep -ciE '^(django|django-cotton|django-basecoat|django-unicorn|unpoly|celery|channels|channels-redis|django-storages|uvicorn|django-tailwind-cli) '   # 11
.venv/bin/python -V                                                                     # matches requires-python
```

Traps:
- If `uv add` stalls on a download, kill it; `uv sync` resumes.

**2. No Node.** There is no `package.json`, `package-lock.json` or `node_modules`, and nothing runs node.
- Tailwind v4 runs as the standalone binary through django-tailwind-cli. Its version is pinned in settings. The binary is downloaded on first use and not committed.
- Browser files are downloaded from jsDelivr into `<pkg>/static/vendor/` and committed: Unpoly JS and CSS with both `.map` files, Alpine, the Alpine morph plugin, Basecoat JS, and the Basecoat CSS source (imported by a relative path).
- All versions live in one place: the URLs of the justfile's `vendor` recipe, like `unpoly@3.14.3`. `just vendor` downloads them again. `just run` and `just asgi` do not depend on it, so the app starts offline.
```
ls package.json package-lock.json node_modules 2>/dev/null                              # nothing
grep -rlE '(^|[^/.])\b(npm|npx)\b|node_modules' justfile .github README.md AGENTS.md .zed   # nothing (jsDelivr URLs contain /npm/, which is fine)
just vendor && git diff --exit-code <pkg>/static/vendor                                  # after this goal's commit: no diff
```
Also: both Unpoly `.map` files are in `static/vendor/` (`ls <pkg>/static/vendor | grep -c '\.map$'` is at least 2), every file in `static/vendor/` is named in the `vendor` recipe, and `just css` plus `just test` pass with every node, npm and npx folder removed from `PATH`.

Traps:
- The Unpoly min files end with `sourceMappingURL`, so production `collectstatic` fails without the `.map` files.

### Settings
**3. Apps wired.** Installed apps and middleware include unicorn, cotton, basecoat, channels and the Unpoly middleware. Unicorn URLs are routed. `UNICORN` uses the Alpine morpher and lists the project app in `APPS`. `ASGI_APPLICATION = "config.asgi.application"`. `CHANNEL_LAYERS` uses `channels_redis.core.RedisChannelLayer` with hosts from `REDIS_URL`.
```
uv run python manage.py shell -c "from django.conf import settings as s; from django.urls import reverse; print(all(a in s.INSTALLED_APPS for a in ['django_unicorn','django_cotton','django_basecoat','channels']), [m for m in s.MIDDLEWARE if 'npoly' in m], reverse('django_unicorn:message'), s.UNICORN, s.ASGI_APPLICATION, s.CHANNEL_LAYERS['default']['BACKEND'])"
# expect: True, the unpoly middleware, /unicorn/message, alpine, config.asgi.application, RedisChannelLayer
```

**4. Database and Redis come from the environment.** `.env` is read by default, and real environment variables win over it. The local cache is Redis from `REDIS_URL`, set in `config/settings/local.py` where the template had an in-memory cache, so test settings never inherit it. Host, port and user match setup.json; the database name is `<pkg>`.
There is no fallback database: if the database variables are missing, settings fail loudly. Tests keep the template's database settings, so they read the same keys. Test settings add `ALLOWED_HOSTS = ["testserver"]`, `InMemoryChannelLayer`, and Celery running tasks inline. They set no `CACHES`.
```
uv run python manage.py shell -c "from django.conf import settings as s; from urllib.parse import urlsplit as u; d=s.DATABASES['default']; r=u(s.CACHES['default']['LOCATION']); print(d['HOST'], d['PORT'], d['USER'], d['NAME'], r.hostname, r.port)"
jq '.postgres.host,.postgres.port,.postgres.username,.redis.host,.redis.port' <setup.json>   # same values
env -i PATH=$PATH HOME=$HOME DJANGO_READ_DOT_ENV_FILE=False uv run python manage.py check     # fails on the missing database variables
DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py shell -c "from django.conf import settings as s; print(s.DATABASES['default']['ENGINE'], s.CHANNEL_LAYERS['default']['BACKEND'], s.CELERY_TASK_ALWAYS_EAGER)"
# expect: postgresql, InMemoryChannelLayer, True
grep -n CACHES config/settings/test.py                                                      # nothing
```

Traps:
- `base.py` reads the database variables at import time, so `manage.py tailwind` needs them too: `.env` locally, the workflow-level env in CI.
- `.env` uses separate `POSTGRES_HOST/PORT/DB/USER/PASSWORD` keys, so the password needs no URL encoding. The Redis password in setup.json may be null: then `REDIS_URL` has no user part.

**5. Secrets stay in `.env`.** Passwords are written from setup.json into `.env` without being shown, and the file is mode 600. Never print, cat or commit it. `.env.example` lists key names with empty values. `.dockerignore` keeps `.env` out of the image (the generated one does not).
```
stat -c %a .env                    # 600
grep -c '=.' .env.example          # 0
grep -cxE '\.env' .dockerignore    # 1
```

**6. Template cleanup.** No `ATOMIC_REQUESTS`. python-slugify removed. `USE_DOCKER` defaults to False in `config/settings/local.py`. `.venv` was built inside the repo folder (a venv built before a rename keeps old paths). The production deploy check is clean.
```
grep -r ATOMIC_REQUESTS config; grep slugify pyproject.toml    # nothing
grep -n USE_DOCKER config/settings/local.py                    # default False
head -1 .venv/bin/pytest                                       # starts with #!<repo folder>/.venv/
env -i PATH=$PATH HOME=$HOME DJANGO_READ_DOT_ENV_FILE=False DJANGO_SETTINGS_MODULE=config.settings.production \
  DJANGO_SECRET_KEY=<random 50 chars> DJANGO_ADMIN_URL=x/ DATABASE_URL=postgres://x@127.0.0.1/x REDIS_URL=redis://127.0.0.1:6379/0 \
  <every other key production.py needs, dummy value> uv run python manage.py check --deploy   # no issues
```

Traps:
- `check --deploy` with GCP and Other SMTP also needs `DJANGO_GCP_STORAGE_BUCKET_NAME`. The production settings read no SMTP host or credentials; the deploy step must add them.

**7. Django check passes.** `uv run python manage.py check` says no issues.

### Frontend
**8. Base layout.** Every page loads the built Tailwind CSS, Unpoly JS and CSS, Basecoat JS, and Alpine with the morph plugin, all from `static/vendor` (no CDN at runtime). Exactly one Alpine. All scripts use `defer`, morph before Alpine. `{% unicorn_scripts %}` appears once in `<head>`. The page has `up-main`, Unpoly sends the CSRF token from a `csrf-token` meta tag (`CSRF_HEADER_NAME = "HTTP_X_CSRF_TOKEN"`), and a `{% csrf_token %}` input sits inside `<main>` for unicorn.
The layout is an app shell, not bare markup: a header with the app title, the nav links and the theme toggle; content in a centered container with a max width and consistent spacing; Basecoat's background, foreground and font tokens on `body`. Every control is a Basecoat component. No project design yet: the prototype's look comes later.
Check: start `just run`; every `/static/` CSS and JS file linked from `curl -s localhost:8000/` returns 200. A test asserts the unicorn script appears once and there is one `csrfmiddlewaretoken`.

Traps:
- The template sets `CSRF_COOKIE_HTTPONLY`, so unicorn cannot read the cookie and uses the first `csrfmiddlewaretoken` input. Without it inside `<main up-main>`, calls fail with `CSRF token is missing`.
- `{% unicorn_scripts %}` twice on a page breaks the non-debug build (`const url` declared twice).

**9. Home page.** `/` renders through one project cotton component that holds a Basecoat button, card and dropdown menu, plus one Tailwind class. Placeholder content says it is a placeholder. No invented product actions: every button and link goes somewhere real.
Check: a test asserts the component and the three Basecoat markers.

Traps:
- The django-basecoat README gives wrong component names. The real ones follow the file paths, with a dot: `<c-dropdown-menu.content>`, `<c-card.header>`. Extra attributes pass through, so `up-href` and `@click` work on `<c-button>`.
- Cotton in tests: render with `engines["django"].from_string('{% load cotton %}{% cotton name a="b" %}{% endcotton %}')`. `<c-x>` tags are not compiled in `from_string`, and `render_component` crashes when template debug is on.

**10. Unpoly protocol works.**
```
curl -s -D- -o/dev/null -H 'X-Up-Version: 3' -H 'X-Up-Target: main' localhost:8000/ | grep -i x-up-method
```

**11. Tailwind build.** The built CSS has classes used by the django-basecoat templates, basecoat-css and the unicorn component templates. It has none from the vendored JS or from the built CSS itself: two `@source not` lines exclude those folders, which also makes the build give the same bytes every time.
Check: after `just css`, the built CSS contains `animate-spin` (from `<c-spinner>`), `.btn-outline`, and a utility used only in the demo unicorn template; `grep -c '@source not' <input css>` is 2.

Traps:
- basecoat-css 1.x lacks classes that django-basecoat 0.2 uses (`btn-outline`, `alert-destructive`). Use 0.3.x.
- Tailwind skips the gitignored `.venv`, so it needs an `@source` line pointing at the django-basecoat templates. Use the literal `lib/python3.X/site-packages` path; a glob does not match.
- The Tailwind binary is about 110 MB from GitHub releases, cached in `.django_tailwind_cli/`. GitHub downloads can crawl; a copy from another checkout is fine if its sha256 matches the release's `sha256sums.txt`.

**12. Dark mode.** Light, dark and system choices. The choice is a `theme` cookie; the server renders `<html data-theme>`, so there is no flash and no head script. Alpine switches it (`x-data` on `<html>`, `@click` on the items) and an Unpoly form posts it to a view that sets the cookie and answers 204. System is CSS (`prefers-color-scheme`). Tailwind's `dark:` follows `data-theme`, `color-scheme` on `:root` matches, Basecoat's dark palette follows too, and every page has the toggle in the header: a Basecoat select or dropdown menu, never bare text or plain buttons.
Check: tests cover the cookie view, the rendered `data-theme`, and that the dark tokens still equal Basecoat's `.dark` block. The built CSS contains `where([data-theme=dark]` and `color-scheme`, and no `:is(.dark *)`.

Traps:
- Basecoat's dark mode uses a `.dark` class and `@custom-variant dark (&:is(.dark *))`. Our own `@custom-variant` on `data-theme`, placed after the Basecoat import, wins, also inside Basecoat's `@apply dark:`. Basecoat's color tokens sit on `.dark`, so copy them onto `[data-theme=dark]` and the system media query; then `.dark` is never set.

**13. Unpoly and Alpine work together.**
- No custom JS: behavior is `up-*` and Alpine attributes. Alpine initializes swapped fragments itself.
- `app.js` holds only `up.history.config.restoreTargets = [":main"]` (Basecoat widgets die when `body` is swapped) and `up.network.config.autoCache = false` (cached pages bring back dead unicorn components).
- Every URL returns a full HTML document, never a fragment.
- Home opens one secondary page as an overlay, from one `<c-button up-href up-follow up-layer="new">` (no button inside an `<a>`). Opening as an overlay is the link's choice, not the page's: the page is a full page with `<main up-main>`, named for what it shows (the unicorn demo of goal 15, for example `/live-counter/`), and works opened directly too. The overlay box is the only frame: no card inside, background from the surface token.

Check: `grep -rn 'basecoat\.init' <pkg>/static --exclude-dir=vendor` finds nothing. A test asserts no inline script besides unicorn's, home has `up-layer="new"`, no `<a>` wraps a button, and the secondary page returns 200. In the browser, under both `just run` and `just asgi`: Alpine, the unicorn demo and the Basecoat dropdown still react after an Unpoly swap of `main`, inside the overlay, and after going back in history; Alpine state inside the component survives a re-render; there is one Alpine script; the theme toggles.

Traps:
- Basecoat's JS already initializes new elements through a MutationObserver on `document.body`, so `basecoat.init(name)` in a compiler binds every listener twice.
- `unpoly.min.css` gives `up-modal-box` `background-color:#fff` and `up-modal-dismiss` a fixed grey, so in dark mode the overlay is a white frame around dark content. Style `up-modal-box`, `up-drawer-box` and `up-popup` in the Tailwind input with Basecoat's `--background`, `--foreground` and `--border` (and the dismiss buttons with `--muted-foreground`); the Tailwind CSS loads after Unpoly's, so these win.

**14. Template layout.** Templates live in `cotton/`, `layouts/`, `partials/`, `pages/` and `unicorn/` (plus error pages and app overrides). There is no root `base.html`. Every page renders.
URLs, URL names, views and templates are named for what the page is to the user. Never for a UI mechanism (modal, overlay, drawer, partial, fragment) and never numbered.
Check: with `just run`, `/`, `/about/` and each project page return 200, and the HTML contains no `{{`, `{%`, `<c-x` or `TemplateSyntaxError`. `grep -rniE 'modal|overlay|drawer|layer|[a-z][0-9]+\b' config/urls.py <pkg>/*/urls.py` and the file names under `templates/pages/` find no route or page named that way.
In the browser, look at every page at desktop width and at phone width, in light and in dark: the header, the container and the spacing hold; nothing touches the viewport edge; no control is unstyled or bare text; nothing overflows sideways; every link and button goes somewhere. Fix what looks broken, then look again.

**15. Unicorn demo.** One clearly named component, for example `live-counter` (`core/components/live_counter.py` and `templates/unicorn/live-counter.html`), on the secondary page that home opens as an overlay (goal 13), not on home.
Check: a test opens that page, posts a `callMethod` to `/unicorn/message/<name>`, gets 200, and finds the new state in `data` and `dom`. In the browser, clicking it works under `just asgi` too.

Traps:
- Write the root attribute single-quoted: `unicorn:data='{"count":0}'`.
- Round-trip test: GET the page, read the attributes with the regex `unicorn:(id|data|meta)=(["'])(.*?)\2`, then POST JSON `{"id", "data", "meta": "<checksum>::1", "actionQueue": [{"type": "callMethod", "payload": {"name": "increment"}}]}` to `/unicorn/message/<name>`. The response has `data` and `dom`.

### Background work
**16. Celery.** A trivial task `ping` returns `"pong"`.
Check: a test runs it inline. With Redis from setup.json running, start `just worker`, then:
```
uv run celery -A config.celery_app call <pkg>.core.tasks.ping     # prints a task id
uv run celery -A config.celery_app result <id>                    # pong
```
`just beat` starts without errors (it needs the migrated database, because it stores its schedule there).

Traps:
- Tests use `CELERY_BROKER_URL = "memory://"` and result backend `cache+memory://`. `celery call` prints only the task id.

**17. Channels.** A consumer in `<pkg>/consumers.py` answers `pong` on `ws/ping/`, routed in `<pkg>/routing.py`. `config/asgi.py` is a `ProtocolTypeRouter`: `http` goes to the Django ASGI app, `websocket` to `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(...)))`. The generated `sys.path` and settings lines stay. The template's raw `config/websocket.py` is removed.
Check: a test with `channels.testing.WebsocketCommunicator` sends a message and gets `pong`. With `just asgi` running, a websocket client on `ws://localhost:8001/ws/ping/` gets `pong`.

Traps:
- In `asgi.py`, import `channels.auth` after `get_asgi_application()` (keep the template's one `# noqa: E402` there); other Channels imports go at the top.
- `channels.testing` imports `daphne`, so add it with `uv add --dev daphne`. `AllowedHostsOriginValidator` reads `ALLOWED_HOSTS` at import, before pytest-django adds `testserver`, so the test settings set it and tests send origin `http://testserver`. Wrap the communicator in `async_to_sync`; pytest-asyncio is not needed.

### Developer workflow
**18. justfile.** The generated compose recipes stay. Host recipes are added:
| recipe | does |
|---|---|
| `run` | runserver on port 8000 |
| `asgi` | `uv run uvicorn config.asgi:application --reload --port 8001`, serves websockets, can run next to `run` |
| `worker`, `beat` | `uv run celery -A config.celery_app ...` directly, not through compose |
| `css`, `css-watch` | `manage.py tailwind build` / `watch`, with `DJANGO_SETTINGS_MODULE=config.settings.test` |
| `vendor` | downloads the pinned browser files |
| `test`, `migrate`, `setup` | `setup` = `uv sync` plus css. `test` builds whatever tests need. |
Check: `just --summary` lists them all. Tests pass even when Redis is unreachable:
```
REDIS_URL=redis://127.0.0.1:1/0 just test
```

**19. Superuser recipe.** `just superuser` runs `createsuperuser --noinput` using `DJANGO_SUPERUSER_EMAIL` (= `<email>`) and a generated `DJANGO_SUPERUSER_PASSWORD` from `.env` (both keys also in `.env.example`). The password is never printed. Bootstrap does not run it.
Check: `grep -c '^DJANGO_SUPERUSER_\(EMAIL\|PASSWORD\)=.' .env` is 2. On a throwaway database `<pkg>_check` on setup.json's Postgres (create, `POSTGRES_DB=<pkg>_check` migrate and superuser, then drop it), the output does not contain the password: `grep -cFf <(sed -n 's/^DJANGO_SUPERUSER_PASSWORD=//p' .env)` is 0.

Traps:
- Keys from `.env` end up in `os.environ`. `DJANGO_SUPERUSER_*` there breaks the template's `test_createsuperuser_command`; an autouse conftest fixture removes them.

**20. Zed tasks.** `.zed/tasks.json` is committed (`.zed/` is not ignored). One task per local process, each calling its just recipe: Tailwind watch (`just css-watch`), Django server (`just run`), ASGI server (`just asgi`), Celery worker (`just worker`), Celery beat (`just beat`), tests (`just test`). Every task sets `"cwd": "$ZED_WORKTREE_ROOT"`, `"use_new_terminal": true`, `"reveal": "always"`, `"hide": "never"`. Long-running tasks allow concurrent runs; tests do not. Django and Celery tasks read `.env`.
Check: `jq` parses the file (it is JSONC, strip comments first if any), every task's command is a recipe in `just --summary`, and `git check-ignore --no-index .zed/tasks.json` exits 1.

### Quality gates
**21. Lint and types.** pre-commit hooks (installed in B2) still all pass. The built CSS and `<pkg>/static/vendor/` are excluded from pre-commit: its whitespace and end-of-file fixers would rewrite them and break the CI check in goal 23 and the no-diff check in goal 2.
```
git add -A && uv run pre-commit run --all-files   # exit 0 (run once more after autofixes)
uv run mypy <pkg>                                 # no issues
```

Traps:
- Ruff flags `HTTPStatus.OK` comparisons (PLR2004) and generated secrets (S106) in tests.

**22. Coverage.** `just test` runs pytest under coverage and prints a report, with `fail_under = 80` in pyproject. Python only: the template's `django_coverage_plugin` is removed with `uv remove --dev django-coverage-plugin`. Coverage comes from real tests (pages, components, settings, task, consumer); `omit` lists only migrations and tests.
Check: `just test` shows TOTAL of at least 80, and `uv run coverage report --fail-under=100` fails (proves the gate is real).

**23. Built CSS is committed and CI catches a stale one.** The linter job also runs `uv sync`, `just css`, then `git diff --exit-code <built css>`. No Node setup and no `.env` in CI. If `ci=None`, there is no CI: report this goal as not verified.
Check: the CI file has that step. After this goal's commit, `just css && git diff --exit-code <built css>` exits 0. A fresh clone with no `.env`, only the workflow's `POSTGRES_*` values, and no node on `PATH` gives no diff after `uv sync` and `just css`. For GitHub, lint the workflow with `actionlint`, or `docker run --rm -v $PWD:/repo -w /repo rhysd/actionlint` if it is not installed; otherwise report not verified.

Traps:
- CI must run `uv sync` before `just css`, or the `@source` path into site-packages is empty. The linter job then needs `libpq-dev` and uv, as the pytest job does (B1).

### Repo files
**24. `.gitignore`.** Ignores `.env`, `.venv` and the Tailwind binary cache `.django_tailwind_cli/`. Does not ignore the built CSS, `<pkg>/static/vendor/` or `.zed/`: those are committed (goals 2, 20, 23).
```
git check-ignore --no-index .env .venv .django_tailwind_cli/ | wc -l             # 3
git check-ignore --no-index <built css> <pkg>/static/vendor/x .zed/tasks.json    # exits 1
```

**25. No leftovers from the template's frontend.** No Bootstrap CSS and no crispy forms. The generated Docker, compose, Celery and docs files stay (see "What happens to the Docker files").
```
grep -rliE 'bootstrap5|bootstrap\.min|crispy' --exclude-dir=.venv .     # nothing
ls justfile compose/production/django/Dockerfile compose/production/django/start docker-compose.local.yml   # all exist
```

**26. README and AGENTS.md basics.** README has the title, the one-liner and how to run it: Postgres and Redis on the host, then `run`, `asgi`, `worker`, `beat`, `css-watch`. AGENTS.md has the stack, the commands (including the Zed tasks), the folder layout and the component ladder. Neither mentions the bootstrapper.
Check: `grep -nE '\.bootstrap|artifacts' AGENTS.md README.md` finds nothing.

**27. AGENTS.md rules.** The app's AGENTS.md also covers:
- the component ladder: Basecoat first, then cotton, then Alpine, then unicorn. Unicorn only when Unpoly and Alpine cannot do it simply (live server state, many linked fields, polling-heavy screens); its endpoint returns JSON. Name the demo component as the example.
- no second component library, and never hand-roll a component Basecoat ships
- naming: URLs, URL names, views and templates are named for what the page is to the user, in the app's language. Never for a UI mechanism (modal, overlay, drawer, partial) and never numbered (`/modal2/`). Opening a page as an overlay is the link's choice (`up-layer="new"`), not part of the page's name.
- looking at the result: after UI changes, open the pages with the browser tools available, at desktop and phone width, light and dark
- every django-basecoat component, read from the package's `templates/cotton/` (the README names are wrong)
- the Unpoly, Alpine, unicorn and theme rules; Celery for background work; Channels for websockets (`just asgi` serves them); `@theme` tokens named by purpose
- working rules: no hand-written migrations, no `# noqa`, no comments that narrate the code, no commit trailers, rebuild and commit the Tailwind CSS after template or CSS changes, lint and test before each commit

Check: every `<site-packages>/django_basecoat/templates/cotton/*.html` name (with `_` as `-`) appears in AGENTS.md; `grep -ciE 'migrations by hand|noqa|narrat|trailer|lint|tailwind' AGENTS.md` is at least 6; `grep -cE 'unicorn.*JSON|JSON.*unicorn' AGENTS.md` is at least 1; `grep -ciE 'mechanism|numbered' AGENTS.md` is at least 1; the demo component's file name appears; goal 26's check still finds nothing.

## Versions
Use current compatible releases: `uv add` chooses them, never pick a version by hand. Bound one only where a trap says a version is bad. Resolved versions live in `uv.lock`, the `vendor` recipe URLs and the Tailwind version setting.

## Database
Pass the password only through the environment, never echo it. With setup.json at `<bootstrapper repo>/.bootstrap/setup.json`, check whether the database exists:
```
PGPASSWORD="$(jq -r .postgres.password <setup.json>)" psql -h "$(jq -r .postgres.host <setup.json>)" -p "$(jq -r .postgres.port <setup.json>)" \
  -U "$(jq -r .postgres.username <setup.json>)" -d postgres -tAc "select 1 from pg_database where datname='<pkg>'"
```
Create it with the same command and `-c 'CREATE DATABASE "<pkg>"'`. Then `just migrate` on Postgres must report all migrations OK. Tests use `test_<pkg>` on the same server, which pytest-django creates and keeps between runs (`--reuse-db`).

## Run
- `cd <repo folder> && just run`
- websockets: `just asgi` (port 8001)
- background jobs: `just worker` and `just beat`
- styles: `just css-watch`

## Later: turning the HTML prototype into the app
Not part of bootstrap. The HTML prototype is throwaway. It shares the look, not the plumbing: plain links, no Unpoly, no cotton or unicorn markers.
| prototype | app |
|---|---|
| `assets/app.css` token values (`:root`, `.dark`) | same variables in the Tailwind input CSS |
| `assets/theme.css` `@theme inline` block | `@theme inline {}` in the Tailwind input CSS |
| Basecoat markup | cotton components, django-basecoat |
