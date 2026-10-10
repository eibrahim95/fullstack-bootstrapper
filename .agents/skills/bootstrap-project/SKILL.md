---
name: bootstrap-project
description: Create the app repo for a project from a registered stack, last pipeline step. Use after /build-html-prototype (or when it was skipped). Scaffolds new git repo, creates local DB, moves project artifacts out of .bootstrap.
---
# bootstrap-project
Final step. New repo from stack registry. Artifacts leave `.bootstrap/projects/NN/`, status.json stays.
Source: apexyard `walking-skeleton-django` (MIT): plan before build, prove the slice end to end.
`$S` = this skill dir. `$SJ` = `.bootstrap/setup.json`. Never print, copy into chat, or commit a password.

## 1 pick
Contract: arg `NN` or slug. No arg: one project not bootstrapped -> use it. Several -> list id, title, state, ask. None -> run /new-project.
Precondition: html-prototype `done`; or `skipped` and wireframes `done`; or both skipped and journeys `done`. Else stop: `run /<skill> NN`, report failed prereq.
`$SJ` needs `postgres`, `github`. Missing: say run /setup, report failed prereq.
Bootstrap `done`: ask overwrite. No: report skipped. Yes: new repo in an empty `$R`; `$A` fixed to existing `artifacts_path` (artifacts already there). Old repo untouched.
Resume: `repo_path` set, has a commit, bootstrap not done -> go to 7.

## 2 where
Ask, recommended answers, one round:
- Q1 parent dir. Recommend `~/Projects`. Expand `~`, make absolute.
- Q2 slug. Recommend status.json `slug`. `[a-z0-9-]` only.
- Q3 stack. Read [references/stacks/index.md](references/stacks/index.md). One stack: pick it, say so. Several: list, ask.
Repo `$R` = `<parent>/<slug>`. Artifacts `$A` = `<parent>/artifacts`.
`$R` exists and non-empty: refuse, ask other parent or slug. Loop.

## 3 plan
Read stack file `references/stacks/<id>.md`. Show:
- `$R` tree from the stack's files list, pinned versions, commands to run.
- DB name `<slug>` on `$SJ` postgres host:port user.
- Artifact dirs that will move to `$A` after first commit. Any `$A/<dir>` already there: name it now.
Ask `Create? (y/n)`. No: report skipped. Nothing written before yes.

## 4 scaffold
Follow stack file `scaffold` section exactly, in order. Each step done when its stated output shows.
Fail: step failed `bootstrap-project: failed scaffold: <step> <reason>`. Artifacts unmoved. Offer to delete `$R` (only dir this run made); rerun needs it gone.

## 5 db
Ask `Create database "<slug>" on <host>:<port> as <user>? (y/n)`.
Yes: stack file `db` section. Exists already: ask reuse or stop. Then migrate and test per stack file.
Fail: `bootstrap-project: failed db: <reason>`. Repo stays, artifacts unmoved.
No: skip, say the db commands for later. Report gets `db-skipped`.

## 6 git
In `$R`:
1. `git init -b main`.
2. `git config --global user.email` empty: set local `user.name` = `$SJ` github.login, `user.email` = github.email. Never touch global.
3. `git add -A`. Check staged list has no `.env`, `node_modules/`, `.venv/`. Has: fix `.gitignore`, re-add.
4. `git commit -m "chore: bootstrap <slug> (<stack id> stack)"`. No trailers. No remote, no push.
5. Write top-level `repo_path` = `$R` to status.json.
Fail: `bootstrap-project: failed git: <reason>`. Artifacts unmoved.

## 7 move
Only after first commit exists.
`python3 -I $S/scripts/move-artifacts.py .bootstrap/projects/NN $A $R`
Script: checks every collision first, records `artifacts_path`, moves each dir, rewrites done step paths absolute, sets bootstrap done, path `$R`, state `project-bootstrapped`. Resumable: rerun same command.
Exit 3 collision: nothing moved. Show clashing dirs. Ask user to move them aside, then rerun `/bootstrap-project NN` (resumes here). Never merge or overwrite.
Other non-zero: `bootstrap-project: failed move: <stderr>`, step failed.

## 8 report
Say: `cd $R && just run`. Artifacts in `$A`. Status in `.bootstrap/projects/NN/status.json`.
Last line, exactly one:
`bootstrap-project: done NN <repo_path>` (append ` db-skipped` if 5 skipped)
`bootstrap-project: failed <scaffold|db|git|move|prereq>: <reason>`
`bootstrap-project: skipped NN`
Failed: set bootstrap step `failed`, result = line. Keep `state`.

## never
Print or commit passwords or `.env`. Push. Write global git config. Move artifacts before first commit. Overwrite a non-empty dir. Edit other steps except path rewrite by script.
