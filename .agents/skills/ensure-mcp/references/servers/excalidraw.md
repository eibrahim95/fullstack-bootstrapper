---
id: excalidraw
transport: stdio
command: npx
args: -y mcp-excalidraw-server
env: EXPRESS_SERVER_URL=http://127.0.0.1:8890
check: server named `excalidraw` in client config (see clients.md) with env EXPRESS_SERVER_URL=http://127.0.0.1:8890
---
note: needs node (npx). Package mcp-excalidraw-server on npm. First run downloads it.
note: tools show as mcp__excalidraw__* in Claude Code.
note: canvas server port comes from EXPRESS_SERVER_URL. Package default is 3000, too common, so we use 8890.
note: entry present with other or missing EXPRESS_SERVER_URL: counts as missing. Change = set that env only.
