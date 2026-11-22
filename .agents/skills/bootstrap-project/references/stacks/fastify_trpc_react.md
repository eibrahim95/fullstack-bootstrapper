# Stack: fastify+trpc+react
A TypeScript monorepo: a Fastify API with typed tRPC calls end to end, and a React single-page app, with the API ready to ship as a container.

| part | role |
|---|---|
| pnpm workspace + Turborepo, Node 24 | one repo, `apps/server` and `apps/web`, one lockfile, tasks run across both |
| Fastify 5 | HTTP server: `/health`, tRPC under `/trpc` |
| tRPC 11 | API procedures. The web app imports the router's type, so a server change that breaks a caller fails the web type-check. |
| zod 4 | input validation on every procedure, and the environment check at boot |
| Drizzle ORM on postgres.js | typed queries. The schema in TypeScript mirrors the SQL migrations. |
| SQL migrations | plain timestamped `.sql` files, applied in order by a small runner that records each one |
| pino | logs (pretty in development only) |
| React 18 + Vite 6 (SWC) | the web app |
| TanStack Query 5 + tRPC React Query | data fetching and caching |
| React Router 6 | pages |
| Tailwind CSS 3 + shadcn/ui (Radix), lucide icons | styling and components |
| vitest 4 | tests: Postgres-backed on the server, jsdom + Testing Library on the web |
| ESLint 9, Prettier, husky, lint-staged, commitlint | lint, format, Conventional Commit messages |
| Postgres | on the host, from /setup. Redis from /setup is not used. |

Not in this stack: sign-in, background jobs, websockets. Add them per project.
Network: GitHub, the npm registry, Docker Hub.

## Names used below
| name | means |
|---|---|
| `<title>`, `<one_liner>`, `<slug>` | from the project's status.json |
| `<pkg>` | the database name: slug with `-` replaced by `_` |
| `<parent>`, repo folder | the parent folder the user chose, and `<parent>/<slug>` |
| setup.json | `.bootstrap/setup.json` in the bootstrapper repo (Postgres, GitHub account) |
| `<x>` | the answer to input `x` from the table below |

## Tools
| tool | check | fix |
|---|---|---|
| node 24 | `node -v` prints `v24.` (run `nvm use 24` first if nvm manages Node) | `/ensure-installed node`, then `nvm install 24` |
| corepack | `corepack --version` | ships with Node 24. Node 25 dropped it: switch to 24. |
| pnpm 10 | `pnpm -v` prints `10.` | `corepack enable pnpm` |
| jq, psql, curl | `command -v jq psql curl` | install with the system package manager |
| docker | `docker info` | /ensure-runnable-docker |

## Inputs
| key | means | recommend |
|---|---|---|
| api_port | port the API listens on in development | first free port from 3100 up: `ss -ltn "sport = :<p>"` shows no LISTEN |
| web_port | port the Vite dev server listens on | first free port from 5200 up, same check |
| ci | CI provider | `Github`. Choices: Github, None |

## Source: how the repo is generated
There is no template generator for the whole repo. These commands create the bare workspace; the agent adapts it until every goal passes. Run them with Node 24 active.
1. Root:
   ```
   mkdir -p <repo folder>/apps && cd <repo folder>
   corepack enable pnpm
   echo 24 > .nvmrc
   printf 'packages:\n  - "apps/*"\n' > pnpm-workspace.yaml
   pnpm init
   pnpm pkg set name=<slug> type=module engines.node='>=24' packageManager=pnpm@$(pnpm -v)
   pnpm pkg set private=true --json
   ```
2. Web, from `apps/`: `pnpm create vite@6 web --template react-swc-ts`.
3. Server: `mkdir apps/server && cd apps/server && pnpm init`, then `pnpm pkg set name=server type=module` and `pnpm pkg set private=true --json`. Remove `packageManager`, `version` and `main` from both app package.json files; the root keeps `packageManager`.
4. `pnpm install` at the root.

Traps:
- create-vite 9 (`@latest`) turned `--template react-swc-ts` into a plain TypeScript app on Vite 8 and TypeScript 6. create-vite 6 gives the React SWC template on Vite 6, with React 19 (goal 1 sets it back to 18).
- `pnpm pkg set private=true` writes the string `"true"`. Use `--json` for booleans, and only for those: `--json` applies to every pair on the line.
- `pnpm init` stamps `packageManager` into every package it creates.

