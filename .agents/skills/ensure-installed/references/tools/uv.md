---
id: uv
check: uv --version
preferred: script
---
script: curl -LsSf https://astral.sh/uv/install.sh | sh
brew: brew install uv
pacman: sudo pacman -S --noconfirm uv
winget: winget install --id astral-sh.uv -e
note: script puts uv in ~/.local/bin. Needs PATH.
