"""Write <repo>/.env from .bootstrap/setup.json without printing secrets.

usage: python3 -I write-env.py <setup.json> <repo_dir> <db_name> [--no-services]
--no-services: leave POSTGRES_DB and REDIS_HOST unset (sqlite + in-memory cache).
Prints only the keys written. File mode 600. Refuses to overwrite an existing .env.
"""
import json
import os
import secrets
import sys
from pathlib import Path


def main():
    setup_path, repo, db_name = sys.argv[1:4]
    no_services = "--no-services" in sys.argv[4:]
    env_path = Path(repo) / ".env"
    if env_path.exists():
        sys.exit(f"exists: {env_path}")
    setup = json.loads(Path(setup_path).read_text())
    pg = setup.get("postgres") or {}
    rd = setup.get("redis") or {}
    lines = {
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
        "DJANGO_DEBUG": "1",
    }
    if not no_services:
        lines.update({
            "POSTGRES_DB": db_name,
            "POSTGRES_HOST": pg.get("host") or "localhost",
            "POSTGRES_PORT": str(pg.get("port") or 5432),
            "POSTGRES_USER": pg.get("username") or "",
            "POSTGRES_PASSWORD": pg.get("password") or "",
            "REDIS_HOST": rd.get("host") or "localhost",
            "REDIS_PORT": str(rd.get("port") or 6379),
            "REDIS_PASSWORD": rd.get("password") or "",
        })
    body = "".join(f"{k}={json.dumps(v)}\n" for k, v in lines.items())
    fd = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(body)
    print("wrote .env keys:", " ".join(lines))


if __name__ == "__main__":
    main()
