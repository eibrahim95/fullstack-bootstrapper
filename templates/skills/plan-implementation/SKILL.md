---
name: plan-implementation
description: Split the whole product PRD into milestones and the specs inside each one. After approval, run /to-spec once per spec and group those issues under their milestones. Use in the app repo after bootstrap, before /to-tickets. A milestone is one release, smaller than the PRD and larger than a spec. Filing them is planning, not implementing them all at once.
disable-model-invocation: true
---
# plan-implementation

The PRD is the whole project. A milestone is one release cut from that project: bigger than a spec, smaller than the PRD. One PRD becomes several milestones. Each milestone holds only the specs that ship in that release. The set of all specs is not one milestone.

A spec is one outcome whose integration branch can be merged and reviewed on its own. If one review of that branch would be too large to read, the spec is still too big. A spec is not a milestone.

This skill proposes every milestone, in merge order, and the specs inside each one. After approval, `/to-spec` publishes each spec as one issue. This skill then creates every milestone and assigns each issue to its milestone. That is the plan. It is not a request to implement every release in one run.

`/to-tickets` writes the tracer bullets, one spec at a time, as children of that spec's issue. The user runs `/implement-spec` later, once per spec issue. Not from a milestone, and not for every spec in one run.

## where things are

This repo, and `gh` for this repo. Planning files sit in the sibling `artifacts` directory beside this repo. From the repo root (`git rev-parse --show-toplevel`): `../artifacts`.

| path | what |
|---|---|
| `../artifacts/spec/spec.md` | the PRD. Required. |
| `../artifacts/wireframes/screen-inventory.md` | screens and the PRD stories they cover, when `../artifacts/wireframes/` exists. |
| `../artifacts/html-prototype/` | the prototype, when it exists. Each screen is one or more HTML files whose name starts with its screen id (`<id>.html`, plus Arabic or phone variants such as `<id>.ar.m.dc.html`), found with `find ../artifacts/html-prototype -name '<id>.*html'`. Its `README.md` names any hosted copy (a claude.ai canvas or design system link) and its design files (`DESIGN.md`, `PRODUCT-RULES.md`, a `design-system/` folder). |

An argument that is an absolute path to an artifacts directory replaces `../artifacts`. Missing `spec/spec.md`: stop. Do not go looking in another checkout.

`gh repo view --json nameWithOwner -q .nameWithOwner` must print this repo. Otherwise stop: `plan-implementation: failed github: <reason>`.

## 1 Read

Read the PRD. When the wireframes directory exists, read `screen-inventory.md` too. When the prototype exists, read its `README.md` only: note the hosted links and the design files it names, and do not open the screen files. Product goals, non-goals, metrics, and validation notes stay in the PRD. A spec cites them and does not restate them.

Done when every PRD flow is in mind and, if wireframes exist, every screen id is tied to the stories it covers.

## 2 Propose every milestone and its specs

Split the whole PRD. Do not stop after the first milestone. Milestones are in merge order: an earlier release does not need a later one. Each milestone is one release a user could ship. It is smaller than the PRD and larger than a spec. Together the milestones cover the PRD, and the set of all specs is not one milestone.

Show milestone, then its specs. For each milestone: title, and which PRD flows or outcomes ship in it. Then that milestone's specs. Each spec:

- One outcome a user can see or a reviewer can check. Not a layer (not "the database", not "the UI").
- Its integration branch merges on its own.
- One person can review that branch in one sitting. Over that line, split.
- Not a release and not a milestone. The specs in one milestone cover that release.

For each spec: title, the outcome, why the review is one sitting, the PRD story numbers, the wireframe screen ids when wireframes exist, and what is left to other specs or later milestones.

Every PRD story is in exactly one spec. Every spec is in exactly one milestone.

Ask `Approve this breakdown? (y/n)`. On no, ask what to move between milestones or between specs, show the full list again, and wait. No issue and no milestone until the answer is yes.

## 3 Publish each spec with /to-spec

Only after that yes. `/to-spec` writes the issue body and publishes it. This skill does not.

If `/to-spec` is not available, stop: `plan-implementation: failed prereq: /to-spec`. Do not write the issues yourself.

For each approved spec, in list order:

- An issue with that exact title already (`gh issue list --state all --limit 200 --json number,title`): keep it. Do not invoke `/to-spec` again.
- Otherwise invoke `/to-spec` once. The context for that invocation is only this spec: its title, the milestone it belongs to, the outcome, the PRD stories and decisions that belong to it, and what is out of scope. When the prototype exists, add a **Design reference** for this spec: each of its screen ids with the prototype file paths for that id (absolute paths), the hosted canvas link from the prototype README with the note that the screen ids are the names on its screen map, and the design files and design-system folder the README names. Say the prototype is the visual reference to build against: read it, do not copy its files into the app. Local paths are for agents (they cannot open claude.ai links); the link is for people and Claude sessions. One invocation publishes one issue. Do not hand it the whole PRD, the whole milestone, or another spec's decisions.

Keep each issue's number and URL. Done when every approved spec has one issue.

## 4 Milestones

One GitHub milestone per approved release. Description, exact: `Progress view of this release's spec issues.`

```
gh api "repos/{owner}/{repo}/milestones?state=all" --jq '.[] | {number,title,state,html_url}'
```

For each approved title: an open milestone with that exact title is reused. None open: create one.

```
gh api repos/{owner}/{repo}/milestones -f title="<title>" -f description="Progress view of this release's spec issues."
```

A closed milestone with the same title is an earlier release. Do not reopen it. Create the approved one only when no open milestone has that title.

Assign each spec issue to its milestone:

```
gh issue edit <number> --milestone "<milestone title>"
```

Done when every approved milestone exists and every spec issue from step 3 is on its milestone.

## report

For each milestone, in merge order: its URL, then each of its specs (number, title, URL). Say each milestone is the progress view for that release, not the whole PRD, and that filing them is the plan.

Next, in that same order, one line per spec: `/to-tickets <number>`, and after that spec's tickets exist, `/implement-spec <number>`. The user runs those later, one spec at a time, starting at the first milestone. This skill does not implement them.

If `/to-tickets` says to run `/setup-matt-pocock-skills`, the user does that in this repo and chooses GitHub. Do not run it from here.

Last line, exactly one:

| outcome | line |
|---|---|
| published | `plan-implementation: done <n> milestones, <m> specs` |
| user stopped without approving | `plan-implementation: skipped` |
| failed | `plan-implementation: failed <github\|prereq>: <reason>` |

## never

- File an issue or a milestone before the full breakdown is approved.
- Stop after the first milestone, or put the whole PRD on one milestone.
- Publish the whole PRD as one spec, or call a milestone a spec.
- Write a spec issue body, or invoke `/to-spec` once for more than one spec.
- Implement the specs in this run.
- Generate tracer-bullet tickets, blocking edges, or sub-issues.
- Point `/implement-spec` at the milestone.
- Close a spec issue.
- Read the PRD from anywhere except the artifacts directory above.
- Paste prototype markup into an issue. When the prototype exists, leave a spec with screens out of its design reference.
