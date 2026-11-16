---
id: rust
check: rustup --version && cargo --version
preferred: script
path: source "$HOME/.cargo/env"
---
script: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
winget: winget install --id Rustlang.Rustup -e
note: script = the official rustup installer with its default profile: rustc, cargo, rustfmt and clippy. User-level, into ~/.cargo and ~/.rustup, no sudo.
note: the installer appends its loader to the shell rc files, so a new shell has cargo on PATH. path: sources ~/.cargo/env in the current shell. Check fails, and ~/.cargo/env exists: show the path cmd, ask OK, run it, then tell the user to reload the terminal.
note: distro packages (apt rustc, dnf rust) ship older toolchains than a repo's rust-toolchain.toml asks for. `rustup toolchain install <version>` adds a pinned one, and rustup switches to it on its own inside that repo.
