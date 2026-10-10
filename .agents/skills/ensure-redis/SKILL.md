---
name: ensure-redis
description: Ensure redis accepts connections, with password. Use after docker ready. Finds, installs, or runs redis in docker. Saves connection to setup.json.
---
# ensure-redis

Check fails: give fix, wait, verify again. Loop until pass. Sudo or interactive cmd: tell user run `! <cmd>`.
User gives up: report failed.

## client
Need `redis-cli`. Missing: run via `docker run --rm --network host redis:7 redis-cli ...`, else install client pkg.

## find
Saved `redis` in `.bootstrap/setup.json` works: go to auth.
Else `redis-cli -h localhost -p 6379 ping` says `PONG` or `NOAUTH`: go to auth.
No: ask user, ask tool:
1 other port: ask port, probe. Fail: ask again.
2 install on system: OS pkg manager, start, enable on boot.
3 docker (need /ensure-runnable-docker): `docker run -d --name redis --restart always -p 6379:6379 -v redis-data:/data redis:7 redis-server --appendonly yes --requirepass <generated>`. Exists: start it, `docker update --restart always`. Port busy: ask other port.
Wait until ready.

## auth
Need host port password. Saved: use. `NOAUTH`: ask user for password.
Redis answers `PONG` with no password: ask user, ask tool:
1 generate password: set it, show once. System redis: tell user `! redis-cli config set requirepass <p>` then `config rewrite`. Docker: recreate container with `--requirepass`, same volume.
2 no password: use as is. Password null.
Verify: `redis-cli -h <h> -p <port> [-a <p> --no-auth-warning] ping` is `PONG`.
Probe: set, get, del key `_bootstrap_probe`.

## state
Only skill allowed to write `.bootstrap/setup.json`, only key `redis`:
`"redis":{"host":"localhost","port":6379,"password":"..."|null,"mode":"docker|system|external"}`

## report
Last line, exactly one:
`ensure-redis: done <host> <port>`
`ensure-redis: failed <port|install|docker|auth|prereq>: <reason>`

## never
Print password after first show. Run FLUSHALL, FLUSHDB, or touch other keys. Write .bootstrap except `redis` key.
