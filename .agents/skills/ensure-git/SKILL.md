---
name: ensure-git
description: Ensure git works with GitHub. Use after git and gh are installed. Picks the GitHub account, checks ssh agent, ssh key for github.com, gh login with Projects scope. GitHub only.
---
# ensure-git

GitHub only. Need git, gh, ssh on PATH. Missing: /ensure-installed <tool>.
Check fails: give fix, one step, wait. Interactive cmd: tell user run `! <cmd>`. Verify again. Still fails: say cause, fix.
User gives up: report failed.

## account
Setup file `.bootstrap/setup.json` has `github.login`, `github.email`: saved. Read only.
gh logins: `gh auth status -h github.com`.
Saved still logged in, or only one login: use it. Many: ask user which, ask tool, one option per login.
None: check 3 sets it.
Not active: ask OK, `gh auth switch -h github.com -u <login>`.
ssh key and gh must be this account.

## email
One <email> for whole run. Find, first hit wins:
1 saved `github.email`. 2 `git config --global user.email`. 3 gh: `gh api user -q .email`, else noreply `<id>+<login>@users.noreply.github.com` (`gh api user -q .id`). 4 comment in `~/.ssh/*.pub`.
Hit: tell user "will use <email>", ask OK. No: ask for another.
No hit: ask user for email.
Set `git config --global user.email <email>` if unset or different, after OK.

## checks
1 agent: `ssh-add -l` exit 0 or 1 ok. 2: `eval "$(ssh-agent -s)"`, or systemd/keyring for long term. Not sshd.

2 ssh: `ssh -T git@github.com` says "successfully authenticated" as <login>. Other user: wrong key.
- No keys in `~/.ssh`: user runs `ssh-keygen -t ed25519 -C <email> -f ~/.ssh/id_ed25519_github`, then `ssh-add` it. Show .pub. Tell user add at https://github.com/settings/ssh/new, then verify again.
- Keys, no `Host github.com` in `~/.ssh/config`: ask which key. Confirm GitHub name. Show block, ask OK. Back up config, append, `chmod 600`. Set `git config --global user.name`.
  `Host github.com`, `User git`, `IdentityFile <key>`, `IdentitiesOnly yes`, `AddKeysToAgent yes`.
- Still fails: key not on GitHub. `ssh -vT git@github.com` shows keys offered. Port 22 blocked: `HostName ssh.github.com`, `Port 443`.

3 gh: `gh auth status` has <login>, scopes `repo`, `read:org`, `project`. Then `gh project list --owner @me --limit 1` exit 0.
Not logged in: `! gh auth login -h github.com -p ssh -w`. Scope missing: `! gh auth refresh -h github.com -s project`.
Login refused: `GH_TOKEN` set. Unset. Org 403: authorize SSO.

## remote
Not bootstrapper repo (no `.agents/skills/ensure-git`): skip.
`git remote get-url origin` works: leave it.
None: ask OK, `git remote add origin git@github.com:eibrahim95/fullstack-bootstrapper.git`.

## report
Last line, exactly one:
`ensure-git: done <login> <email>`
`ensure-git: failed <agent|ssh|gh|prereq>: <reason>`

## never
Print private key. Overwrite key, config, existing origin. Change anything without OK. Install tools. Write .bootstrap.
