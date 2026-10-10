---
name: setup
description: Bootstrap dev env from zero. Use when user has no clear goal or fresh machine. Rerun resumes where it stopped.
---
# setup
Do nothing yourself. Only call skills.
Only file you touch: .bootstrap/setup.json.

## steps
Order matters. req = blocks. opt = continues.
- req  /ensure-installed git
- req  /ensure-installed claude-code
- req  /ensure-installed zed
- req  /ensure-installed delta
- req  /ensure-installed gh
- req  /ensure-installed uv
- req  /ensure-installed docker
- req  /ensure-installed just
- req  /ensure-installed gcloud
- req  /ensure-installed terraform
- req  /ensure-installed npx
- req  /ensure-git
- req  /ensure-runnable-docker
- req  /ensure-gcloud

## state
.bootstrap/setup.json:
{"flow":"setup","github":{"login":null,"email":null},"gcloud":{"config":null,"project":null},"steps":[{"id":"git","need":"required","status":"pending","result":null}]}
status: pending, done, failed, skipped.
github.login, github.email: chosen GitHub account and commit email. Set from /ensure-git report. Later skills read it.
gcloud.config, gcloud.project: chosen gcloud config and its project. Set from /ensure-gcloud report. Later skills read them.

## run
1. Read state file. Missing: create, all pending.
2. Sync with steps above. New: pending. Gone: drop. Missing github or gcloud key: add it, values null.
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
