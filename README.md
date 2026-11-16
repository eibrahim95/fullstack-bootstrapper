# Fullstack Bootstrapper

A local workflow that sets up a machine for AI agents, then bootstraps a full-stack app from a stack registry.

The first pass sets up the development environment: tools, services, and conventions an agent needs to work on a local machine. The second pass creates the app from a registered stack. Stacks are pluggable. New stacks are added to the registry; agents do not invent one-off setups.

Work is split across skills. Skills depend on each other and hand work off when their part is done. Every path starts at `/setup`.

## Stacks

| Id | Stack |
| --- | --- |
| `django+unpoly` | Django (ASGI), Celery, Channels, django-cotton, Unpoly, Alpine.js, django-basecoat, django-unicorn (high-interactivity parts only), Tailwind CSS |
| `fastify+trpc+react` | TypeScript monorepo (pnpm, Turborepo, Node 24): Fastify, tRPC, Drizzle on Postgres, React, Vite, TanStack Query, React Router, Tailwind CSS, shadcn/ui |
| `topcoat` | Rust 1.99: Topcoat 0.12 (server-rendered, runtime and shards), Toasty on Postgres, Tailwind CSS 4, Topcoat UI, Fluent en/ar |

`django+unpoly` is the first registered stack. Django owns the server. django-cotton, Unpoly, Alpine.js, and django-basecoat cover server-rendered UI, progressive enhancement, and small client behavior. django-unicorn is for high-interactivity parts only (live server state, many interdependent fields, polling). Tailwind CSS is the styling layer. Celery runs background tasks and Channels serves websockets, both on the local Redis. The repo comes from cookiecutter-django with Docker and GCP options on, so it carries the production Dockerfile and compose files.

`fastify+trpc+react` is a TypeScript monorepo with an API and a single-page app. Fastify serves tRPC procedures, and the React app imports the router's type, so a server change that breaks a caller fails the type-check. Drizzle queries Postgres, whose schema changes through plain SQL migrations. The web app uses Vite, TanStack Query, React Router, Tailwind CSS 3 and shadcn/ui. The API ships as a container.

`topcoat` is a server-rendered Rust app on Topcoat from the Tokio project. Pages are mostly hypermedia: `view!` components, with the Topcoat runtime and server-rendered shards for small interactions. Islands are on Topcoat's roadmap; until they ship, a heavy widget is a custom element with JSON props. Toasty talks to Postgres, Tailwind and Topcoat UI give the look, and Fluent carries Arabic (RTL) and English. Topcoat is pre-1.0, so versions are pinned exactly.

## Skills

Skills are the unit of work. A skill does one job, uses what earlier skills produced, and names the next skill when it hands off.

| Skill | Role |
| --- | --- |
| `/setup` | Entry point. Installs the tools the machine needs, records progress in `.bootstrap/setup.json`, and resumes where it stopped. |
| `/project` | Runs the project pipeline below for one project, in order, and resumes at the first step not done. |

Everyone starts at `/setup`, including when the next step is not obvious. After `/setup`, use `/project`.

## Project pipeline

Each project lives in `.bootstrap/projects/NN/` with a `status.json` state machine. Each skill below does one step, writes its own artifact directory, and advances the state. `/project` calls them in order.

| State reached | Skill | Artifact |
| --- | --- | --- |
| `idea-captured` | `/new-project` | `idea/` |
| `idea-validated` | `/validate-idea` | `validation/` |
| `spec-created` | `/write-spec` | `spec/` |
| `journey-drawn` | `/draw-journeys` | `journeys/` |
| `wireframes-created` | `/draw-wireframes` (optional) | `wireframes/` |
| `html-prototype-created` | `/build-html-prototype` (optional) | `html-prototype/` |
| `project-bootstrapped` | `/bootstrap-project` | repo in a parent directory you pick, with the artifacts moved to `artifacts/` beside it |

Steps run in order up to `/draw-wireframes`. `/build-html-prototype` and `/bootstrap-project` both start after that, each in its own background thread started by `/project`, so they run in parallel. A prototype that finishes after bootstrap moves itself into `artifacts/`. Rerun `/project` to see progress.

Support skills: `/ensure-installed <tool>`, `/ensure-mcp <server>`, and the `/ensure-*` skills that `/setup` calls.

## Attribution

A lot of the workflow here comes from two projects we are grateful for.

- **[mattpocock/skills](https://github.com/mattpocock/skills)** — small, composable agent skills for real engineering. Once a project is bootstrapped, we use many of those skills directly.
- **[me2resh/apexyard](https://github.com/me2resh/apexyard)** — an ops repo for governing agent-built work: tickets, review, and merge gates so code can ship safely.

Thank you to [Matt Pocock](https://github.com/mattpocock) and [Ahmed (me2resh)](https://github.com/me2resh) for the ideas this workflow is built on.

## License

Apache License 2.0. See [LICENSE](LICENSE).
