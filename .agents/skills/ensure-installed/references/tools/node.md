---
id: node
check: . ~/.nvm/nvm.sh 2>/dev/null; node --version && npx --version
preferred: script
---
script: ([ -s "$HOME/.nvm/nvm.sh" ] || curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | PROFILE="$HOME/.bashrc" bash) && export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm install node
apt: sudo apt install -y nodejs npm
dnf: sudo dnf install -y nodejs npm
pacman: sudo pacman -S --noconfirm nodejs npm
brew: brew install node
winget: winget install --id OpenJS.NodeJS.LTS -e
note: script = nvm via official installer, then latest node (`nvm install node`). User-level, no sudo.
note: installer appends nvm loader to ~/.bashrc. New shell or `. ~/.bashrc` needed. Other shells: not handled.
note: nvm pinned v0.40.8. Newer tag: github.com/nvm-sh/nvm/releases.
note: npx ships with node.
