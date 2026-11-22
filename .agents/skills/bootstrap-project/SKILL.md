---
name: bootstrap-project
description: Create the app repo for a project from a registered stack, last pipeline step. Use after wireframes; runs in parallel with /build-html-prototype. Scaffolds new git repo, pushes generated code to main on a new GitHub repo (or into a folder of an existing one), creates local DB, commits agent skills onto the bootstrap branch, opens one PR with a commit per goal, moves done artifacts out of .bootstrap.
---
# bootstrap-project
Last step of the project pipeline. Creates the app's git repo from a stack in the registry and pushes the generated code to `main` on GitHub. Then it reaches the stack's goals on one branch, a commit per goal, commits the agent skills from `templates/skills/` onto that same branch, opens a PR, and moves the project's planning files (idea, spec, journeys, wireframes...) next to the repo. Only `status.json` stays in `.bootstrap/projects/<id>/`.
With `target=existing` it puts the app into a folder of a GitHub repo that already exists instead; see [Into an existing repo](#into-an-existing-repo).

## Names used below
| name | means |
|---|---|
| project folder | `.bootstrap/projects/<id>/`, `<id>` = two digits like `01` |
| setup.json | `.bootstrap/setup.json`: Postgres, Redis and GitHub account from /setup. Holds passwords: never print, paste into chat, or commit them. |
| status helper | `python3 -I .agents/skills/project/scripts/status.py <project folder>`. The only way to write `status.json`: `step bootstrap key=value ...` updates this step, `set key=value` sets a top-level key. It locks the file, because the html-prototype top-level thread writes it at the same time. Never edit `status.json` by hand. |
| parent folder | folder the user picks for this project only. Holds the repo and the artifacts. |
| repo folder | `<parent folder>/<slug>`: the new git repo. Existing repo: `<parent folder>/<repo name>`, a fresh clone |
| app folder | where the stack's code lives: the repo folder, or `<repo folder>/<app_dir>` in an existing repo |
| default branch | `main`; in a non-empty existing repo, that repo's default branch |
| artifacts folder | `<parent folder>/artifacts`: where planning files move to |
| stack file | `references/stacks/<file>` named in the registry row of the chosen stack |
| skill templates | `templates/skills/`: one directory per skill to install into the app repo. Not live skills of this repo. Do not run them here. |

## Called from /project
/project usually runs this skill in a top-level thread, with every answer in the prompt: `parent=`, `slug=`, `stack=`, `target=new|existing` (missing = `new`), `owner=` and `visibility=` (new) or `repo=` and `app_dir=` (existing), one `key=value` per row of the stack file's Inputs table, `db=yes|no`, `approved=yes`.
Use given answers and never ask again: nobody is watching that thread. Every check below still applies. If a given answer fails a check, report failed instead of asking. If an answer with no default is missing, report `failed prereq`.

## 1 Pick the project and check prerequisites
Which project: the argument (`01` or the slug). No argument: if exactly one project is not bootstrapped yet, use it; if several, list id, title and state and ask; if none, tell the user to run /new-project.

Stop with `failed prereq` and tell the user what to run when:
| check | fix to suggest |
|---|---|
| wireframes step is not `done` (or is `skipped` but journeys is not `done`) | `/draw-wireframes <id>` or the earlier step named |
| setup.json lacks `postgres`, `redis` or `github` | /setup |
| `gh auth status` fails | /ensure-git |

The html-prototype step may be in any state. It runs in parallel; never wait for it.
If bootstrap is already `done`: report skipped, and say where the repo and artifacts are. Never redo it.
If bootstrap is `running`: another thread owns it. Say so, show its `thread`, and stop. If the user says that thread is dead, continue (see resume below).
When all checks pass, mark the step running: status helper `step bootstrap status=running path=null`.

**Resume:** if `status.json` already has `repo_path` and that repo has a commit (existing repo: a commit holding the app folder, on the branch step 5 commits to), the earlier run got past step 5. Jump to step 6; each later part skips what is already done (repo created, `main` pushed, database created, goal commits made, skills committed, PR opened).

## 2 Ask where and how
Ask everything in one round, each question with a recommended answer:
| question | recommend |
|---|---|
| parent folder (for this project only) | `~/Projects/<slug>`. Expand `~`, make the path absolute. |
| slug (repo name; the app's name in an existing repo), letters, digits and `-` only | the `slug` in status.json |
| target: a new GitHub repo, or a folder in an existing one | new |
| new: GitHub owner, user or org | setup.json `github.login` |
| new: visibility | private |
| existing: repo, `<owner>/<name>` | none, must be answered |
| existing: app_dir, the folder in that repo for the app | `.` if the repo is empty, else `apps/<slug>` |
| stack | Read [references/stacks/index.md](references/stacks/index.md). One stack: pick it and say so. Several: list them. |
| every row of the stack file's Inputs table | that row's recommendation. Rows with no default (like domain) must be answered. |

Then check two rules. If either fails, say why and ask again:
- **GitHub:** `gh repo view <owner>/<slug>` must find nothing. A new repo is never one that exists. Existing repo: the rules in [Into an existing repo](#into-an-existing-repo) instead.
- **Parent folder:** it must not exist (we create it) or be an empty folder (we use it). Anything else (a non-empty folder, a file, a link to a non-empty folder) is refused. We never mix the project into existing content.

When resuming, skip both rules: the repo and folder are ours already.

Then run every check in the chosen stack file's Tools section. If one fails, stop with `failed prereq` and suggest that row's fix.

## 3 Show the plan and get a yes
Read the stack file. Show the user:
- the parent folder, and whether it will be created or reused
- the generate command(s) from the stack file's Source section, filled with the answers
- the stack's baseline goals and goals, one line each
- the database name from the stack file's Database section, and the Postgres host, port and user from setup.json
- the exact `gh repo create <owner>/<slug> --<visibility>` command, and that the generated code, with the baseline goals met, is pushed to `main` once its CI checks pass locally
- that the goals land on branch `bootstrap/<stack id>`, one commit per goal, with a PR into `main` that the user merges
- that every skill directory in `templates/skills/` is copied into the repo and committed on `bootstrap/<stack id>` before that push
- which planning folders will move to the artifacts folder after the PR is open

Ask `Create? (y/n)`, unless `approved=yes` was given. On no, report skipped. Nothing is written before the yes.

## 4 Generate the repo
Run the stack file's Source steps. Its output becomes the repo folder.
If it fails: report `bootstrap-project: failed scaffold: generate <reason>`, and offer to delete what this run made (the repo folder, plus the parent folder if this run created it).

## 5 Make the first commit
The generated code goes to `main` with only the stack's Baseline goals added, and only once its CI would pass: `main` is pushed next, and its first CI run must be green.
In the repo folder:
1. `git init -b main`. The first branch is always `main`.
2. If the global `git config user.email` is empty, set `user.name` and `user.email` on this repo only, from setup.json `github.login` and `github.email`. Never change the global config.
3. Reach every goal in the stack file's Baseline section, in order, and run its verify, as in step 8 (traps are advice; three failed attempts on the same goal: stop). Keep each result for the report. Nothing else from the Goals section goes into this commit.
4. `git add -A`, then check that nothing like `.env`, `node_modules/`, `.venv/` or `target/` is staged. If one is, fix `.gitignore` and add again.
5. If the repo has CI config (`.github/workflows/`, `.gitlab-ci.yml`, `.travis.yml`, `.drone.yml`), read every job and run its steps locally, the way CI runs them: same commands, same containers when a job uses docker compose, no `.env` (CI has none). Lint GitHub workflows with `actionlint`, or `docker run --rm -v $PWD:/repo -w /repo rhysd/actionlint` if it is not installed. Fix what fails with the smallest change, `git add -A` again, and rerun until every job passes. A step that cannot run locally (it needs a secret or a service you cannot start): say which, and rely on the CI run in step 6. If the same job fails three attempts in a row, stop.
6. `git commit -m "chore: init <slug> from <stack id> stack"`, with no trailers.
7. Record the repo: status helper `set repo_path=<repo folder>`.
If a baseline goal does not pass: report `bootstrap-project: failed scaffold: <goal> <reason>`. If CI does not pass: report `bootstrap-project: failed ci: <job> <reason>`. If git fails: report `bootstrap-project: failed git: <reason>`. Either way nothing is pushed and nothing moves.

## 6 Create the GitHub repo and push main
In the repo folder. On resume, skip each part that is already done.
1. `gh repo create <owner>/<slug> --<visibility>`, empty: no README, license, `.gitignore`, `--source` or `--push`. The user approved it in step 3; do not ask again.
2. `git remote add origin <url>`, ssh or https as gh is configured. Check with `git remote -v`. Record it: status helper `set github_url=<url>`.
3. `git push -u origin main`. Never force. Then `gh repo view <owner>/<slug> --json defaultBranchRef -q .defaultBranchRef.name` must print `main`; if not, `gh repo edit <owner>/<slug> --default-branch main`.
4. If the stack's CI is GitHub, watch the run on `main`: `gh run watch <run id> --exit-status`, at most 15 minutes. If it fails, read `gh run view <run id> --log-failed`, fix it locally, rerun step 5's CI checks, commit `fix(ci): <what>` and push. Three failed runs: stop. Still running after 15 minutes: say so, give the `gh run list` command, and go on.
If any of this fails: report `bootstrap-project: failed github: <reason>`. The local commit stays and nothing moves. Running `/bootstrap-project <id>` again resumes here.

## 7 Create the database
This comes before the goals, because the app cannot start without its database and the goal checks start the app.
Ask `Create database "<name>" on <host>:<port> as <user>? (y/n)`, unless `db=` was given.
- **Yes:** follow the stack file's Database section. If the database already exists, ask whether to reuse it or stop. With given answers, reuse it only if it is empty, otherwise fail. Migrations run later, as part of the goals.
- **No:** skip it and show the commands to create it later. Goals that need the running app are then reported as not verified, and the report line gets `db-skipped`.
If creating it fails: report `bootstrap-project: failed db: <reason>`. The repo stays and nothing moves.

## 8 Reach every goal, one commit each
Branch off `main`: `git switch -c bootstrap/<stack id>`. On resume, switch to that branch and run each goal's verify in order: a goal that passes with a clean tree is done; the first that fails is where work restarts.
The stack file's Goals describe the end state. How to get there is your call. Work through them in the stack file's order, and run every check inside the repo folder. A goal's Traps list pitfalls found in earlier runs: advice, not requirements. They save time, but versions change, so check them.
After each goal, run its verify. Fix and rerun until it passes. If the same goal fails three attempts in a row, stop. Keep each goal's result for the report.
When a goal passes, commit it on its own: `git add -A`, check the staged files as in step 5, then commit with no trailers. Write the message for someone reading the app's history, who has never seen the stack file:
- Conventional Commits, with the type the change really is (`feat`, `build`, `ci`, `chore`, `refactor`, `test`, `docs`).
- The subject says what the app now does or has, in the app's terms, read from the diff. Never goal numbers, goal names, or the words goal, baseline, stack, bootstrap.
- A body when the why is not obvious from the diff: a choice made, a workaround for a trap, what was removed and why. Skip the body when the subject says it all.

A fix an earlier goal needs goes into the current goal's commit. A goal with nothing to commit (already met) gets no commit; say so in the PR. A check marked "after this goal's commit" runs right after that commit; a fix for it is amended into the same commit (nothing is pushed yet).
If you stop: report `bootstrap-project: failed scaffold: <goal> <reason>`. Nothing is pushed and nothing moves. `main`, the GitHub repo and the branch's commits stay; running `/bootstrap-project <id>` again resumes on the branch.

## 9 Install the agent skills
On `bootstrap/<stack id>`, before the push. The skills have to be in a commit on that branch, not only on the local disk after the PR exists.
Skill templates are `templates/skills/` in this repo. Every immediate directory there is one skill. Do not run them here, and do not add them one by one in this step: a later template is copied by the same command.
From this repo, run:
```
python3 -I .agents/skills/bootstrap-project/scripts/install-skills.py <repo folder> templates/skills
```
The script copies each template directory to `<repo>/.agents/skills/<name>/` and symlinks `<repo>/.claude/skills/<name>` to `../../.agents/skills/<name>`. One link per skill. It does not link `.claude/skills` itself at `.agents/skills`. Running it again replaces those skill directories with the templates.
The templates hand off to `/to-spec`, `/to-tickets` and `/implement-spec` from mattpocock/skills. Those are installed once per user, not into the repo: files in `~/.agents/skills/<name>/`, each linked from `~/.claude/skills/<name>`. If `~/.agents/skills/to-spec` is missing, say so in the report; do not install them into the repo.
Then, in the repo folder, if `git status --porcelain -- .agents/skills .claude/skills` is empty, the skills are already committed: skip the commit. Otherwise `git add .agents/skills .claude/skills`. Nothing else staged (no `.env`, `node_modules/`, `.venv/`). Commit with no trailers, for someone reading the app's history:
```
chore: add skills for cutting a PRD into specs

Planning continues in this repo: cut the PRD into specs, then ticket and implement one spec at a time.
```
No goal numbers, and not the words goal, baseline, stack, or bootstrap.
If the script fails: report `bootstrap-project: failed scaffold: skills <reason>`. If the commit fails: report `bootstrap-project: failed git: skills <reason>`. Nothing is pushed and nothing moves.

## 10 Push the branch and open the PR
1. `git push -u origin bootstrap/<stack id>`. Never force. On resume, this push sends the skills commit if the remote does not have it yet.
2. `gh pr create --base main --head bootstrap/<stack id> --title "Bootstrap <slug> on the <stack id> stack"`. The body lists every goal, one line each: its commit, and verified or not verified (why). If any goal is not verified, add `--draft`. Record it: status helper `set pr_url=<url>`. On resume, if `pr_url` is already set, skip create.
3. If the stack's CI is GitHub, watch the PR's run as in step 6. Its result counts for the stack's CI goal in the report. If it fails, fix it on the branch in a new commit `fix(ci): <what>` and push. Three failed runs, or still running after 15 minutes: mark that goal not verified, update the PR body and give the `gh run list` command.
Never merge the PR: the user reviews and merges it.
If any of this fails: report `bootstrap-project: failed github: <reason>`. Nothing moves. Running `/bootstrap-project <id>` again resumes here.

## 11 Move the planning files
Only after the PR is open. Run:
```
python3 -I .agents/skills/bootstrap-project/scripts/move-artifacts.py <project folder> <artifacts folder> <repo folder>
```
The script moves only steps that are `done`. A running or pending html-prototype stays put and moves itself when it finishes (`--late`). The script checks every name clash before moving anything, then records `artifacts_path`, moves each folder, rewrites each done step's `path` to the new absolute path, and marks bootstrap done with state `project-bootstrapped`. Rerunning the same command is safe.
- **Exit 3, name clash** (only after an interrupted move, or files the user put in the artifacts folder): nothing was moved. Show the clashing folders, ask the user to move them aside, then run `/bootstrap-project <id>` again; it resumes here. Never merge or overwrite.
- **Any other error:** report `bootstrap-project: failed move: <script error>`.

## 12 Report
Tell the user:
- how to run it: the stack file's Run section, with the repo folder filled in
- the GitHub URL, the PR URL, where the artifacts are, and that status stays in `<project folder>/status.json`
- the skills now committed on `bootstrap/<stack id>`. In the app repo: `/plan-implementation` once, to file every release milestone and its spec issues. Then, later, `/to-tickets` on one spec issue and `/implement-spec` on that same issue. A milestone is that release's progress view, not the whole PRD, and not the input to `/implement-spec`.

Then a `verified:` list with one line per stack goal, baseline goals first: `<n> <short name>: verified`, or `<n> <short name>: not verified (<why>)`. A goal whose check did not run, or ran only partly (no browser tools, database skipped), is not verified. Never pass a goal silently.

If html-prototype is not `done` or `skipped` yet, add a line: `html-prototype is <status> (thread <thread>). It moves itself into <artifacts folder> when done.`

The last line is exactly one of:
| outcome | line |
|---|---|
| done | `bootstrap-project: done <id> <repo_path>`, plus ` db-skipped` if step 7 was skipped and ` draft-pr` if the PR is a draft |
| failed | `bootstrap-project: failed <scaffold\|ci\|db\|git\|github\|move\|prereq>: <reason>` |
| skipped | `bootstrap-project: skipped <id>` |
On failure also record it: status helper `step bootstrap status=failed result="<line>"`. Leave the top-level `state` as it is.

## Into an existing repo
`target=existing`: the app goes into the app folder of a GitHub repo that already exists. Every step above runs, with these differences. Empty repo = no commits (`gh repo view <repo> --json isEmpty` is true); it gets `main` exactly like a new repo. Non-empty repo: its default branch is never pushed; everything arrives through the PR.
| step | difference |
|---|---|
| 2 rules | Replace the GitHub rule. `gh repo view <repo> --json isEmpty,defaultBranchRef,viewerPermission` finds it, and `viewerPermission` is `ADMIN`, `MAINTAIN` or `WRITE`. Non-empty repo, on its default branch: `app_dir` is not `.` and does not exist (`gh api repos/<repo>/contents/<app_dir>` is a 404); branch `bootstrap/<stack id>` does not exist; no CI file named `<slug>` exists; no directory in `templates/skills/` has the name of one in `.agents/skills/` or `.claude/skills/`. Any clash: name it and ask again; with given answers, `failed prereq`. The parent folder rule is unchanged. |
| 3 plan | Show `gh repo clone <repo> <repo folder>` instead of `gh repo create`, the app folder, and where the baseline commit goes: empty repo, `main`, pushed; non-empty, the first commit of `bootstrap/<stack id>`. |
| 4 generate | First `gh repo clone <repo> <repo folder>` (an empty repo clones with a warning). Then run the Source steps into the app folder. A generator that refuses an existing destination, with the app folder being the repo folder: generate into `<parent folder>/.gen-<slug>`, move everything in it into the repo folder, delete it. From here on, every path and command in the stack file that names the repo folder means the app folder. Only git, the CI file and the skills (step 9) stay at the repo root. |
| 5 first commit | No `git init`. Empty repo: `git symbolic-ref HEAD refs/heads/main`. Non-empty: `git switch -c bootstrap/<stack id> origin/<default branch>`. App folder not the repo root: the stack's ignore file lives in the app folder; the CI file lives at the repo root's CI location, named `<slug>`, triggered only by changes under `<app_dir>/` and to itself, every step run in the app folder (GitHub: `paths:` and `defaults.run.working-directory`), caches keyed to the app folder. Run that file's jobs locally; in a non-empty repo also every existing workflow the changed paths trigger. An existing workflow whose latest run on the default branch also fails (`gh run list --branch <default branch> --workflow <file> -L 1`) is reported, not fixed. Record `set repo_path=<repo folder> app_path=<app folder> target=existing`. |
| 6 GitHub | No `gh repo create`; the clone set `origin`. `set github_url=<origin url>`. Empty repo: push `main` and watch its CI as written. Non-empty: skip this step's push and CI watch. |
| 8 goals | Empty repo: branch off `main` as written. Non-empty: stay on `bootstrap/<stack id>`. App folder not the repo root, with the goal that writes the README and AGENTS.md: empty repo, also a root `README.md` (title, one-liner, link to `<app_dir>/`) and a root `AGENTS.md` that points at `<app_dir>/AGENTS.md`; non-empty, one line in the root `AGENTS.md` pointing at `<app_dir>/AGENTS.md`, creating the file if missing. App folder not the repo root, with the goal that adds the dev workflow: the task runner and editor tasks live at the repo root, so they work from where the editor opens the repo. Root `justfile` with `mod <app> '<app_dir>'` (recipes run in the app folder: `just <app> dev`), and the editor tasks file at the root (Zed: `.zed/tasks.json`), labelled `<app>: <recipe>` and calling `just <app> <recipe>`, none in the app folder. The app's own justfile stays. |
| 10 PR | `--base <default branch>`. Non-empty: the body lists the baseline goals first; their commit opens the branch. |
| 12 report | The Run section with the app folder filled in. |

## Never
- Print or commit passwords or `.env`.
- Push `main` before its CI checks pass locally, push goal work to `main`, push branches other than `main` and `bootstrap/<stack id>`, force push, or merge the PR.
- Push the default branch of a non-empty existing repo, or create a repo when `target=existing`.
- Change the global git config.
- Move planning files before the PR is open.
- Leave the agent skills uncommitted, or install them only after the push.
- Write into a non-empty folder. In an existing repo, write nothing outside the app folder except the CI file, `.agents/skills`, `.claude/skills`, and the root README, AGENTS.md, `justfile` and editor tasks in step 8; never overwrite an existing skill.
- Edit other steps in status.json. The move script's path rewrite is the only exception.
