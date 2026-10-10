---
name: validate-idea
description: Validate idea with 5 questions, verdict GREEN/YELLOW/RED. Use after /new-project, before /write-spec. Writes validation/validation.md, sets validation step.
---
# validate-idea

Source: apexyard validate-idea (MIT), adapted.
Not Wardley, not canvas, no rubric. Five plain questions, one per turn, then verdict.

## project
Arg `NN` (or slug), optional `override`. No arg: one project not bootstrapped -> use it; several -> numbered list (id, title, state), ask; none -> say run /new-project.
Dir: `.bootstrap/projects/NN/`. Missing id: error.
Need step `idea` done. Else stop: "run /new-project".
Step `validation` already `done`: ask overwrite. No: report skipped. Yes: redo, warn later steps may be stale.

## override
Arg `override` and step `validation` is `failed` with RED: user explicit override. Skip questions.
Set step done, path `validation`, result `validate-idea: done NN validation/ RED overridden`, state `idea-validated`. Add line `Overridden by user <date>` to `validation/validation.md`. Report that line.
Step not RED-failed: ignore arg, run normally.

## context
Read `idea` in `status.json`, `idea/idea.md`. Show 3-5 lines: title, one_liner, target_user, problem. User can correct in first answer.

## questions
ONE AT A TIME. Wait for answer before next. One probe max per question. Still weak after probe: record as is, let it show in verdict.
No web research. Alternatives come from user.

1 Target user. Show `idea.target_user`. Ask: confirm or sharpen? Role, context, moment of need. "Everyone" or vague: probe once: narrowest plausible group, who benefits MOST in first 30 days?
2 Current alternative. What do they do today instead? Competitor name, manual workaround, or "nothing". "Nothing": probe once: real-but-low-priority or fictional gap? What evidence?
3 Smallest version. Smallest thing that proves value, 1-2 days max, not the MVP. Answer >= 1 week: probe once: cut in half, which half tells you the rest is worth building?
4 Kill criteria. What concrete observation tells you to park this? Cannot articulate: that is signal, note it.
5 Build, buy, or rent.
  - BUILD: differentiating, moat is the implementation
  - BUY: commodity, adopt OSS or product
  - RENT: utility, pay a SaaS
  BUILD but Q2 alternative is a working product: probe once: what angle do they lack? "Do it better" is no moat; real differentiator or BUY.

## verdict
Read all five together. Judgement, no rubric, no scores.
- GREEN: concrete user, clear alternative being beaten, small slice fits 1-2 days, kill criteria articulable, build/buy/rent fits.
- YELLOW: kernel exists, one or two answers weak, needs reshaping.
- RED: two or more weak, or BUILD with no differentiator, or no kill criteria.
One line, bold, one-sentence reason.

## write
`validation/validation.md` in project dir. One page, read-out <= 4 sentences. Template: [references/validation-template.md](references/validation-template.md).

## status
Edit only step `validation` + top-level `state`. Keep other keys.
- GREEN: step done, path `validation`, result `validate-idea: done NN validation/ GREEN`, state `idea-validated`.
- YELLOW: ask user: proceed or park?
  - proceed: step done, path `validation`, result `validate-idea: done NN validation/ YELLOW`, state `idea-validated`.
  - park: step failed, result `validate-idea: failed YELLOW parked: <criterion to sharpen>`. State unchanged.
- RED: step failed, result `validate-idea: failed RED <reason>`. State unchanged. Later skills refuse to run. Tell user: `/validate-idea NN override` to proceed anyway.

## handoff
GREEN or proceeding: name `/write-spec NN` as next. Do not run it.

## report
Last line, exactly one: the step `result` string.

## anti-pattern
Batching all five questions in one message. User answers shallow, skips thinking. Ask one, wait, ask next.

## never
Auto-run /write-spec. Write outside `validation/` and own step. Score with rubric. Print secrets.
