---
name: bootstrap-project
description: Create the app repo for a project from a registered stack, last pipeline step. Use after wireframes; runs in parallel with /build-html-prototype. Scaffolds new git repo, creates local DB, moves done artifacts out of .bootstrap.
---
# bootstrap-project
Final step. New repo from stack registry. Artifacts leave `.bootstrap/projects/NN/`, status.json stays.
Source: apexyard `walking-skeleton-django` (MIT): plan before build, prove the slice end to end.
`$S` = this skill dir. `$SJ` = `.bootstrap/setup.json`. Never print, copy into chat, or commit a password.
`P` = `python3 -I .agents/skills/project/scripts/status.py .bootstrap/projects/NN`. Every `status.json` write goes through it (`P step bootstrap k=v ...`, `P set k=v`). It locks and re-reads: html-prototype thread writes the same file at the same time. Never edit the file by hand.
/project hands this skill to a background thread with answers in the prompt: `parent=`, `slug=`, `stack=`, `approved=yes`, `db=yes|no`. Supplied: use, never ask. Not supplied: ask as below. Parent rule and every check still apply: on violation with supplied answer, report failed, do not loop.

## 1 pick
Contract: arg `NN` or slug. No arg: one project not bootstrapped -> use it. Several -> list id, title, state, ask. None -> run /new-project.
Precondition: wireframes `done`; or wireframes `skipped` and journeys `done`. Else stop: `run /<skill> NN`, report failed prereq. html-prototype may be in any status: it runs in parallel, never wait for it.
`$SJ` needs `postgres`, `github`. Missing: say run /setup, report failed prereq.
Bootstrap `done`: report skipped, say `repo_path` and `artifacts_path`. Never redo.
Bootstrap `running`: another thread owns it. Say so, show `thread`, stop. User says that thread is dead: run on (resume rule below).
After checks pass: `P step bootstrap status=running path=null`.
Resume: `repo_path` set, has a commit, bootstrap not done -> go to 7.

## 2 where
Ask, recommended answers, one round:
- Q1 parent dir for this project only. Recommend `~/Projects/<slug>`. Expand `~`, make absolute.
- Q2 slug. Recommend status.json `slug`. `[a-z0-9-]` only.
- Q3 stack. Read [references/stacks/index.md](references/stacks/index.md). One stack: pick it, say so. Several: list, ask.
Repo `$R` = `<parent>/<slug>`. Artifacts `$A` = `<parent>/artifacts`.
Parent rule: not exist -> will create. Exists and empty dir -> use. Anything else (non-empty, file, symlink to non-empty): refuse, say why, ask other parent. Loop. Never merge into existing content.
Resume (`repo_path` set, step 1): skip this rule.

## 3 plan
Read stack file `references/stacks/<id>.md`. Show:
- Parent dir: created now, or empty and reused.
- `$R` tree from the stack's files list, pinned versions, commands to run.
- DB name `<slug>` on `$SJ` postgres host:port user.
- Artifact dirs that will move to `$A` after first commit.
Ask `Create? (y/n)`, or `approved=yes` in call. No: report skipped. Nothing written before yes.

## 4 scaffold
Follow stack file `scaffold` section exactly, in order. Each step done when its stated output shows.
Fail: step failed `bootstrap-project: failed scaffold: <step> <reason>`. Artifacts unmoved. Offer to delete what this run made (`$R`, and `<parent>` if this run created it); rerun needs a parent that passes the rule.

## 5 db
Ask `Create database "<slug>" on <host>:<port> as <user>? (y/n)`, or `db=` in call.
Yes: stack file `db` section. Exists already: ask reuse or stop. Then migrate and test per stack file.
Fail: `bootstrap-project: failed db: <reason>`. Repo stays, artifacts unmoved.
No: skip, say the db commands for later. Report gets `db-skipped`.

## 6 git
In `$R`:
1. `git init -b main`.
2. `git config --global user.email` empty: set local `user.name` = `$SJ` github.login, `user.email` = github.email. Never touch global.
3. `git add -A`. Check staged list has no `.env`, `node_modules/`, `.venv/`. Has: fix `.gitignore`, re-add.
4. `git commit -m "chore: bootstrap <slug> (<stack id> stack)"`. No trailers. No remote, no push.
5. `P set repo_path=$R`.
Fail: `bootstrap-project: failed git: <reason>`. Artifacts unmoved.

## 7 move
Only after first commit exists.
`python3 -I $S/scripts/move-artifacts.py .bootstrap/projects/NN $A $R`
Script moves only steps `done`. html-prototype `running` or `pending` stays in the project dir and moves itself (`--late`) when it finishes. Script: checks every collision first, records `artifacts_path`, moves each dir, rewrites done step paths absolute, sets bootstrap done, path `$R`, state `project-bootstrapped`. Resumable: rerun same command.
Exit 3 collision (only after an interrupted move, or user edits in `$A`): nothing moved. Show clashing dirs. Ask user to move them aside, then rerun `/bootstrap-project NN` (resumes here). Never merge or overwrite.
Other non-zero: `bootstrap-project: failed move: <stderr>`, step failed.

## 8 report
Say: `cd $R && just run`. Artifacts in `$A`. Status in `.bootstrap/projects/NN/status.json`.
Last line, exactly one:
`bootstrap-project: done NN <repo_path>` (append ` db-skipped` if 5 skipped)
`bootstrap-project: failed <scaffold|db|git|move|prereq>: <reason>`
`bootstrap-project: skipped NN`
Failed: `P step bootstrap status=failed result="<line>"`. Keep `state`.
html-prototype not `done` or `skipped` at the end: add one line before the report line: `html-prototype is <status> (thread <thread>). It moves itself into $A when done.`

## never
Print or commit passwords or `.env`. Push. Write global git config. Move artifacts before first commit. Overwrite a non-empty dir. Edit other steps except path rewrite by script.
