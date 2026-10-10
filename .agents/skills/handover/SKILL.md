---
name: handover
description: Hand the work to a new top-level thread that runs on its own. Use when user wants to continue elsewhere, fork off a job, or run in background. Picks model and effort from repo rules or thread, asks if unknown. Claude Code and Delta.
---
# handover

New thread = independent top-level session, not a child. For a child that reports back use /delegate.

## 1 write the handover prompt
New thread starts blank. Prompt must stand alone: goal, state so far, decisions made and why, files and paths touched, open questions, next steps, constraints from user and repo, what done looks like. Include `git branch` and dirty files if relevant. No "as discussed".

## 2 choose model and effort
Follow `../delegate/references/choose.md`. Size up the work the new thread will do next. Before launch. Nothing decides it: default (inherit, medium); ask only if cost or risk high.

## 3 launch
Delta: use Delta's tool for creating a top-level thread. Pass prompt, model, effort if it takes them. It returns a link.
Claude Code (model `opus` `sonnet` `haiku` or full id; effort `low` `medium` `high` `xhigh` `max`): write the prompt to a file, then launch from the repo dir:
```bash
f=$(mktemp) && cat > "$f" <<'PROMPT'
<handover prompt>
PROMPT
claude --bg --name <short-task-name> --model <model> --effort <effort> --permission-mode bypassPermissions "$(cat "$f")"
```
Prints `backgrounded · <id> · <name>`. Keep the id.
Fails `Workspace not trusted`: tell user to run `claude` once in this dir and trust it, then retry.
Session may move into a worktree under `.claude/worktrees/`. Tell user if the task needs the main working copy.
Unsure which harness: in Delta if Delta thread tools are listed, else Claude Code.

## 4 tell the user where it is
Last thing in the reply, highlighted, so it is not missed. Then stop; do not poll.

Delta:
> **➡️ New thread: <link>**
> Model `<m>`, effort `<e>`.

Claude Code:
> **➡️ New thread running in background: `<name>` (id `<id>`)**
> **Open it: run `claude agents` in this directory** (`<absolute cwd>`), or `claude attach <id>`.
> Output so far: `claude logs <id>`. Stop: `claude stop <id>`.
> Model `<m>`, effort `<e>`.

## never
Launch before model and effort are settled. Put secrets in the prompt. Claim the thread finished: it only started.
