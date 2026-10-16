# Stack registry
One row per stack. Match user input on id or alias. New stack: add a row and a stack file with sections Tools, Inputs, Source, Goals, Versions, Database, Run. A goal is an end state with a check. It may end with a Traps list: pitfalls from earlier runs, under the goal they blocked. When a check starts catching a trap, delete the trap. The Goals section opens with the versions its traps were last verified with. Every stack-specific tool, command and name lives in the stack file; SKILL.md stays stack-agnostic. File names use `_`, not `+`. No template files: the agent generates from Source and adapts until Goals pass. Never improvise a stack not listed.

| id | aliases | what | file |
|---|---|---|---|
| django+unpoly | django, django-cotton, basecoat | Django (ASGI), Celery, Channels, django-cotton, Unpoly, Alpine.js, django-basecoat, django-unicorn (high-interactivity parts only), Tailwind CSS, GCP-ready Docker files | [django_unpoly.md](django_unpoly.md) |
