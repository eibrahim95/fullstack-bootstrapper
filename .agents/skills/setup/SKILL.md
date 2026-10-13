---
name: setup
description: Bootstrap dev env from zero. Use when user has no clear goal or fresh machine. Rerun resumes where it stopped.
---
# setup
Do nothing yourself. Only call skills.
Only file you touch: .bootstrap/setup.json.
Exception: /ensure-postgres and /ensure-redis write their own key (password). Never copy it.

## steps
Order matters. req = blocks. opt = continues.
- req  /ensure-installed git
- req  /ensure-installed claude-code
- req  /ensure-installed zed
- req  /ensure-installed delta
- req  /ensure-installed gh
- req  /ensure-installed uv
- req  /ensure-installed python
- req  /ensure-installed docker
- req  /ensure-installed just
- req  /ensure-installed gcloud
- req  /ensure-installed terraform
- req  /ensure-installed npx
- req  /ensure-git
- req  /ensure-runnable-docker
- req  /ensure-gcloud
- req  /ensure-postgres
- req  /ensure-redis
- opt  /ensure-installed impeccable (only /build-html-prototype needs it)
- opt  /ensure-installed cookiecutter (needed by /bootstrap-project)
- opt  /ensure-mcp excalidraw (diagrams, project progress still uses Excalidraw)

## state
.bootstrap/setup.json:
{"flow":"setup","github":{"login":null,"email":null},"gcloud":{"config":null,"project":null},"postgres":{"host":null,"port":null,"username":null,"password":null},"redis":{"host":null,"port":null,"password":null},"steps":[{"id":"git","need":"required","status":"pending","result":null}]}
status: pending, done, failed, skipped.
step id = last word of the call: git, npx, python, ensure-git, impeccable, cookiecutter, excalidraw. opt step: need `optional`.
github.login, github.email: chosen GitHub account and commit email. Set from /ensure-git report. Later skills read it.
gcloud.config, gcloud.project: chosen gcloud config and its project. Set from /ensure-gcloud report. Later skills read them.

## run
1. Read state file. Missing: create, all pending.
2. Sync with steps above. New: pending. Gone: drop. Missing github, gcloud, postgres or redis key: add it, values null.
3. Walk steps in order. Skip done. Skip opt skipped.
4. Call step. Read its report line.
   present, installed, done: done.
   skipped: skipped. failed: failed.
   Write status + line to file.
   Step ensure-git done: write <login>, <email> from its line to github.login, github.email.
   Step ensure-gcloud done: write <config>, <project> from its line to gcloud.config, gcloud.project.
5. Step req and not done: stop.
   Say which, why. Say "run /setup again".
6. Step opt and not done: go on.
7. End: say state is in .bootstrap/setup.json.
