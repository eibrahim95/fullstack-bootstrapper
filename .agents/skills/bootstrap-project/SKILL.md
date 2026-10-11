---
name: bootstrap-project
description: Create the app repo for a project from a registered stack, last pipeline step. Use after wireframes; runs in parallel with /build-html-prototype. Scaffolds new git repo, creates local DB and GitHub repo, pushes main, moves done artifacts out of .bootstrap.
---
# bootstrap-project
Final step. New repo from stack registry. Artifacts leave `.bootstrap/projects/NN/`, status.json stays.
Source: apexyard `walking-skeleton-django` (MIT): plan before build, prove the slice end to end, push main only after it passes.
`$S` = this skill dir. `$SJ` = `.bootstrap/setup.json`. Never print, copy into chat, or commit a password.
`P` = `python3 -I .agents/skills/project/scripts/status.py .bootstrap/projects/NN`. Every `status.json` write goes through it (`P step bootstrap k=v ...`, `P set k=v`). It locks and re-reads: html-prototype thread writes the same file at the same time. Never edit the file by hand.
/project hands this skill to a background thread with answers in the prompt: `parent=`, `slug=`, `stack=`, `owner=`, `visibility=`, stack inputs as `key=value` (stack file `inputs`), `approved=yes`, `db=yes|no`. Supplied: use, never ask. Not supplied: ask as below. Parent rule and every check still apply: on violation with supplied answer, report failed, do not loop.

## 1 pick
Contract: arg `NN` or slug. No arg: one project not bootstrapped -> use it. Several -> list id, title, state, ask. None -> run /new-project.
Precondition: wireframes `done`; or wireframes `skipped` and journeys `done`. Else stop: `run /<skill> NN`, report failed prereq. html-prototype may be in any status: it runs in parallel, never wait for it.
`$SJ` needs `postgres`, `redis`, `github`. Missing: say run /setup, report failed prereq.
`command -v cookiecutter` empty: say run `/ensure-installed cookiecutter`, report failed prereq.
`docker info` fails: say run `/ensure-runnable-docker`, report failed prereq.
`gh auth status` fails: say run `/ensure-git`, report failed prereq.
Bootstrap `done`: report skipped, say `repo_path` and `artifacts_path`. Never redo.
Bootstrap `running`: another thread owns it. Say so, show `thread`, stop. User says that thread is dead: run on (resume rule below).
After checks pass: `P step bootstrap status=running path=null`.
Resume: `repo_path` set, has a commit, bootstrap not done -> go to 8 (github, skips what is done).

## 2 where
Ask, recommended answers, one round:
- Q1 parent dir for this project only. Recommend `~/Projects/<slug>`. Expand `~`, make absolute.
- Q2 slug. Recommend status.json `slug`. `[a-z0-9-]` only.
- Q3 GitHub owner (user or org). Recommend `$SJ` github.login. Repo name = slug.
- Q4 visibility. Recommend private.
- Q5 stack. Read [references/stacks/index.md](references/stacks/index.md). One stack: pick it, say so. Several: list, ask.
- Q6+ every row of stack file `inputs`, same batch, its recommended answer. Input without a default (e.g. domain): no recommendation, must answer.
Repo `$R` = `<parent>/<slug>`. Artifacts `$A` = `<parent>/artifacts`.
GitHub rule: `gh repo view <owner>/<slug>` finds a repo -> refuse, ask other owner or slug. Loop.
Parent rule: not exist -> will create. Exists and empty dir -> use. Anything else (non-empty, file, symlink to non-empty): refuse, say why, ask other parent. Loop. Never merge into existing content.
Resume (`repo_path` set, step 1): skip both rules.

## 3 plan
Read stack file named in the registry row (`references/stacks/`). Show:
- Parent dir: created now, or empty and reused.
- cookiecutter command from stack `source`, filled with inputs.
- Goal list from stack `goals`, one line each.
- DB name (stack `db`) on `$SJ` postgres host:port user.
- Exact `gh repo create <owner>/<slug> --<visibility>` command, and that `main` is pushed only if every goal passes on Postgres.
- Artifact dirs that will move to `$A` after first commit.
Ask `Create? (y/n)`, or `approved=yes` in call. No: report skipped. Nothing written before yes.

## 4 generate
Run stack `source` command, output lands at `$R`.
Fail: step failed `bootstrap-project: failed scaffold: generate <reason>`. Offer to delete what this run made (`$R`, and `<parent>` if this run created it).

