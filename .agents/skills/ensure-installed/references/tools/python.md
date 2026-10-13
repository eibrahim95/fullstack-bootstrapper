---
id: python
check: python3 --version 2>&1 || python --version 2>&1 || py --version 2>&1 || python3.14 --version 2>&1 || python3.13 --version 2>&1 || python3.12 --version 2>&1 || python3.11 --version 2>&1 || python3.10 --version 2>&1
preferred: uv
path: uv python update-shell
---
uv: uv python install --default
brew: brew install python
apt: sudo apt install -y python3
dnf: sudo dnf install -y python3
pacman: sudo pacman -S --noconfirm python
winget: winget install --id Python.Python.3.13 -e
note: any of python3, python, py, or python3.10–3.14 on PATH counts. Found: present, stop. Do not install another.
note: uv is user-level, no sudo. `--default` links python and python3 into `uv python dir --bin` (usually ~/.local/bin). Without `--default` only python3.x is linked.
note: path: only after the uv line. Check fails, and `uv python dir --bin` contains python or python3, and that dir is not on PATH. Show the path cmd. Say it edits the shell rc. Ask OK. No OK: failed, stop. Run it. Version: `"$(uv python dir --bin)/python3" --version` or python in that dir. Tell the user to reload the terminal. This shell will not see it. Report installed. Do not recheck here.
