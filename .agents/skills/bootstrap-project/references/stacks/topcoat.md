# Stack: topcoat
A server-rendered Rust web app on Topcoat (tokio-rs), with Toasty on Postgres, Tailwind and Topcoat UI, Arabic and English from day one, and a container image.

| part | role |
|---|---|
| Rust 1.99, edition 2024 | toolchain, pinned in `rust-toolchain.toml` with rustfmt and clippy |
| Topcoat 0.12 | router (module routing), `view!` components, layouts, assets, sessions, mail, localization, browser runtime |
| Topcoat runtime (`--interaction topcoat`) | small interactions: `$(...)` expressions and `#[shard]` components that re-render on the server |
| Toasty 0.11 with the `postgresql` feature | models and queries. Schema changes through `cargo run -- toasty migration generate` and `apply`, the branch the generated `src/main.rs` adds when the first argument is `toasty`. |
| Tailwind CSS 4 (Topcoat `tailwind` feature) + Topcoat UI | styling and components copied into `src/components` by `topcoat ui` |
| Iconify, Fontsource | icons and fonts through Topcoat's asset pipeline |
| Fluent (`l10n-fluent`) | `en` and `ar` messages, `lang` and `dir` on `<html>` |
| Topcoat mail (`mail-smtp`) | email: SMTP in production, file transport in development, memory transport in tests |
| just | the commands people and agents run |
| Postgres | on the host, from /setup. Redis from /setup is not used. |

Not in this stack: sign-in, background jobs, form validation, admin screens, rate limiting. Topcoat lists auth, background jobs and validations on its roadmap; until they ship, add crates per project.
Islands are on Topcoat's roadmap but not shipped. Interactive pages use the runtime and shards first. A widget that needs more is a custom element with a JSON props contract (goal 9), so it can become an island later without changing the page around it.
Topcoat is pre-1.0: the README says "Early-stage and experimental. Expect breaking changes." Pin exact versions and upgrade on purpose, following each release's upgrade guide.
Network: GitHub (the Tailwind CLI download), crates.io, Docker Hub.

## Names used below
| name | means |
|---|---|
| `<title>`, `<one_liner>`, `<slug>` | from the project's status.json |
| `<pkg>` | the Cargo package and database name: slug with `-` replaced by `_` |
| `<parent>`, repo folder | the parent folder the user chose, and `<parent>/<slug>` |
| setup.json | `.bootstrap/setup.json` in the bootstrapper repo (Postgres, GitHub account) |
| `<x>` | the answer to input `x` from the table below |

