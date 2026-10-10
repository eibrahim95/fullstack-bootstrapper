---
id: zed
check: zed --version || zeditor --version
preferred: script
---
script: curl -f https://zed.dev/install.sh | sh
brew: brew install --cask zed
pacman: sudo pacman -S --noconfirm zed
note: some distros name the binary zeditor.
