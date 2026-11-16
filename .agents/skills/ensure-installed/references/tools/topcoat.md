---
id: topcoat
check: topcoat --version
preferred: cargo
---
cargo: cargo install topcoat-cli --version 0.12.1 --locked
note: needs rust first. Run `/ensure-installed rust` when cargo is missing.
note: the CLI version moves together with the `topcoat` crate pinned in the app. Upgrade both in one step.
note: the binary lands in ~/.cargo/bin, which the rust installer puts on PATH. It also runs as `cargo topcoat`.
