---
name: validate-idea
description: Stress-test idea with questions, adversarial challenge, grilling loop, verdict GREEN/YELLOW/RED. Use after /new-project, before /write-spec. May amend idea. Writes validation/validation.md, sets validation step.
---
# validate-idea

Goal: find loopholes while cheap. Idea that sails through untouched is suspect, not good.
Not Wardley, not canvas, no score rubric.

## project
Arg `NN` (or slug), optional `override`. No arg: one project not bootstrapped -> use it; several -> numbered list (id, title, state), ask; none -> say run /new-project.
Dir: `.bootstrap/projects/NN/`. Missing id: error.
Need step `idea` done. Else stop: "run /new-project".
Step `validation` already `done`: ask overwrite. No: report skipped. Yes: redo, warn later steps may be stale.

## override
Arg `override` and step `validation` is `failed` with RED: user explicit override. Skip all phases.
Set step done, path `validation`, result `validate-idea: done NN validation/ RED overridden`, state `idea-validated`. Add line `Overridden by user <date>` to `validation/validation.md`. Report that line.
Step not RED-failed: ignore arg, run normally.

## phases
Run in order. Show phase name when entering.

### 1 context
Read `idea` in `status.json`, `idea/idea.md`. Show 3-5 lines. User can correct in first answer.

### 2 questions
ONE AT A TIME. Wait for answer. One probe max per question. Still weak: record as is, challenge will hit it.
No web research here: alternatives come from user. Q1 show `idea.target_user`, confirm or sharpen.
1 Target user: role, context, moment of need. "Everyone" or vague: probe once, narrowest group that benefits MOST in first 30 days?
2 Current alternative: what do they do today? Name it. "Nothing": probe once, real-but-low-priority or fictional gap? Evidence?
3 Whole product: every role, and what each does, start to finish. A demo only: probe once for the rest.
4 Risks: assumptions that could kill or reshape it (legal, cost, trust, cold start, who pays). Name them.
5 Kill criteria: what concrete observation would make you park it later? Record it on the validation. Cannot say: note it, that is signal.
6 Build, buy, or rent: BUILD differentiating; BUY commodity, adopt OSS; RENT utility, pay SaaS. BUILD while Q2 has working product: probe once, what angle do they lack? "Do it better" is no moat.

### 3 challenge
Spawn ONE fresh subagent. Fresh context on purpose: it must not share your agreement with the user.
Model and effort: per `.agents/skills/delegate/references/choose.md`. Work is high reasoning, low volume: strong tier, high effort. Pass model explicitly. Harness: per `/delegate` launch.
Lens: `.claude/agents/contrarian.md`. Target block: idea fields, the six answers, earlier decisions if re-challenge.
Claude Code: `Agent` tool, `subagent_type: contrarian`. Prompt = target block only.
Else: read that file, drop the YAML frontmatter, prompt = body + target block. Delta: spawn `scout` (web, no file edits).
Show its output to user verbatim. No softening, no summary. Disagree: say so as separate note.
Give each objection id O1.. in order.

### 4 grill
Work objections: showstopper first, then serious. worth-weighing: only if cheap. nit: list, skip.
Rounds, grilling format. Round = all independent open objections at once, numbered, each with your recommended resolution, worded so "yes" accepts:
```
❓ **Q1** - **O2 <short title>**: <objection, plain>

➡️ <recommended: change the product (a limit, a plan, a check) / check Z first>
```
Prefer meeting a risk with a change to the product (a limit, a plan, a check). Wait for answers. Next round: objections that depended on earlier answers, or answers still open.
Valid outcome per objection:
- fixed: product changes. Say the change.
- cut: user removed it from the product. Say what was removed.
- evidence: name concrete check, who, by when. Becomes open assumption.
- accepted: user takes the risk, states reason. Max 2 accepted serious risks for GREEN.
Not valid: "it will be fine", "we will see", "users will love it". Say it is not an answer, ask again once. Still hand-waving: outcome `open`.
Facts you can look up (does X exist, what does Y cost): look them up, never ask user. Use a subagent for bulk reading.
A lookup still running is an unsettled prerequisite, not a reason to wait. Ask every open objection that does not depend on it in this round. Only the ones downstream wait for the result.
Max 3 rounds, then ask: keep grilling or stop and judge with what is open.

### 5 amend
Idea fields (`title`, `one_liner`, `target_user`, `problem`) changed by a decision: show old -> new, ask OK. OK: update `idea` in `status.json` and `idea/idea.md`, only those fields, log in validation.md `Revisions to idea`. Slug and id never change.
Scope changes (add, cut, rework features) go in validation.md `Decisions`. Write-spec reads them.
This is the only time this skill edits outside its own step.

### 6 re-challenge
A showstopper or serious objection led to a change: run phase 3 once more on the revised idea, then phase 4 on what is new. Max 2 challenge rounds total. Then judge.

## verdict
Judgement from the whole run, no scores. One line, bold, one-sentence reason.
- GREEN: no open showstopper. Every serious objection fixed, cut, backed by an evidence plan, or accepted with reason. Last challenge verdict proceed or proceed-with-changes, changes applied.
- YELLOW: serious objection `open`, or key evidence pending, but a kernel exists.
- RED: showstopper open, or last verdict reconsider and user did not change the idea.
Zero changes and zero serious objections: say that plainly, name the three strongest attacks and why they failed. Do not pad.

## write
`validation/validation.md`. Template: [references/validation-template.md](references/validation-template.md). Read-out <= 4 sentences.

## status
Edit step `validation`, top-level `state`, and `idea` only per phase 5. Keep other keys.
- GREEN: step done, path `validation`, result `validate-idea: done NN validation/ GREEN`, state `idea-validated`.
- YELLOW: ask user: proceed or park?
  - proceed: step done, path `validation`, result `validate-idea: done NN validation/ YELLOW`, state `idea-validated`.
  - park: step failed, result `validate-idea: failed YELLOW parked: <criterion to sharpen>`. State unchanged.
- RED: step failed, result `validate-idea: failed RED <reason>`. State unchanged. Later skills refuse. Tell user: `/validate-idea NN override`.

## handoff
GREEN or proceeding: name `/write-spec NN` as next. Do not run it.

## report
Last line, exactly one: the step `result` string.

## never
Batch the six questions. Challenge in your own context. Soften the challenge. Accept hand-waving. Auto-run /write-spec. Write outside `validation/`, own step, and phase-5 idea fields. Print secrets.
