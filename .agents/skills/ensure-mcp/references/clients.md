# clients
Server entry comes from references/servers/<id>.md. Below: `<name>` = id, `<cmd>` `<args...>` = command and args, `<ENV>` = env pairs (none: omit).
Backup before any edit: `cp -p <file> <file>.bak-$(date +%Y%m%d%H%M%S)`. File missing: no backup, create it.
JSON/TOML merge: parse, add only the one key, write back. Keep everything else. Use `python3`/`jq` (JSON) or append a table (TOML). Never rewrite whole file from template.
Prefer CLI where one exists. CLI edits the file itself: backup first anyway.

## claude-code
- detect: `command -v claude`
- file: `$CLAUDE_CONFIG_DIR/.claude.json` if var set, else `~/.claude.json`. Key `mcpServers.<name>` (user scope).
- check: `claude mcp get <name>` exit 0. Or `claude mcp list | grep -i '^<name>:'`.
- add: `claude mcp add --scope user [-e K=V] <name> -- <cmd> <args...>`
- json fallback: `"mcpServers":{"<name>":{"type":"stdio","command":"<cmd>","args":[...],"env":{}}}`
- note: `claude mcp list` runs health checks, slow.

## codex
- detect: `command -v codex`
- file: `${CODEX_HOME:-~/.codex}/config.toml`. Table `[mcp_servers.<name>]`.
- check: `codex mcp list` has row `<name>`. Or `grep -F '[mcp_servers.<name>]'` in file.
- add: `codex mcp add [--env K=V] <name> -- <cmd> <args...>`
- toml fallback:
  ```
  [mcp_servers.<name>]
  command = "<cmd>"
  args = ["..."]
  env = { K = "V" }
  ```

## opencode
- detect: `command -v opencode`
- file: `~/.config/opencode/opencode.json` (`$XDG_CONFIG_HOME/opencode/` if set). Also `.jsonc` variant: use whichever exists.
- check: key `mcp.servers.<name>` or `mcp.<name>` present in file (`jq -e`). Both shapes exist, see below.
- add: `opencode mcp add --global [--env K=V] <name> -- <cmd> <args...>`
  Without `--global` writes project config. CLI picks the shape this version wants.
- json fallback: `command` is one array, env key is `environment`. Follow shape already in file:
  - file has `mcp.servers` (opencode v2, CLI writes this): `"mcp":{"servers":{"<name>":{"type":"local","command":["<cmd>","<args>"],"environment":{}}}}`
  - else (opencode docs): `"mcp":{"<name>":{"type":"local","command":["<cmd>","<args>"],"environment":{},"enabled":true}}`
  - no `mcp` key: use CLI.
- note: `opencode mcp list` can hang. Prefer file check.

## zed
- detect: `command -v zed || command -v zeditor`, or settings dir exists.
- file: Linux/mac `~/.config/zed/settings.json` (`$XDG_CONFIG_HOME/zed/`). Windows `%APPDATA%\Zed\settings.json`. Zed settings are JSONC (comments, trailing commas): do not parse with strict JSON. Edit text, insert one entry inside `context_servers`, keep rest byte-identical. Ask user to edit by hand if unsure.
- check: `context_servers` object has key `<name>`. (`grep -n '"<name>"'` inside that block.)
- add: no CLI. Merge key:
  `"context_servers":{"<name>":{"command":"<cmd>","args":[...],"env":{}}}`
  `context_servers` missing: add it. Zed docs: also `url` + `headers` for remote.
