---
id: gh
check: gh --version
preferred: null
---
apt: sudo apt install -y gh
dnf: sudo dnf install -y gh
pacman: sudo pacman -S --noconfirm github-cli
brew: brew install gh
winget: winget install --id GitHub.cli -e
note: distro apt may be old. gh auth login is not this skill.
