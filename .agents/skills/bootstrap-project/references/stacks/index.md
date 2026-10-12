# Stack registry
One row per stack. Match user input on id or alias. New stack: add a row and a stack file with sections Inputs, Source, Goals, Hints, Versions, Database. File names use `_`, not `+`. No template files: the agent generates from Source and adapts until Goals pass. Never improvise a stack not listed.

| id | aliases | what | file |
|---|---|---|---|
| django+unpoly | django, django-cotton, basecoat | Django (ASGI), Celery, Channels, django-cotton, Unpoly, Alpine.js, django-basecoat, django-unicorn (high-interactivity parts only), Tailwind CSS, GCP-ready Docker files | [django_unpoly.md](django_unpoly.md) |
