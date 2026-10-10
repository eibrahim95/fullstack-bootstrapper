---
id: claude-code
check: claude --version
preferred: script
---
script: curl -fsSL https://claude.ai/install.sh | bash
brew: brew install --cask claude-code
npm: npm install -g @anthropic-ai/claude-code
note: script puts claude in ~/.local/bin. Needs PATH. Login is not this skill.
