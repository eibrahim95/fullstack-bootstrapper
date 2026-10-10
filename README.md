# Fullstack Bootstrapper

A local workflow that sets up a machine for AI agents, then bootstraps a full-stack app from a stack registry.

The first pass sets up the development environment: tools, services, and conventions an agent needs to work on a local machine. The second pass creates the app from a registered stack. Stacks are pluggable. New stacks are added to the registry; agents do not invent one-off setups.

Work is split across skills. Skills depend on each other and hand work off when their part is done. Every path starts at `/setup`.

## Stacks

| Id | Stack |
| --- | --- |
| `cotton` | Django, django-cotton, Unpoly, Alpine.js, django-basecoat, Tetra, Tailwind CSS |

`cotton` is the first registered stack. Django owns the server. django-cotton, Unpoly, Alpine.js, django-basecoat, and Tetra cover server-rendered UI, progressive enhancement, and small client behavior. Tailwind CSS is the styling layer.

## Skills

Skills are the unit of work. A skill does one job, uses what earlier skills produced, and names the next skill when it hands off.

| Skill | Role |
| --- | --- |
| `/setup` | Entry point. Installs the tools the machine needs, records progress in `.bootstrap/setup.json`, and resumes where it stopped. Stack selection comes later. |

Everyone starts at `/setup`, including when the next step is not obvious.

## Attribution

A lot of the workflow here comes from two projects we are grateful for.

- **[mattpocock/skills](https://github.com/mattpocock/skills)** — small, composable agent skills for real engineering. Once a project is bootstrapped, we use many of those skills directly.
- **[me2resh/apexyard](https://github.com/me2resh/apexyard)** — an ops repo for governing agent-built work: tickets, review, and merge gates so code can ship safely.

Thank you to [Matt Pocock](https://github.com/mattpocock) and [Ahmed (me2resh)](https://github.com/me2resh) for the ideas this workflow is built on.

## License

Apache License 2.0. See [LICENSE](LICENSE).