## Baseline: in the first commit
These go into the first commit on `main`, so its first CI run is green. Everything else waits for the Goals branch.
Traps last verified 2026-10-18 with Node 24.18.0, pnpm 10.16.0, create-vite 6, React 18.3.1, Vite 6.4.4, TypeScript 5.8.3, Tailwind 3.4.19, shadcn CLI 2.3.0, tRPC 11.19.0, TanStack Query 5.104.4, React Router 6.30.6, Fastify 5.12.7, Drizzle 0.45.4, postgres.js 3.4.9, zod 4.6.7, tsup 9.0.0, vitest 4.1.12, ESLint 9.39.5, Turborepo 2.11.9.

**B1. Workspace tasks and CI.** Turborepo at the root, with tasks `build` (`dependsOn: ["^build"]`, outputs `dist/**`), `lint`, `check-types`, `test` (`passThroughEnv: ["DB_*"]`) and `dev` (persistent, no cache). Each app has `lint`, `check-types`, `test` and `build` scripts that pass on the bare scaffold; the server has a `src/index.ts` that starts Fastify with `GET /health`, and its tests run `vitest run --passWithNoTests` until goal 5. The web app's `check-types` is `tsc -b`.
CI (from the `ci` input) is one GitHub workflow on pull requests and pushes to `main`. It sets `DB_HOST=localhost`, `DB_PORT=5432`, `DB_USERNAME=postgres`, `DB_PASSWORD=postgres` and `DB_NAME=app` once, at workflow level. Steps: `actions/checkout@v7`, `pnpm/action-setup@v6`, `actions/setup-node@v7` with `node-version-file: .nvmrc` and `cache: pnpm`, start the runner's Postgres, `pnpm install --frozen-lockfile`, `pnpm turbo run lint check-types test build`, then a "server bundle loads" step. No Docker, `services:` containers or `.env`. If `ci=None`, there is no CI: report this goal as not verified.
The bundle step runs the built server for 15 seconds and fails only on a module-loading error. A config or database error means the bundle loaded; exit 124 (still running) is a pass:
```
set +e; timeout 15 node apps/server/dist/index.js > boot.log 2>&1; set -e
! grep -qE 'Dynamic require of|ERR_MODULE_NOT_FOUND|Cannot find (module|package)' boot.log
```
Check:
```
pnpm turbo run lint check-types test build                     # every task successful
grep -niE 'docker|compose|services:|\.env' <CI file>           # nothing
```
Lint the workflow with `actionlint`, or `docker run --rm -v $PWD:/repo -w /repo rhysd/actionlint` if it is not installed.

Traps:
- GitHub's `ubuntu-latest` ships PostgreSQL with the service stopped: `sudo systemctl start postgresql.service`, then `sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres'"`, because TCP logins need a password.
- Turborepo hides environment variables a task does not declare. Without `passThroughEnv` on `test`, CI's `DB_*` never reach the tests.

**B2. Git hooks.** husky is installed by the root `prepare` script. `pre-commit` runs `pnpm exec lint-staged`, which runs Prettier on staged files. `commit-msg` runs `pnpm exec commitlint --edit "$1"` with `@commitlint/config-conventional`. `.prettierrc` sets `printWidth: 120` and `singleQuote: true`; `.prettierignore` lists `dist` and `pnpm-lock.yaml`.
Check: on a scratch commit, the message `bad message` is refused and `chore: try hooks` passes; `pnpm exec prettier --check .` passes. Undo the scratch commit before the real first commit.

Traps:
- `commitlint.config.js` is ESM. Without `"type": "module"` on the root package, Node warns on every commit.

## Goals
Server tests run on Postgres from `apps/server/.env` locally and from the workflow env in CI. Checks that start the app need the database created and migrated.
A browser check means using the browser tools available to you, the way a person would: open the page, click, look. Never write a script that drives a browser. With no browser tools, report that goal as not verified.

### Dependencies
**1. Packages and versions.** Every dependency is added with `pnpm add <pkg>@<major>` (`-D` for dev tools) in the app that uses it, and removed with `pnpm remove`. Never write a dependency into package.json by hand. Majors match this stack: React 18 with its types, Vite 6, TypeScript 5, Tailwind 3, tRPC 11, TanStack Query 5, React Router 6, Fastify 5, Drizzle 0.45, zod 4 in both apps, vitest 4, ESLint 9, `@types/node` 24.
- server: fastify, @trpc/server, drizzle-orm, postgres, zod, pino, pino-pretty, close-with-grace, @fastify/cors, dotenv; dev: tsx, tsup, vitest, typescript, @types/node, eslint, @eslint/js, typescript-eslint, globals
- web: @trpc/client, @trpc/react-query, @tanstack/react-query, react-router-dom, zod, and what the shadcn CLI adds; dev: tailwindcss, postcss, autoprefixer, vitest, jsdom, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, @types/node, and `server@workspace:*`
- root, dev: turbo, typescript, prettier, husky, lint-staged, @commitlint/cli, @commitlint/config-conventional
```
pnpm install --frozen-lockfile                                     # lock matches
ls package-lock.json yarn.lock apps/*/package-lock.json 2>/dev/null # nothing
pnpm -r ls --depth 0 --json | jq -r '.[].dependencies // {} | to_entries[] | "\(.key) \(.value.version)"' | grep -E '^(react|fastify|@trpc/server|drizzle-orm|zod) '   # majors above
```

