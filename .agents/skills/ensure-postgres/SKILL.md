---
name: ensure-postgres
description: Ensure postgres accepts connections with a user that can create databases. Use after docker ready. Finds, installs, or runs postgres in docker. Saves connection to setup.json.
---
# ensure-postgres

Check fails: give fix, wait, verify again. Loop until pass. Sudo or interactive cmd: tell user run `! <cmd>`.
User gives up: report failed.

## client
Need `psql`, `pg_isready`. Missing: run via `docker run --rm --network host postgres:17 <cmd>`, else install client pkg.

## find
Saved `postgres` in `.bootstrap/setup.json` works: go to user.
Else `pg_isready -h localhost -p 5432` ok: go to user.
No: ask user, ask tool:
1 other port: ask port, probe. Fail: ask again.
2 install on system: OS pkg manager, start, enable on boot.
3 docker (need /ensure-runnable-docker): `docker run -d --name postgres --restart always -p 5432:5432 -v postgres-data:/var/lib/postgresql/data -e POSTGRES_PASSWORD=<generated> postgres:17`. Exists: start it, `docker update --restart always`. Port busy: ask other port.
Wait until ready.

## user
Need host port username password. Saved: use. Else ask for existing creds, or create role `bootstrap` with generated password, show it once:
`CREATE ROLE bootstrap LOGIN CREATEDB PASSWORD '<p>'`
Docker: `docker exec postgres psql -U postgres -c ...`. Else user runs `! sudo -u postgres psql -c ...`.
Verify login. `select rolcreatedb, rolsuper from pg_roles where rolname = current_user` must be `t`, `f`. Else user runs as superuser `ALTER ROLE <u> CREATEDB NOSUPERUSER;`.
Probe: create db, drop it.

## state
Only skill allowed to write `.bootstrap/setup.json`, only key `postgres`:
`"postgres":{"host":"localhost","port":5432,"username":"bootstrap","password":"...","mode":"docker|system|external"}`

## report
Last line, exactly one:
`ensure-postgres: done <host> <port> <username>`
`ensure-postgres: failed <port|install|docker|user|role|prereq>: <reason>`

## never
Print password after first show. Drop other databases. Write .bootstrap except `postgres` key.
