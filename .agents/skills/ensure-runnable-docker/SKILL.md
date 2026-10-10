---
name: ensure-runnable-docker
description: Ensure docker runs as normal user, no sudo. Use after docker installed. Fixes docker group on Linux, Docker Desktop on Windows/Mac.
---
# ensure-runnable-docker

Need docker on PATH. Missing: /ensure-installed docker.
Never run sudo. Never change groups yourself. Tell user, wait.

## check
`docker info` exit 0 and `docker run --rm hello-world` ok: done.

## fail
Read error.
- `permission denied` on docker.sock (Linux):
  user runs `! sudo usermod -aG docker $USER`
  then logout, login again (or reboot). Fresh shell. `id -nG` must list docker.
  Quick test w/o logout: `newgrp docker`.
- `Cannot connect to the Docker daemon` (Linux): `! sudo systemctl enable --now docker`.
- Windows: use Docker Desktop with WSL2 backend. Docker Desktop > Settings > Resources > WSL integration: enable distro. Run docker inside WSL, not as admin. Not in group `docker-users`: admin runs `net localgroup docker-users <user> /add`, then sign out, sign in.
- Mac: start Docker Desktop. Wait for whale idle.
Verify again. Still fails: say cause, fix.
User gives up: report failed.

## report
Last line, exactly one:
`ensure-runnable-docker: done`
`ensure-runnable-docker: failed <perm|daemon|prereq>: <reason>`

## never
Run sudo. Edit groups. Install tools. Write .bootstrap.
