---
name: bootstrap-project
description: Create the app repo for a project from a registered stack, last pipeline step. Use after wireframes; runs in parallel with /build-html-prototype. Scaffolds new git repo, creates local DB and GitHub repo, pushes main, moves done artifacts out of .bootstrap.
---
# bootstrap-project
Last step of the project pipeline. Creates the app's git repo from a stack in the registry, proves it works, pushes it to GitHub, then moves the project's planning files (idea, spec, journeys, wireframes...) next to the repo. Only `status.json` stays in `.bootstrap/projects/<id>/`.
Source: apexyard `walking-skeleton-django` (MIT): plan before build, prove the slice end to end, push main only after it passes.

## Names used below
| name | means |
|---|---|
| project folder | `.bootstrap/projects/<id>/`, `<id>` = two digits like `01` |
| setup.json | `.bootstrap/setup.json`: Postgres, Redis and GitHub account from /setup. Holds passwords: never print, paste into chat, or commit them. |
| status helper | `python3 -I .agents/skills/project/scripts/status.py <project folder>`. The only way to write `status.json`: `step bootstrap key=value ...` updates this step, `set key=value` sets a top-level key. It locks the file, because the html-prototype thread writes it at the same time. Never edit `status.json` by hand. |
| parent folder | folder the user picks for this project only. Holds the repo and the artifacts. |
| repo folder | `<parent folder>/<slug>`: the new git repo |
| artifacts folder | `<parent folder>/artifacts`: where planning files move to |
| stack file | `references/stacks/<file>` named in the registry row of the chosen stack |

## Called from /project
/project usually runs this skill in a background thread, with every answer in the prompt: `parent=`, `slug=`, `stack=`, `owner=`, `visibility=`, one `key=value` per row of the stack file's Inputs table, `db=yes|no`, `approved=yes`.
Use given answers and never ask again: nobody is watching that thread. Every check below still applies. If a given answer fails a check, report failed instead of asking.

## 1 Pick the project and check prerequisites
Which project: the argument (`01` or the slug). No argument: if exactly one project is not bootstrapped yet, use it; if several, list id, title and state and ask; if none, tell the user to run /new-project.

Stop with `failed prereq` and tell the user what to run when:
| check | fix to suggest |
|---|---|
| wireframes step is not `done` (or is `skipped` but journeys is not `done`) | `/draw-wireframes <id>` or the earlier step named |
| setup.json lacks `postgres`, `redis` or `github` | /setup |
| `command -v cookiecutter` finds nothing | `/ensure-installed cookiecutter` |
| `docker info` fails | /ensure-runnable-docker |
| `gh auth status` fails | /ensure-git |

The html-prototype step may be in any state. It runs in parallel; never wait for it.
If bootstrap is already `done`: report skipped, and say where the repo and artifacts are. Never redo it.
If bootstrap is `running`: another thread owns it. Say so, show its `thread`, and stop. If the user says that thread is dead, continue (see resume below).
When all checks pass, mark the step running: status helper `step bootstrap status=running path=null`.

**Resume:** if `status.json` already has `repo_path` and that repo has a commit, the earlier run got past step 7. Jump to step 8; each later part skips what is already done.

## 2 Ask where and how
Ask everything in one round, each question with a recommended answer:
| question | recommend |
|---|---|
| parent folder (for this project only) | `~/Projects/<slug>`. Expand `~`, make the path absolute. |
| slug (repo name), letters, digits and `-` only | the `slug` in status.json |
| GitHub owner, user or org | setup.json `github.login` |
| visibility | private |
| stack | Read [references/stacks/index.md](references/stacks/index.md). One stack: pick it and say so. Several: list them. |
| every row of the stack file's Inputs table | that row's recommendation. Rows with no default (like domain) must be answered. |

Then check two rules. If either fails, say why and ask again:
- **GitHub:** `gh repo view <owner>/<slug>` must find nothing. We only create new repos.
- **Parent folder:** it must not exist (we create it) or be an empty folder (we use it). Anything else (a non-empty folder, a file, a link to a non-empty folder) is refused. We never mix the project into existing content.

When resuming, skip both rules: the repo and folder are ours already.

## 3 Show the plan and get a yes
Read the stack file. Show the user:
- the parent folder, and whether it will be created or reused
- the cookiecutter command from the stack file's Source section, filled with the answers
- the stack's goals, one line each
- the database name from the stack file's Database section, and the Postgres host, port and user from setup.json
- the exact `gh repo create <owner>/<slug> --<visibility>` command, and that `main` is pushed only if every goal passes on Postgres
- which planning folders will move to the artifacts folder after the first commit

Ask `Create? (y/n)`, unless `approved=yes` was given. On no, report skipped. Nothing is written before the yes.

## 4 Generate the repo
Run the stack file's Source steps. Its output becomes the repo folder.
If it fails: report `bootstrap-project: failed scaffold: generate <reason>`, and offer to delete what this run made (the repo folder, plus the parent folder if this run created it).

