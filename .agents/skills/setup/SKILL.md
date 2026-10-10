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

## state
.bootstrap/setup.json:
{"flow":"setup","steps":[{"id":"git","need":"required","status":"pending","result":null}]}
status: pending, done, failed, skipped.

## run
1. Read state file. Missing: create, all pending.
2. Sync with steps above. New: pending. Gone: drop.
3. Walk steps in order. Skip done. Skip opt skipped.
4. Call step. Read its report line.
   present, installed: done.
   skipped: skipped. failed: failed.
   Write status + line to file.
5. Step req and not done: stop.
   Say which, why. Say "run /setup again".
6. Step opt and not done: go on.
7. End: say state is in .bootstrap/setup.json.
