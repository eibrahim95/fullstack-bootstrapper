---
id: cookiecutter
check: command -v cookiecutter
preferred: uv
---
uv: uv tool install cookiecutter
pipx: pipx install cookiecutter
brew: brew install cookiecutter
apt: sudo apt install -y cookiecutter
note: uv puts it in ~/.local/bin, user-level, no sudo. Needs PATH. Version: cookiecutter --version.
note: apt ships older release. Prefer uv.