## Tools
| tool | check | fix |
|---|---|---|
| rustup, cargo | `rustup --version && cargo --version` | `/ensure-installed rust` |
| Rust 1.99 | `rustc --version` prints `1.99` or later (the repo's `rust-toolchain.toml` pins it once it exists) | `rustup toolchain install 1.99 --component rustfmt clippy` |
| topcoat CLI 0.12 | `topcoat --version` | `cargo install topcoat-cli --version 0.12.1 --locked` (not in /ensure-installed yet) |
| just | `just --version` | `/ensure-installed just` |
| jq, psql, curl | `command -v jq psql curl` | install with the system package manager |
| docker | `docker info` | /ensure-runnable-docker |

## Inputs
| key | means | recommend |
|---|---|---|
| port | port the dev server listens on | first free port from 3000 up: `ss -ltn "sport = :<p>"` (macOS: `lsof -iTCP:<p> -sTCP:LISTEN`) shows nothing |
| default_locale | locale used when the browser asks for neither | `en`. Choices: en, ar |
| ci | CI provider | `Github`. Choices: Github, None |

## Source: how the repo is generated
```
topcoat new <repo folder> --name <pkg> --no-git --no-interactive \
  --recommended --routing module --database toasty --interaction topcoat \
  --tailwind --icons iconify --font fontsource --ui --no-example
```
`--recommended` answers every choice; the other flags pin them so a newer CLI with a different preset still gives this shape. The bootstrap creates the repo itself, hence `--no-git`. Then the agent adapts the app until every goal passes.

Traps:
- The destination must not exist, even empty.
- Without a terminal, `topcoat new` needs a destination and every feature choice, and never falls back to a preset on its own.
- The generator only scaffolds Toasty on SQLite. Goal 3 moves it to Postgres.

## Baseline: in the first commit
These go into the first commit on `main`, so its first CI run is green. Everything else waits for the Goals branch.
Traps last verified: none. No bootstrap run has happened, so every trap below comes from the docs and source read 2026-11-16, with `topcoat` and `topcoat-cli` 0.12.1, `toasty` 0.11.0, Rust 1.99 and `actions/checkout` v7. The first run replaces this line with the versions it verified, and records what it hit as traps.

**B1. Toolchain and checks.** `rust-toolchain.toml` pins `channel = "1.99"` with `components = ["rustfmt", "clippy"]`. `rustfmt.toml` sets `edition = "2024"` (`topcoat fmt --rustfmt` needs it). `Cargo.toml` pins `topcoat` with `=0.12.1` and `toasty` with `=` the version the generator wrote. A justfile has `fmt` (`topcoat fmt --rustfmt`), `check` (`topcoat fmt --check --rustfmt`, `cargo clippy --all-targets -- -D warnings`, `cargo test`) and `dev` (`HOST=127.0.0.1 PORT=<port> topcoat dev`). `topcoat l10n check` joins `check` in goal 5, `migration` and `migrate` in goal 3, `seed` in goal 14.
CI (from the `ci` input) is one GitHub workflow on pull requests and pushes to `main`: `actions/checkout@v7`, `rustup show` (installs the pinned toolchain), `Swatinem/rust-cache@v2`, start the runner's Postgres, then the same commands as `just check`, with `DATABASE_URL` set at workflow level. No Docker or `services:` containers. If `ci=None`, there is no CI: report this goal as not verified.
```
just check                                                 # passes on the bare scaffold
grep -nE '"=0\.12\.1"' Cargo.toml                          # topcoat pinned exactly
grep -niE 'docker|compose|services:' <CI file>             # nothing
```
Lint the workflow with `actionlint`, or `docker run --rm -v $PWD:/repo -w /repo rhysd/actionlint` if it is not installed.

Traps:
- GitHub's `ubuntu-latest` ships PostgreSQL with the service stopped: `sudo systemctl start postgresql.service`, then `sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres'"`, because TCP logins need a password.
- `topcoat fmt --check` without `--rustfmt` checks only macro bodies.

**B2. `.gitignore`.** Ignores `target/`, `.env`, `data.db*` and `mail/` (the file transport's folder). Does not ignore `Cargo.lock`, `.zed/` or `components.toml`.
```
git check-ignore --no-index target/x .env data.db | wc -l       # 3
git check-ignore --no-index Cargo.lock .zed/tasks.json          # exits 1
```

## Goals
Checks that start the app need the database created and migrated.
A browser check means using the browser tools available to you, the way a person would: open the page, click, look. Never write a script that drives a browser. With no browser tools, report that goal as not verified.

### Dependencies
**1. Crates and versions.** Every crate is added with `cargo add <crate>@<version>` and removed with `cargo remove`; never edit `[dependencies]` by hand. `topcoat` stays pinned with `=` (B1). Topcoat features in use: `tailwind`, `l10n-fluent`, `session`, `mail-smtp`, `sse`, and whatever the generator enabled. `toasty` adds the `postgresql` feature and drops `sqlite` once nothing uses it. `toasty-cli` arrives with the generator, for the migration branch in `src/main.rs`; pin it with `=` too.
```
cargo tree -d --depth 1                                     # no duplicate topcoat or toasty versions
grep -nE '^topcoat.*"=0\.12\.1"' Cargo.toml                 # pinned
```

### Server
**2. Environment from `.env`, checked at boot.** `src/env.rs` reads `DATABASE_URL` (required, `postgresql://`), `HOST` (default `127.0.0.1`), `PORT` (default `<port>`), `SMTP_URL` (optional; empty means the file transport) and `APP_ENV` (default `development`). A missing required variable stops boot with a message naming every missing key; there is no fallback database. `.env` is written from setup.json without being shown, mode 600, with database `<pkg>`. `.env.example` lists the keys with empty values.
```
stat -f %Lp .env 2>/dev/null || stat -c %a .env           # 600
grep -c '=.' .env.example                                  # 0
env -i PATH=$PATH HOME=$HOME ./target/debug/<pkg>          # exits non-zero, names DATABASE_URL
```

**3. Postgres through Toasty.** `src/db.rs` connects with `Db::builder().models(toasty::models!(crate::*)).connect(DATABASE_URL)`; the URL scheme picks the driver, so the generator's `sqlite:data.db` constant becomes goal 2's `DATABASE_URL`. One example model, `Note` (`id`, `body`, `created_at`), so the app has one real read and write. Migrations run through the app binary, which is what the generator wires: `src/main.rs` keeps its `toasty` first-argument branch (`toasty_cli::ToastyCli::new(db).parse_from(args)`), so `cargo run -- toasty migration generate` writes `toasty/history.toml`, `toasty/snapshots/` and `toasty/migrations/*.sql`, and `cargo run -- toasty migration apply` applies them. The generator writes no `Toasty.toml`; add one only to move the folder or change the file naming. `just migration` and `just migrate` wrap those two commands and run from the crate root. The generated `toasty/` folder is committed.
```
just migration                                             # writes the first file under toasty/migrations/
just migrate; just migrate                                 # applies, then applies nothing
grep -rn 'sqlite' Cargo.toml src/                          # nothing
```
Traps:
- `toasty` is the app binary's first argument, not a program on `PATH`: `toasty migration generate` is a command-not-found, and the working form needs the crate root, because the binary opens the database before it parses the argument.
- `migration generate` writes nothing and exits 0 when the schema has not changed since the snapshot, so an empty `git status` means no diff, not a broken command.
- When the diff has a dropped and an added table or column, `generate` asks whether it is a rename, and that prompt blocks without a terminal. Answer it in a terminal, or split the change into two migrations.

**4. Pages, layout and health.** Module routing. A root layout with the app title, nav links (active state shown) and the theme and language controls; content in a centred container with a max width. Routes: `/{locale}/` is the notes page (a form plus the list, newest first, with empty and error states, labelled as example data); `/{locale}/about` is a placeholder that says so; `/` redirects to the negotiated locale. `GET /health` pings the database and returns `{"ok":true}`.
```
curl -s localhost:<port>/health                            # {"ok":true}
curl -sI localhost:<port>/ | grep -i '^location: /'        # redirect to /en/ or /ar/
```

**5. Arabic and English.** `messages!("./l10n/{locale}.ftl")` with `src/l10n/en.ftl` and `src/l10n/ar.ftl`. Every user-facing string goes through `t!`. The locale comes from the URL prefix, then `negotiate(accept_language(cx), ...)`, then `<default_locale>`. `<html lang dir>` comes from `locale(cx).id()` and `.direction()`. The language switch links to the same page under the other prefix. Layout uses logical CSS properties and Tailwind `ms-`/`me-`/`ps-`/`pe-`/`start-`/`end-` utilities, never `ml-`/`mr-`/`left-`/`right-`.
```
topcoat l10n check                                         # exit 0, both locales complete
curl -s localhost:<port>/ar/ | grep -o '<html[^>]*>'       # lang="ar" dir="rtl"
grep -rnE '\b(ml|mr|pl|pr)-[0-9]|\b(left|right)-[0-9]' src/ # nothing
```
Check, in the browser: `/ar/` mirrors (nav, form and list read right to left), and the switch keeps the page.

Traps:
- A missing message renders its key, such as `greeting(name: "Ada")`, instead of falling back to another language. `topcoat l10n check` is the guard.

**6. Tailwind and Topcoat UI.** `build.rs` renders Tailwind with the release pinned through `version(...)` and `version_checksum(...)`, or the default release, which Topcoat verifies itself. `topcoat ui init` installs the theme; components come from `topcoat ui add` into `src/components`: at least button, card, input and dropdown menu. Every control on the pages is one of them. `components.toml` is committed.
```
topcoat ui list                                            # the installed components, no pending updates
```

Traps:
- `build.rs` downloads the Tailwind CLI from GitHub. Offline builds and locked-down image builds fail unless `executable_env("TAILWIND_CLI")` points at a preinstalled binary.
- Tailwind only sees class names written out in source. Classes built from strings at run time are missing from the CSS.

**7. Dark mode.** Light, dark and system. The `dark` class on `<html>` before first paint (an inline script reading the stored choice), `color-scheme` following it. The control is the Topcoat UI dropdown menu with an icon and label.
Check, in the browser: choose Dark and reload: dark from the first paint. In both themes and both directions, at desktop and phone width, nothing overflows sideways or shows as a bare unstyled control.

**8. Live updates with the runtime.** Adding a note re-renders only the list, through a `#[shard]`, not the whole page. A second shard shows the note count, updated over the `sse` feature when another browser adds a note. The shard validates its arguments; its endpoint does not inherit page guards.
Check, in the browser: two windows on `/en/`; add a note in one; the other's count changes without a reload.

Traps:
- A shard has its own HTTP endpoint, and the page's guards do not run for it. Authorize inside every shard and procedure.
- Every value a signal sends back is user input.
- The runtime is marked highly experimental. Keep `$(...)` expressions small.

**9. Interactive widget seam (islands placeholder).** One custom element, served through `asset!`, mounted on a server-rendered page as `<x-note-preview data-props='{...}'>` with props from a typed Rust struct serialised to JSON. The page works without it, showing the server-rendered fallback inside the element. The README names this as the pattern for heavy client widgets until Topcoat ships islands. No htmx, Datastar or Alpine alongside the Topcoat runtime.
Check, in the browser: the widget renders with the server's props; with JavaScript off, the fallback shows.

**10. Mail.** One message (a test "note added" email) rendered with `view!`, translated, sent through the transport chosen from `SMTP_URL`: SMTP when set, the file transport into `mail/` otherwise. Tests use the memory transport and assert the subject and recipient.
Check: add a note in development; a file appears in `mail/`.

**11. Sessions.** Topcoat manages the token (32 random bytes, `__Host-` cookie, `Secure`, `HttpOnly`, `SameSite=Lax`); the app stores only its SHA-256 `TokenHash` with the expiry in a `session` table through Toasty, and rejects missing or expired records. Sign-in itself is not in this stack, so the example session only holds the chosen theme.
Check: `curl -c` then `-b` keeps the same session across two requests; the table holds a hash, never the raw token.

**12. Tests.** `cargo test` covers: a note added and listed first, an empty note refused, `/health`, the environment error, and the mail assertion. Tests use `<pkg>_test` on the same server, created and migrated if missing, reused between runs. No database mocks.
Check: `cargo test` passes twice in a row.

### Delivery
**13. Container.** `Dockerfile`, multi-stage. Build stage `rust:1.99-slim` with the pinned Tailwind CLI on `TAILWIND_CLI`; `cargo build --release --locked`. Run stage `debian:bookworm-slim` (or distroless cc once verified), non-root user, the binary and its assets, `HOST=0.0.0.0`, `PORT` honoured. `.dockerignore` excludes `target`, `.env`, `.git`, `mail`.
```
docker build -t <slug> .
docker run -d --rm --name <slug>-check --network host --env-file .env -e HOST=0.0.0.0 -e PORT=<free port> <slug>
curl -s localhost:<free port>/health                 # {"ok":true}
docker exec <slug>-check whoami                      # not root
docker stop <slug>-check
```

**14. Dev workflow.** justfile recipes: `dev` (`HOST=127.0.0.1 PORT=<port> topcoat dev`), `check`, `fmt`, `test`, `migration` (`cargo run --quiet -- toasty migration generate`), `migrate` (`cargo run --quiet -- toasty migration apply`), `seed` (inserts the example notes, idempotent). `.zed/tasks.json` is committed with one task per local process, each calling a just recipe: dev, test, migrate. Every task sets `"cwd": "$ZED_WORKTREE_ROOT"`, `"use_new_terminal": true`, `"reveal": "always"`, `"hide": "never"`. `rust-analyzer.toml` sets `[rustfmt] overrideCommand = ["topcoat", "fmt", "--stdin", "--rustfmt"]`.
Check: `just dev`, then `curl localhost:<port>/health` answers. `jq` parses the tasks file, and every command is a just recipe.

Traps:
- `topcoat dev` reads `HOST` and `PORT` from the environment and, when that port is taken, moves to the next free one and prints it. A check that curls the recipe's port can hit whatever already holds it; read the port the dev server prints.

**15. A fresh clone passes CI.** A clone with no `.env`, with only `DATABASE_URL` exported (database `<pkg>_ci`), passes `just check`. Drop `<pkg>_ci` and `<pkg>_ci_test` afterwards. For GitHub, lint the workflow with `actionlint`; otherwise report not verified.

**16. README and AGENTS.md.** README has the title, the one-liner and how to run it: Postgres on the host, `just migrate`, `just dev`, the URL, and the islands note from goal 9. AGENTS.md has the stack, the commands (including the Zed tasks), the folder layout and these rules:
- crates only through `cargo add <crate>@<version>`; `topcoat` stays pinned with `=`, and upgrades follow the release's upgrade guide in their own commit
- schema changes only through `just migration`; never edit an applied migration
- every user-facing string through `t!`, in both `en.ftl` and `ar.ftl`; logical direction utilities only
- every shard and procedure authorizes and validates its own input
- components come from `topcoat ui add`; never hand-roll one it ships
- heavy client widgets are custom elements with JSON props until islands ship; no second interaction library
- routes and files are named for what the page is to the user, never for a UI mechanism and never numbered
- after UI changes, look at the pages with the browser tools available, at desktop and phone width, light and dark, `en` and `ar`
- working rules: no comments that narrate the code, Conventional Commits with no trailers, `just check` before each commit
Check: `grep -nE '\.bootstrap|artifacts|bootstrapper' README.md AGENTS.md` finds nothing; `grep -ciE 'cargo add|just migration|t!|shard|topcoat ui|narrat|trailer' AGENTS.md` is at least 6.

## Versions
`topcoat` and `topcoat-cli` 0.12.1, pinned exactly; the CLI and crate move together. Rust 1.99 in `rust-toolchain.toml` (Topcoat's MSRV). Toasty and `toasty-cli`: the version `topcoat new` 0.12.1 writes (0.11.0 when this was written), both pinned with `=`. The migration commands come from `toasty-cli` inside the app binary, so nothing extra is installed for them. Tailwind: the release Topcoat 0.12.1 verifies by default, or a `version` plus `version_checksum`. Other crates: `cargo add <crate>@<major.minor>`; resolved versions live in `Cargo.lock`, which is committed.

## Database
Pass the password only through the environment, never echo it. With setup.json at `<bootstrapper repo>/.bootstrap/setup.json`, check whether the database exists:
```
PGPASSWORD="$(jq -r .postgres.password <setup.json>)" psql -h "$(jq -r .postgres.host <setup.json>)" -p "$(jq -r .postgres.port <setup.json>)" \
  -U "$(jq -r .postgres.username <setup.json>)" -d postgres -tAc "select 1 from pg_database where datname='<pkg>'"
```
Create it with the same command and `-c 'CREATE DATABASE "<pkg>"'`. Then `just migrate` must apply every migration. Tests use `<pkg>_test` on the same server, which the test setup creates and keeps between runs.

## Run
- `cd <repo folder> && just dev`
- app: `http://127.0.0.1:<port>` (redirects to `/<locale>/`)
- schema: `just migration`, then `just migrate`
- checks: `just check`
