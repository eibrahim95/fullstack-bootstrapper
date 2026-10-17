# Stack registry
One row per stack. Match user input on id or alias. New stack: add a row and a stack file with sections Tools, Inputs, Source, Baseline, Goals, Versions, Database, Run. A goal is an end state with a check. It may end with a Traps list: pitfalls from earlier runs, under the goal they blocked. When a check starts catching a trap, delete the trap. Baseline goals (numbered B1, B2...) are met in the first commit on `main`, so its CI is green; Goals land on the bootstrap branch, one commit each. The Baseline section opens with the versions every trap was last verified with. Every stack-specific tool, command and name lives in the stack file; SKILL.md stays stack-agnostic. File names use `_`, not `+`. No template files: the agent generates from Source and adapts until Goals pass. Never improvise a stack not listed.

| id | aliases | what | file |
|---|---|---|---|
| django+unpoly | django, django-cotton, basecoat | Django (ASGI), Celery, Channels, django-cotton, Unpoly, Alpine.js, django-basecoat, django-unicorn (high-interactivity parts only), Tailwind CSS, GCP-ready Docker files | [django_unpoly.md](django_unpoly.md) |
