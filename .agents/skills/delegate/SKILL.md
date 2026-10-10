---
name: delegate
description: Hand a bounded task to a subagent in the current thread. Use when work can run in a child and the result comes back here. Picks model and effort from repo rules or thread, asks if unknown. Claude Code and Delta.
---
# delegate

Subagent = child of this thread. Result returns here. For a new top-level thread use /handover.

## 1 delegate at all?
Check `references/choose.md` step 2 first. Not worth it: do the work here, stop.

## 2 write the brief
Child has no memory of this thread. Brief must stand alone: goal, why, files and paths, constraints, what done looks like, what to return. Short, concrete.

## 3 choose model and effort
Follow `references/choose.md`. Size up the work the child will do, not the work done so far. Before launch. Nothing decides it: default (inherit, medium); ask only if cost or risk high.

## 4 launch
Claude Code (model `opus` `sonnet` `haiku` or full id; effort `low` `medium` `high` `xhigh` `max`): `Agent` tool. Set `model`, `effort`, `description`, `prompt` (the brief). Pick `subagent_type` that fits (`Explore` read-only search, `Plan` design, `general-purpose` else). Independent children: launch in one message, parallel.
Delta: use Delta's own subagent tool. Set model and effort if it takes them.
Unsure which harness: you are in Delta if Delta thread tools are listed, else Claude Code.

## 5 after
Child runs in background: do not poll, do not duplicate its work. Result arrives, then read it, check it, restate it to user in own words.

## never
Launch before model and effort are settled. Send a brief that says "as discussed". Guess model or effort.