## 5 Create the database
This comes before the goals, because the app cannot start without its database and the goal checks start the app.
Ask `Create database "<name>" on <host>:<port> as <user>? (y/n)`, unless `db=` was given.
- **Yes:** follow the stack file's Database section. If the database already exists, ask whether to reuse it or stop. With given answers, reuse it only if it is empty, otherwise fail. Migrations run later, as part of the goals.
- **No:** skip it and show the commands to create it later. Goals that need the running app are then reported as not verified, and the report line gets `db-skipped`.
If creating it fails: report `bootstrap-project: failed db: <reason>`. The repo stays and nothing moves.

## 6 Reach every goal
The stack file's Goals describe the end state. How to get there is your call. Its Hints list traps found in earlier runs: they save time, but versions change, so check them.
After each goal, run its verify. Fix and rerun until it passes. If the same goal fails three attempts in a row, stop. Keep each goal's result for the report.
If you stop: report `bootstrap-project: failed scaffold: <goal> <reason>`. Nothing moves. Offer to delete what this run made: the repo folder, the parent folder and the database if this run created them. A rerun needs a parent folder that passes the rule again.

## 7 Make the first commit
In the repo folder:
1. `git init -b main`.
2. If the global `git config user.email` is empty, set `user.name` and `user.email` on this repo only, from setup.json `github.login` and `github.email`. Never change the global config.
3. `git add -A`, then check that nothing like `.env`, `node_modules/` or `.venv/` is staged. If one is, fix `.gitignore` and add again.
4. `git commit -m "chore: bootstrap <slug> (<stack id> stack)"`, with no trailers.
5. Record the repo: status helper `set repo_path=<repo folder>`.
If any of this fails: report `bootstrap-project: failed git: <reason>`. Nothing moves.

## 8 Create the GitHub repo and push
In the repo folder. On resume, skip each part that is already done.
1. `gh repo create <owner>/<slug> --<visibility>`, empty: no README, license, `.gitignore`, `--source` or `--push`. The user approved it in step 3; do not ask again.
2. `git remote add origin <url>`, ssh or https as gh is configured. Check with `git remote -v`. Record it: status helper `set github_url=<url>`.
3. Push only if every goal passed and the database was migrated on Postgres: `git push -u origin main`. Push `main` only, never force. Otherwise do not push: say why, give the push command, and add `not-pushed` to the report line. This keeps a broken first commit off the remote.
4. If you pushed and the stack's CI is GitHub, watch that run: `gh run watch <run id> --exit-status`, at most 15 minutes. Its result counts for the stack's CI goal in the report. Still running after 15 minutes: mark that goal not verified and give the `gh run list` command.
If any of this fails: report `bootstrap-project: failed github: <reason>`. The local commit stays and nothing moves. Running `/bootstrap-project <id>` again resumes here.

## 9 Move the planning files
Only after the first commit exists. Run:
```
python3 -I .agents/skills/bootstrap-project/scripts/move-artifacts.py <project folder> <artifacts folder> <repo folder>
```
The script moves only steps that are `done`. A running or pending html-prototype stays put and moves itself when it finishes (`--late`). The script checks every name clash before moving anything, then records `artifacts_path`, moves each folder, rewrites each done step's `path` to the new absolute path, and marks bootstrap done with state `project-bootstrapped`. Rerunning the same command is safe.
- **Exit 3, name clash** (only after an interrupted move, or files the user put in the artifacts folder): nothing was moved. Show the clashing folders, ask the user to move them aside, then run `/bootstrap-project <id>` again; it resumes here. Never merge or overwrite.
- **Any other error:** report `bootstrap-project: failed move: <script error>`.

## 10 Report
Tell the user:
- how to run it: `cd <repo folder> && just run`, websockets with `just asgi` (port 8001), background jobs with `just worker` and `just beat`, styles with `just css-watch`
- the GitHub URL, where the artifacts are, and that status stays in `<project folder>/status.json`

Then a `verified:` list with one line per stack goal: `<n> <short name>: verified`, or `<n> <short name>: not verified (<why>)`. A goal whose check did not run, or ran only partly (no browser, database skipped), is not verified. Never pass a goal silently.

If html-prototype is not `done` or `skipped` yet, add a line: `html-prototype is <status> (thread <thread>). It moves itself into <artifacts folder> when done.`

The last line is exactly one of:
| outcome | line |
|---|---|
| done | `bootstrap-project: done <id> <repo_path>`, plus ` db-skipped` if step 5 was skipped and ` not-pushed` if step 8 did not push |
| failed | `bootstrap-project: failed <scaffold\|db\|git\|github\|move\|prereq>: <reason>` |
| skipped | `bootstrap-project: skipped <id>` |
On failure also record it: status helper `step bootstrap status=failed result="<line>"`. Leave the top-level `state` as it is.

## Never
- Print or commit passwords or `.env`.
- Push before every goal passes on Postgres, push other branches, or force push.
- Change the global git config.
- Move planning files before the first commit.
- Write into a non-empty folder.
- Edit other steps in status.json. The move script's path rewrite is the only exception.
