---
id: docker
check: docker --version
preferred: script
---
apt: sudo apt install -y docker.io
pacman: sudo pacman -S --noconfirm docker docker-compose
brew: brew install --cask docker
winget: winget install -e --id Docker.DockerDesktop
script: curl -fsSL https://get.docker.com | sh
note: script uses sudo, installs docker-ce from official repo. Installed only. Daemon start and docker group are not this skill.
