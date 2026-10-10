---
id: delta
check: (test -d ~/.local/delta.app || test -d ~/Applications/Delta.app || test -d /Applications/Delta.app) && delta --version
preferred: script
---
script: f=$(mktemp) && curl -fsSL https://delta.dev/install.sh -o "$f" && sh "$f" --non-interactive
note: Delta = Zed Industries app, docs delta.dev. NOT git-delta pager. Same cmd name, so check tests app dir.
note: script is user-level. Linux needs python3. Puts cli at ~/.local/bin/delta. Needs PATH.
note: Mac manual: Delta.app to /Applications, then Delta > Install CLI (may ask admin). Not scripted.
note: needs Zed account + Early Access Agreement. Sign in is not this skill.
