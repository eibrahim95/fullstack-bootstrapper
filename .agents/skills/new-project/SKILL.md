---
name: new-project
description: Capture a new project idea as seed for the project pipeline. Use when user has an app idea, or /project says new. Creates .bootstrap/projects/NN/ with idea.md and status.json.
---
# new-project
Capture only. No spec, no research.
Source: apexyard `idea` skill (MIT), ai-hero `grilling` round format (MIT).

## fields
All required, non-empty. Arg text = title draft.
- title: short name
- one_liner: one sentence, what it does
- target_user: who uses it
- problem: pain it solves
- submitter: default `github.login` in `.bootstrap/setup.json`, else `git config user.name`

## ask
ONE round. Numbered, each with recommended answer so "yes" accepts. Derive recommendations from arg and chat so far.
```
❓ **Q1** - **Title**: ...

➡️ <recommended>

---
❓ **Q2** - **One-liner**: ...
```
Q1 title, Q2 one-liner, Q3 target user, Q4 problem, Q5 submitter, Q6 notes (optional, default none).
Empty answer on a required field: ask that field again. Loop until filled.

## duplicate
Read `title` of every `.bootstrap/projects/*/status.json`.
Normalize: lowercase, strip punctuation, split to tokens.
>= 80% of tokens of the shorter title in the longer: flag.
Ask: `Similar: NN <title>. Duplicate (skip) or add anyway?`
Duplicate: stop, say `/project NN`, report skipped.

## create
1. `mkdir -p .bootstrap/projects`.
2. NN = highest numeric dir name + 1, two digits zero padded (100 after 99). None: 01.
3. slug = title lowercase kebab, `[a-z0-9-]` only, max 40 chars, no edge dashes.
4. Dir `.bootstrap/projects/NN` exists: never overwrite. Pick next free NN.
5. Write `idea/idea.md`:
```
# <title>
<one_liner>

- Target user: <target_user>
- Problem: <problem>
- Submitter: <submitter>
- Created: <YYYY-MM-DD>

## Notes
<notes, section only if given>
```
6. Write `status.json`:
```json
{"flow":"project","id":"NN","slug":"<slug>","title":"<title>","state":"idea-captured",
 "idea":{"one_liner":"...","target_user":"...","problem":"...","submitter":"...","created":"YYYY-MM-DD"},
 "steps":[
  {"id":"idea","status":"done","path":"idea","result":"new-project: done NN idea/"},
  {"id":"validation","status":"pending","path":null,"result":null},
  {"id":"spec","status":"pending","path":null,"result":null},
  {"id":"journeys","status":"pending","path":null,"result":null},
  {"id":"wireframes","status":"pending","path":null,"result":null},
  {"id":"html-prototype","status":"pending","path":null,"result":null},
  {"id":"bootstrap","status":"pending","path":null,"result":null}]}
```
Escape JSON strings.

## validate
Ask: `Validate now? /validate-idea NN (y/n, default n)`.
Yes: call /validate-idea NN. It owns its step.
No: say `run /project NN` to continue.

## report
Last line, exactly one (printed after validate step):
`new-project: done NN idea/`
`new-project: skipped NN` (duplicate)
`new-project: failed <reason>`

## never
Write outside `.bootstrap/projects/NN/`. Edit other projects. Overwrite existing dir.