## 5 db
Before goals: without the db the app does not start, so run checks cannot pass.
Ask `Create database "<db name>" on <host>:<port> as <user>? (y/n)`, or `db=` in call.
Yes: stack file `db` section. Exists already: ask reuse or stop (supplied answers: reuse only if empty, else failed). Migrate comes in goals.
Fail: `bootstrap-project: failed db: <reason>`. Repo stays, artifacts unmoved.
No: skip, say the db commands for later. Goals that start the app: not verified (db skipped). Report gets `db-skipped`.

## 6 goals
Reach every stack goal. How = your call; stack `hints` save time, re-check them.
Run each goal's verify. Fix, rerun, until all pass. Same goal fails 3 attempts: stop. Keep each goal's result for 10.
Fail: step failed `bootstrap-project: failed scaffold: <goal> <reason>`. Artifacts unmoved. Offer to delete what this run made (`$R`, and `<parent>` if this run created it, and the db if this run created it); rerun needs a parent that passes the rule.

## 7 git
In `$R`:
1. `git init -b main`.
2. `git config --global user.email` empty: set local `user.name` = `$SJ` github.login, `user.email` = github.email. Never touch global.
3. `git add -A`. Check staged list has no `.env`, `node_modules/`, `.venv/`. Has: fix `.gitignore`, re-add.
4. `git commit -m "chore: bootstrap <slug> (<stack id> stack)"`. No trailers.
5. `P set repo_path=$R`.
Fail: `bootstrap-project: failed git: <reason>`. Artifacts unmoved.

## 8 github
In `$R`. Each part skips when already done (resume).
1. `gh repo create <owner>/<slug> --<visibility>`: empty. No README, license, gitignore, `--source`, `--push`. Approved in 3, never ask again.
2. `git remote add origin <ssh or https url per gh config>`. Check `git remote -v`. `P set github_url=<url>`.
3. Push only when every goal verified and db migrated on Postgres: `git push -u origin main`. Only `main`. Never force. Else no push: say why and the push command, report gets `not-pushed`.
4. Pushed and stack CI is GitHub: `gh run watch <run id> --exit-status` on the push run, max 15 min. Pass/fail feeds the CI goal in 10; still running: not verified, give `gh run list` command.
Fail: `bootstrap-project: failed github: <reason>`. Local commit stays, artifacts unmoved. Rerun `/bootstrap-project NN` resumes here.

## 9 move
Only after first commit exists.
`python3 -I $S/scripts/move-artifacts.py .bootstrap/projects/NN $A $R`
Script moves only steps `done`. html-prototype `running` or `pending` stays in the project dir and moves itself (`--late`) when it finishes. Script: checks every collision first, records `artifacts_path`, moves each dir, rewrites done step paths absolute, sets bootstrap done, path `$R`, state `project-bootstrapped`. Resumable: rerun same command.
Exit 3 collision (only after an interrupted move, or user edits in `$A`): nothing moved. Show clashing dirs. Ask user to move them aside, then rerun `/bootstrap-project NN` (resumes here). Never merge or overwrite.
Other non-zero: `bootstrap-project: failed move: <stderr>`, step failed.

## 10 report
Say: `cd $R && just run` (websockets: `just asgi` on 8001; background: `just worker`, `just beat`; styles: `just css-watch`). GitHub: `github_url`. Artifacts in `$A`. Status in `.bootstrap/projects/NN/status.json`.
Then `verified:` list, one line per stack goal: `<n> <short name>: verified` or `<n> <short name>: not verified (<why>)`. Goal whose verify did not run, or ran only partly (no browser, db skipped): not verified. Never pass silently.
Last line, exactly one:
`bootstrap-project: done NN <repo_path>` (append ` db-skipped` if 5 skipped, ` not-pushed` if 8 did not push)
`bootstrap-project: failed <scaffold|db|git|github|move|prereq>: <reason>`
`bootstrap-project: skipped NN`
Failed: `P step bootstrap status=failed result="<line>"`. Keep `state`.
html-prototype not `done` or `skipped` at the end: add one line before the report line: `html-prototype is <status> (thread <thread>). It moves itself into $A when done.`

## never
Print or commit passwords or `.env`. Push before every goal passes on Postgres, push other branches, force push. Write global git config. Move artifacts before first commit. Overwrite a non-empty dir. Edit other steps except path rewrite by script.