### Server
**2. Environment from `.env`, checked at boot.** `src/env.ts` reads the environment through a zod schema: `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD` and `DB_NAME` are required, `PORT` defaults to `<api_port>`, `WEB_ORIGIN` defaults to `http://localhost:<web_port>`, `NODE_ENV` defaults to development. A missing variable throws an error naming every missing key; there is no fallback database. `apps/server/.env` is written from setup.json without being shown, mode 600, with `DB_NAME=<pkg>`. `.env.example` lists the keys with empty values.
```
stat -c %a apps/server/.env                    # 600
grep -c '=.' apps/server/.env.example          # 0
cd /tmp && env -i PATH=$PATH HOME=$HOME node <repo folder>/apps/server/dist/index.js   # exits 1, names all five DB_ keys
```

Traps:
- dotenv reads `.env` from the current folder, so run the missing-variables check from outside `apps/server`.

**3. Database and migrations.** Migrations are SQL files in `apps/server/migrations/`, named `YYYYMMDDHHMM_<snake_name>.sql`, each starting with two comment lines: the name, then what it changes and why. `pnpm migration <name>` creates that stub and refuses a name that exists. `pnpm migrate` applies the pending files in name order, each in its own transaction, recording `name`, a sha256 `checksum` and `applied_at` in `migration_log`. A file whose checksum changed after it was applied stops the run with a message to write a new migration. `src/db/schema.ts` (Drizzle) mirrors the SQL; drizzle-kit does not generate migrations. One example table, `note` (`id serial`, `body text`, `created_at timestamptz`), so the app has one real read and write.
```
pnpm migrate; pnpm migrate                     # the second run applies nothing
echo '-- x' >> <the applied file>; pnpm migrate # fails: changed after it was applied (restore the file after)
```

**4. API.** `src/app.ts` exports `buildServer(env, db, ping)`, used by `src/index.ts` and by tests. It registers CORS for `WEB_ORIGIN`, tRPC at `/trpc` with the Fastify adapter, and `GET /health`, which pings the database and returns `{"ok":true}`. Procedures: `note.list` (newest first) and `note.add` (zod: trimmed, 1 to 500 characters). Logs use pino, pretty only in development, off in tests. `index.ts` closes Fastify and the database pool on shutdown with close-with-grace.
The router's import graph uses no Node globals, because the web app type-checks it: the database client takes a plain config object, and only `env.ts` and `index.ts` touch `process`.
```
curl -s localhost:<api_port>/health            # {"ok":true}
curl -s localhost:<api_port>/trpc/note.list    # {"result":{"data":[...]}}
```

Traps:
- If the router's imports reach `process` (for example the database client taking the env type), the web type-check fails with TS2591 and `Cannot find namespace 'NodeJS'` in server files.
- Ports 3000 and 3003 are often taken by other local tools; that is why the ports are inputs.

**5. Server tests on Postgres.** A vitest global setup creates `<DB_NAME>_test` on the same server if it is missing and migrates it. Tests call procedures through `createCallerFactory` and HTTP through `app.inject`. They cover: a note added and listed first, an empty note refused, `/health`, and the environment error. No database mocks.
Check: `pnpm --filter server test` passes, twice in a row (the test database is reused).

**6. Build and bundle.** tsup builds ESM for `node24` from named entries `index` (`src/index.ts`) and `migrate` (`scripts/migrate.ts`, a thin call into `src/db/migrate.ts`), so the output is `dist/index.js` and `dist/migrate.js`. Everything the server imports at run time is in `dependencies`.
```
pnpm --filter server build && ls apps/server/dist/index.js apps/server/dist/migrate.js
PORT=<free port> timeout 8 node --env-file=apps/server/.env apps/server/dist/index.js; echo $?   # 124, no module errors
```

Traps:
- Entries given as an array from two folders make tsup write `dist/src/index.js` and `dist/scripts/migrate.js`, and `node dist/index.js` fails.

