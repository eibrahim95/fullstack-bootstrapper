---
name: project
description: Run the project pipeline from idea to bootstrapped app. Use when user wants to build an app, or continue a project. Rerun resumes at first step not done. Hands html-prototype and bootstrap to background threads, in parallel.
---
# project
Do nothing yourself. Only call skills.
Only file you touch: `.bootstrap/projects/NN/status.json`, only through `P` = `python3 -I .agents/skills/project/scripts/status.py .bootstrap/projects/NN` (locks, re-reads: background threads write it too). You write only: step `skipped`, step `thread`, reset of a dead `running` step to `pending`.
Other skills own their step. Never copy their artifacts.

## steps
Order matters. Skill gets arg NN.
| step id | skill | how |
|---|---|---|
| idea | /new-project | here |
| validation | /validate-idea | here |
| spec | /write-spec | here |
| journeys | /draw-journeys | here |
| wireframes | /draw-wireframes (optional) | here |
| html-prototype | /build-html-prototype (optional) | handover thread |
| bootstrap | /bootstrap-project | handover thread |
Steps 1-5 strictly sequential, in this thread. html-prototype and bootstrap both need only wireframes (bootstrap: journeys if wireframes skipped). They run in parallel, each in own top-level thread.
Step status: pending, running, done, failed, skipped.

## pick
Arg `NN` or slug: use it. Missing: error.
No arg: list `.bootstrap/projects/*/status.json`: id, title, state, next step(s) (first not done, not skipped; after wireframes both parallel ones, with `running` + thread shown). Ask which, or `new`.
`new`, or none exist: call /new-project, then continue with the NN it made.

## progress
Draw project progress on Excalidraw canvas after every skill finishes, after launching threads, on stop, and when listing a project.
Nothing printed in chat except one line. Spec: [references/progress.md](references/progress.md).
No Excalidraw MCP: fallback in same file, and say `/ensure-mcp excalidraw`.

## run
1. Read status.json.
2. Walk steps idea..wireframes in order. Skip done. Skip skipped.
3. Before wireframes, ask once: `Do wireframes or skip?`
   Skip: `P step wireframes status=skipped result="project: skipped NN"`. Nothing else.
4. Call step skill with NN. Read its report line.
   Re-read status.json after: skill wrote it.
   Draw progress (see progress).
5. Step `failed`, or skill reports `pending` (wireframes not approved yet), or skill needs input you cannot get: stop.
   Say which skill, why. Say "run /<skill> NN, then run /project NN again".
   Validation RED or failed: also say user can run `/validate-idea NN override`.
6. Step done: next.
7. Reached html-prototype and bootstrap: go to fan-out.

## fan-out
Both threads start together. Collect every answer first, so threads never wait on a user.
1. Per step, by status: `done` or `skipped`: leave. `running`: show its `thread`, do not launch again. `pending` or `failed`: launch.
2. wireframes `skipped`: html-prototype needs the inventory. `P step html-prototype status=skipped result="project: skipped NN (no wireframes)"`, say why.
3. Ask one round, recommended answers, only for steps to launch:
   html-prototype: do it or skip? Implementer model, reviewer model (different, per `.agents/skills/delegate/references/choose.md`). If `html-prototype/` exists in project dir: archive, wipe, or stop.
   bootstrap: parent dir (recommend `~/Projects/<slug>`, must be missing or empty), slug (recommend status.json `slug`), stack (one stack: say it), every stack file `inputs` row (read `.agents/skills/bootstrap-project/references/stacks/`, recommended answer each, no-default rows must be answered), create database `<slug>` on setup.json postgres (y/n), then ask `approved`: show what thread will create (repo dir, artifacts dir, stack, db) and ask OK.
   Check parent rule here. Violation: ask again.
4. Call /handover once per launched step, one after the other, before replying. Handover prompt stands alone:
   repo dir; project NN and title; exact call `/build-html-prototype NN models=<impl>,<rev> out=<choice>` or `/bootstrap-project NN parent=<p> slug=<s> stack=<id> <input>=<answer>... db=<yes|no> approved=yes` (quote answers with spaces); answers are final, no user watching, never ask, missing input = report failed; the other step runs in a parallel thread and shares status.json, so write only through the skill; finish with the skill's report line. No passwords in prompt.
   Keep returned name/id. `P step <id> thread="<name> <id>"`.
5. Draw progress. Then say, last in reply: both threads running, how to watch (from /handover output), `run /project NN again to see progress`. Stop. Do not poll.

## rerun
`running` step: show `thread`, tell user to check it (`claude logs <id>`). Do not relaunch.
User says a thread is dead: `P step <id> status=pending thread=null`, then launch it again (fan-out 3-4, ask only what is missing).
`failed` step: say which skill and why, say `/<skill> NN` or `/project NN` to retry.
Both parallel steps `done` or `skipped`: end.
Bootstrap `done`, `artifacts_path` set, a done step `path` still relative (prototype finished while bootstrap moved): run `python3 -I .agents/skills/bootstrap-project/scripts/move-artifacts.py .bootstrap/projects/NN <artifacts_path> <repo_path> --late`.

## end
Say state is in `.bootstrap/projects/NN/status.json`. After bootstrap: say `repo_path` and `artifacts_path` from it.
