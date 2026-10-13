---
name: ensure-installed
description: Ensure CLI tool installed. Use when tool missing or env setup needed. Arg `list` shows supported tools. Arg `<tool>` checks and installs it.
---
# ensure-installed

Arg: `list` or `<tool>`.

## list
Read references/index.md. Print it. Stop.

## tool
1. Find arg in references/index.md. Match id or alias. Ignore case.
2. Hit: read references/tools/<id>.md.
   Miss: read references/generic.md. Tell user "not in registry".
3. Run check cmd. Found: report present. Stop.
4. Detect env: os, distro, arch, pkg managers on PATH.
5. Pick install line.
   `preferred` set and usable here: take it. Say it is user-level.
   Usable = key is pkg manager on PATH, or script (curl), binary (curl, unzip), npm, cargo and tool on PATH.
   `preferred` null or unusable: take line whose key matches a pkg manager on PATH.
   No match: read generic.md.
   Many match: recommend one. Ask user.
   Prefer no sudo. Warn when line uses sudo.
6. Show exact cmd. Ask OK. Run. No OK, no run.
7. Run check cmd again.
   Pass: continue.
   Fail and tool has a `path:` note: that note is a step, not only a tell. Condition true: show path cmd, ask OK, run. No OK: failed, stop. Then tell user to reload the terminal. Then step 8. Report installed. Stop. Do not recheck in this shell.
   Condition false: say why. Stop.
   No `path:` note: say why. Stop.
8. Tool file has `note`: tell user. The `path:` note was already done in step 7. Still tell it.

## report
Last line, exactly one:
`<tool>: present <version>` (no version: omit)
`<tool>: installed <version>`
`<tool>: skipped`
`<tool>: failed <reason>`
`<tool>` = name caller gave, not id.

## never
Install without OK. Configure or log in. Edit registry. Other skills do that.