### Web
**7. Typed client.** The web app has `server@workspace:*` as a dev dependency and imports `type AppRouter` from `server/router`, exposed through the server's `exports["./router"].types` pointing at `src/router.ts`. The tRPC React client uses `httpBatchLink` on `/trpc`; Vite's dev server proxies `/trpc` to `<api_port>` and listens on `<web_port>` with `strictPort`. The built web bundle contains no server code.
```
pnpm --filter web build && grep -lE 'drizzle|fastify|postgres' apps/web/dist/assets/*.js   # nothing
```
Also: rename `note` in the server router (on a file copy, restored after; never `git stash`) and `pnpm --filter web check-types` fails; after restoring it passes.

Traps:
- create-vite's root `tsconfig.json` has `"files": []`, so `tsc --noEmit` there checks nothing and passes. `check-types` must be `tsc -b`.

**8. Tailwind 3 and shadcn/ui.** Tailwind 3 runs through PostCSS with autoprefixer; `content` lists `./index.html` and `./src/**/*.{ts,tsx}`. shadcn/ui is set up with the `shadcn@2.3.0` CLI (`init -d`: new-york style, CSS variables), and components are added with the same CLI into `src/components/ui`: at least button, card, input and dropdown-menu. The `@` alias to `src` is set in the root and app tsconfig and in Vite. `tailwind.config.ts` imports `tailwindcss-animate`.
```
grep -c 'hsl(var' apps/web/tailwind.config.ts                                   # 0
pnpm --filter web build && grep -o '\.bg-background{[^}]*}' apps/web/dist/assets/*.css   # background-color:var(--background)
```

Traps:
- `shadcn@2.10` `init -d` fails on Tailwind 3 with `tailwind: Required`. Use 2.3.0.
- shadcn 2.3.0 writes today's registry colours as `oklch(...)` values but keeps the `hsl(var(--x))` wrapper in the Tailwind config. The result is invalid, so every colour is transparent. Use `var(--x)` in the config.
- `tailwindcss init` writes `content: []`, which builds no utility classes.
- Vite's dev server does not pick up `tailwind.config.ts` changes. Restart it.

**9. App shell and pages.** A header with the app title, nav links (React Router `NavLink`, active state shown) and the theme menu; content in a centred container with a max width. Two routes: `/`, the notes page (a form plus the list, with loading, empty and error states, labelled as example data), and `/about`, a placeholder that says so. Routes and page files are named for what the page is to the user. Every control is a shadcn component.
Check, in the browser: add a note; it appears first and stays after a reload. `/about` renders. At desktop and phone width, in light and dark, nothing overflows sideways, touches the viewport edge or shows as a bare unstyled control.

**10. Dark mode.** Two themes, light and dark; there is no "system" choice. With nothing stored, `prefers-color-scheme` picks the starting theme; once the user switches, the choice is kept in `localStorage` and wins. An inline script in `index.html` sets the `dark` class before first paint (stored choice, else the media query), so there is no flash; `color-scheme` follows. The control is one shadcn button with an icon and a label, switching between the two.
Check, in the browser: with nothing stored, the page follows the OS setting; switch to Dark and reload: the page is dark from the first paint; the control offers no third option. In both themes the shell's computed `background-color` is a colour, not `rgba(0, 0, 0, 0)`.

**11. Web tests.** vitest with jsdom, Testing Library and `@testing-library/jest-dom/vitest`, configured in `vite.config.ts` (imported from `vitest/config`). One component test drives the note form like a user: type, submit, field cleared; and the button is disabled while the field is empty.
Check: `pnpm --filter web test` passes.

### Quality and delivery
**12. Lint and format.** ESLint 9 flat config in each app with typescript-eslint; the web app adds react-hooks and react-refresh, with `react-refresh/only-export-components` off for `src/components/ui` only. Both run with `--max-warnings=0`.
```
pnpm turbo run lint && pnpm exec prettier --check .
```

Traps:
- shadcn's `button.tsx` exports `buttonVariants` beside the component, which react-refresh warns on.
- A component defined in `main.tsx` trips react-refresh too; keep the provider tree in its own file.
- The shadcn Tailwind config uses `require("tailwindcss-animate")`, which typescript-eslint forbids. Import it.

**13. A fresh clone passes CI.** A clone with no `.env`, with only the `DB_*` values exported (from setup.json, `DB_NAME=<pkg>_ci`), passes `pnpm install --frozen-lockfile`, `pnpm turbo run lint check-types test build` and the bundle step from B1. Drop `<pkg>_ci` and `<pkg>_ci_test` afterwards. For GitHub, lint the workflow with `actionlint`; otherwise report not verified.

