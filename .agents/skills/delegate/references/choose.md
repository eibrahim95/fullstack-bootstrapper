# choose model and effort

Harness-neutral. Judge the work the child or new thread does next, not work done so far. Never guess.

## 1 explicit wins
User said model or effort, or repo rules fix it (`AGENTS.md`, `CLAUDE.md`, nested ones, harness settings): use it. Rules give range or table: pick inside it by 3-6.

## 2 delegate at all?
Skip delegation, do it here: one dependent chain, fits in this context, small task. Split costs plan + handoff + merge.
Delegate: independent pieces, read-heavy work that bloats context, true background work.
Skipping: tell user, stop.

## 3 size up the work
- Reasoning: judgment per step. Design, vague spec, hard debug, security = high. Clear recipe, mechanical edit, lookup = low.
- Volume: tokens read, written, looped. Many files, long logs, many tool calls = high.
- Risk: wrong result is costly (prod, data, irreversible, user-facing) = one tier up, plus review.

## 4 pick tier
Tiers relative. Map to harness models by capability and price.

| reasoning | volume | tier |
| :- | :- | :- |
| high | low | strong |
| high | high | split, see below |
| low | high | small or mid, cheapest that holds |
| low | low | small |

High+high, pick one:
- Orchestrator: strong plans and merges, mid workers do bulk.
- Advisor: mid runs the loop, asks strong on hard calls. Cheap runners rarely ask. Give them explicit triggers: stuck twice, failed check, unclear spec, risky step.
No clear winner: take advisor if work is one chain, orchestrator if parts are independent.

Unsure between two tiers: cheaper if wrong result is easy to spot and redo, stronger if not.

## 5 pick effort
Try lower effort on the chosen model before moving up a tier.
Mechanical = lowest. Normal = middle. Multi-step, vague, risky = high. Top only if hard and wrong is costly.
Lowest effort on small model skips checks and searches: add a verify step (tests, schema, review).
No effort setting: skip, say so.

## 6 escalate
Low-risk work: start cheap, verify. Check fails: move up one tier or one effort level, retry once. Fails again: tell user.

## 7 sanity check
Strong on mechanical work, or small on design work: redo 3.
Work splits by type: heavy-volume part goes to cheaper tier.

## 8 default, ask
Nothing decides it: inherit this thread's model, medium effort. Say so.
Ask only when cost or risk is high and 3 can't be scored. One question, model and effort together, harness question tool. Options = what harness lists. Recommend one, one-line reason. No launch before answer.

## values
Use only what harness lists: tool schema, CLI help, settings. Not listed: ask.

## handoff
Child gets no memory. Pass full context or written plan. Read-only children are safest cheap and parallel.

## report
Before launch, one line: `model <m>, effort <e>: <reasoning/volume/risk>, source <user|rules|inferred|default|asked>`.
