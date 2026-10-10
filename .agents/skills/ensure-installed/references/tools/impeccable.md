---
id: impeccable
check: test -f ~/.agents/skills/impeccable/SKILL.md || test -f ~/.claude/skills/impeccable/SKILL.md
preferred: npm
---
npm: npx -y impeccable install --global --yes
note: agent skill, not a CLI. Installs into ~/.agents/skills and ~/.claude/skills. User-level, no sudo. Needs node.
note: --yes takes detected harnesses. Pick others: --providers=<names>. Update later: npx impeccable update.
note: first use in agent: run /impeccable init in agent chat. Not this skill.
