---
id: just
check: just --version
preferred: script
---
apt: sudo apt install -y just
dnf: sudo dnf install -y just
pacman: sudo pacman -S --noconfirm just
brew: brew install just
winget: winget install --id Casey.Just -e
script: curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin
note: apt may lack just on old releases. Use script.
