# __TITLE__

__ONE_LINER__

## Run

Needs: uv, just, node/npm, local Postgres and Redis.

```bash
cp .env.example .env   # fill in, skip if .env exists
just setup             # uv sync, npm ci, vendor JS, build CSS
just migrate
just run               # http://127.0.0.1:8000
just test
```
