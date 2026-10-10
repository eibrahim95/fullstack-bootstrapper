---
name: ensure-mcp
description: Ensure MCP server configured in agent clients. Use when agent needs an MCP tool. Arg `list` shows supported servers. Arg `<server>` checks and adds it to Claude Code, Codex, opencode, Zed. Edits client configs after OK.
---
# ensure-mcp

Arg: `list` or `<server>`.

## list
Read references/index.md. Print it. Stop.

## server
1. Find arg in references/index.md. Match id or alias. Ignore case.
   Miss: say "not in registry". Report failed. Stop.
2. Read references/servers/<id>.md. Read references/clients.md.
3. Per client: run its detect cmd. Not installed: mark skipped, say so.
4. Per installed client: run its check. Present: mark present.
5. Nothing missing: report present. Stop.
6. Missing clients: per client show exact change (CLI cmd, or file + JSON/TOML keys). Ask OK. No OK: that client stays skipped.
   Server needs prereq (npx): check on PATH first. Missing: /ensure-installed node.
7. On OK: back up config (see clients.md), apply. Merge, never overwrite. Config unparsable: stop that client, report failed.
8. Run check again per edited client. Fail: say why, restore backup.
9. Server file has `note`: tell user. Say running agent sessions need restart.

## report
Last line, exactly one:
`<server>: present <clients>`
`<server>: installed <clients>` (clients changed now)
`<server>: skipped` (no client installed or no OK)
`<server>: failed <reason>`
`<clients>` = comma list: claude-code, codex, opencode, zed.
`<server>` = name caller gave, not id.

## never
Edit config without OK or backup. Overwrite config. Log in. Set secrets. Edit registry. Touch other servers.