**14. API container.** `apps/server/Dockerfile`, multi-stage on `node:24-slim`. The build stage enables corepack, copies the root manifests and the server's package.json, runs `pnpm install --frozen-lockfile --ignore-scripts --filter server`, copies the server source, builds, and runs `pnpm --filter server deploy --prod --legacy /out`. The run stage copies `node_modules` and `package.json` from `/out`, plus `dist` and `migrations`, sets `NODE_ENV=production`, runs as `node`, and starts `node dist/index.js`. `.dockerignore` excludes `node_modules`, `dist`, `.env`, `.git` and `.turbo`.
```
docker build -f apps/server/Dockerfile -t <slug>-server .
docker run -d --rm --name <slug>-check --network host --env-file apps/server/.env -e PORT=<free port> <slug>-server
curl -s localhost:<free port>/health                 # {"ok":true}
docker exec <slug>-check node dist/migrate.js        # exit 0
docker exec <slug>-check whoami                      # node
docker stop <slug>-check
```
`--ignore-scripts` keeps the root `prepare` (husky) out of the image build.

**15. Dev workflow.** Root scripts: `dev` (turbo runs the API with `tsx watch` and Vite together), `build`, `lint`, `check-types`, `test`, `format`, `migrate` and `migration`. `.zed/tasks.json` is committed with one task per local process, each calling a root script: dev, test, migrate. Every task sets `"cwd": "$ZED_WORKTREE_ROOT"`, `"use_new_terminal": true`, `"reveal": "always"`, `"hide": "never"`; `dev` allows concurrent runs, tests do not.
Check: `pnpm dev`, then `curl localhost:<api_port>/health` and `curl -s localhost:<web_port>/trpc/note.list` (through the proxy) both answer. `jq` parses the tasks file, and every command is a root script.

### Repo files
**16. `.gitignore`.** Ignores `node_modules`, `dist`, `.env`, `.turbo`, `*.tsbuildinfo` and `coverage`. Does not ignore `.zed/` or `pnpm-lock.yaml`.
```
git check-ignore --no-index apps/server/.env apps/web/dist/x node_modules/x | wc -l   # 3
git check-ignore --no-index .zed/tasks.json pnpm-lock.yaml                            # exits 1
```

**17. README and AGENTS.md.** README has the title, the one-liner and how to run it: Postgres on the host, `nvm use`, `pnpm install`, `pnpm migrate`, `pnpm dev`, and the two URLs. AGENTS.md has the stack, the commands (including the Zed tasks), the folder layout and these rules:
- dependencies only through `pnpm add <pkg>@<major>` in the app that uses them
- schema changes only through `pnpm migration <name>`: never edit an applied migration, write a new one, and update `schema.ts` in the same commit
- every procedure validates its input with zod; the router's imports never touch Node globals
- shadcn components come from the CLI (2.3.0, for Tailwind 3); no second component library, and never hand-roll a component shadcn ships
- routes and files are named for what the page is to the user, never for a UI mechanism (modal, drawer) and never numbered
- after UI changes, look at the pages with the browser tools available, at desktop and phone width, light and dark
- working rules: no comments that narrate the code, Conventional Commits with no trailers, lint, type-check and test before each commit
Check: `grep -nE '\.bootstrap|artifacts|bootstrapper' README.md AGENTS.md` finds nothing; `grep -ciE 'pnpm add|pnpm migration|zod|shadcn|narrat|trailer' AGENTS.md` is at least 6.

## Versions
Majors are fixed by this stack (goal 1). Within a major, `pnpm add <pkg>@<major>` picks the newest release and writes the range; resolved versions live in `pnpm-lock.yaml`. The shadcn CLI is the one exact pin, `shadcn@2.3.0`, until a later 2.x is verified on Tailwind 3.

## Database
Pass the password only through the environment, never echo it. With setup.json at `<bootstrapper repo>/.bootstrap/setup.json`, check whether the database exists:
```
PGPASSWORD="$(jq -r .postgres.password <setup.json>)" psql -h "$(jq -r .postgres.host <setup.json>)" -p "$(jq -r .postgres.port <setup.json>)" \
  -U "$(jq -r .postgres.username <setup.json>)" -d postgres -tAc "select 1 from pg_database where datname='<pkg>'"
```
Create it with the same command and `-c 'CREATE DATABASE "<pkg>"'`. Then `pnpm migrate` must apply every migration. Tests use `<pkg>_test` on the same server, which the test setup creates and keeps between runs.

## Run
- `cd <repo folder> && nvm use && pnpm dev`
- web: `http://localhost:<web_port>`, API: `http://localhost:<api_port>`
- schema: `pnpm migration <name>`, then `pnpm migrate`
- checks: `pnpm turbo run lint check-types test build`
