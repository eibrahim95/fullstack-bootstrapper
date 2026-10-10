---
name: ensure-git
description: Ensure git works with GitHub. Use after git and gh are installed. Picks the GitHub account, checks ssh agent, ssh key for github.com, gh login with Projects scope. GitHub only.
---
# ensure-git

GitHub only. Host github.com. Other host: say unsupported. Stop.
Need git, gh, ssh, ssh-keygen on PATH. Missing: call /ensure-installed <tool>. Not ok: stop.

## account
Pick GitHub account first. Ssh key and gh login must both be this account.
1. Read `.bootstrap/setup.json` if exists. `github.login` set: that is saved. Never write that file. Setup does.
2. List gh logins: `gh auth status -h github.com`, lines "Logged in to github.com account <login>".
3. Saved login still in list: use it. Say so. Next.
4. Else one login: use it. Say so.
5. Else many: ask user which. Use the ask tool, one option per login (tool allows 4 options; more: user types it in Other). Header: GitHub account. Use answer.
6. Else none: no account yet. Check 2 and 3 find it. Check 3 login sets account.
7. Not active: `gh auth switch -h github.com -u <login>`. Ask OK first.
Keep <login> as the account. Later checks must match it.

## loop
Per check, in order:
1. Run check. Pass: say so. Next check.
2. Fail: give instruction. One step at a time. Wait for user.
   Interactive cmd (passphrase, browser): tell user run `! <cmd>`.
3. Run check again. Pass: next check.
4. Still fail: say what failed, likely cause (see fixes), fix. Wait. Back to 3.
   User gives up: report failed.

## checks
### 1 agent
Check: `ssh-add -l`. Exit 0 or 1: ok. Exit 2: agent not reachable.
Fix: `eval "$(ssh-agent -s)"` for this shell. Long term: systemd user unit (`systemctl --user enable --now ssh-agent`) or desktop keyring. macOS: agent runs by default.
Note: this is ssh-agent, not sshd. Git needs client side only.

### 2 ssh
Check: `ssh -T git@github.com`. Exit 1 and text "successfully authenticated": auth ok. Username from greeting.
Account set and greeting username differs: wrong key wins. Not ok. Ask which key belongs to <login> (see config branch). Fix `IdentityFile`. Test one key: `ssh -i <key> -o IdentitiesOnly=yes -T git@github.com`.
No account yet: greeting username becomes account.
Fail: list `~/.ssh/*.pub`.
- No keys: offer new key.
  `ssh-keygen -t ed25519 -C <email> -f ~/.ssh/id_ed25519_github`. User runs it (passphrase).
  Then `ssh-add ~/.ssh/id_ed25519_github`.
  Show `cat ~/.ssh/id_ed25519_github.pub`. Tell user: add at https://github.com/settings/ssh/new (type: authentication key). Wait.
- Keys exist, no `Host github.com` in `~/.ssh/config`:
  Ask which key. Ask GitHub name and email. Default from `git config --global user.name|user.email`. Offer noreply: `<id>+<login>@users.noreply.github.com`.
  Show block, ask OK:
  ```
  Host github.com
    HostName github.com
    User git
    IdentityFile <key>
    IdentitiesOnly yes
    AddKeysToAgent yes
  ```
  OK: copy config to `~/.ssh/config.bak.<date>`, append block, `chmod 600 ~/.ssh/config`.
  Ask OK, then `git config --global user.name`, `user.email`.
- Key and config ok, still fail: see fixes.

### 3 gh
Check: `gh auth status -h github.com` logged in, scopes `repo`, `read:org`, `project`.
Account set: it must be logged in, and active (`gh auth switch` if not).
Then: `gh project list --owner @me --limit 1` exit 0. This is the real test. @me = active account.
Not logged in: user runs `! gh auth login -h github.com -p ssh -w`.
Only scope missing: user runs `! gh auth refresh -h github.com -s project`.

## fixes
- `Permission denied (publickey)`: key not on GitHub, or wrong key. Check `ssh -vT git@github.com 2>&1 | grep -i offer`. Add pub key. Check IdentityFile path.
- `Bad owner or permissions`: `chmod 700 ~/.ssh; chmod 600 ~/.ssh/config ~/.ssh/id_*`; pub keys 644.
- `Could not open a connection to your authentication agent`: agent not running. Check 1.
- key asks passphrase every time: `ssh-add <key>`. Config has AddKeysToAgent.
- ssh times out on port 22: network blocks it. Use `Host github.com` + `HostName ssh.github.com` + `Port 443`. Ask OK first.
- `gh auth login` refuses: `GH_TOKEN` or `GITHUB_TOKEN` is set. Unset it, or fix token scopes.
- project cmd says missing scope: `gh auth refresh -h github.com -s project`.
- project cmd 403 on org: org SSO. Authorize token at https://github.com/settings/tokens or via `gh auth refresh`. Org may block apps.
- fine-grained token: needs Projects permission. Use `gh auth login` instead.

## report
Last line, exactly one:
`ensure-git: done <login>`
`<login>` = chosen account. Setup saves it in `github.login`.
`ensure-git: failed <check>: <reason>`
`<check>` = agent, ssh, gh, or prereq.

## never
Read or print private key. Overwrite key or config. Run state-changing cmd without OK. Install tools itself. Write .bootstrap. Ask when saved or only account fits.
