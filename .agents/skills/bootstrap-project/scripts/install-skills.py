"""Copy skill templates into an app repo and link each one for Claude.

usage: python3 -I install-skills.py <repo> <templates>

Every immediate subdirectory of <templates> is one skill. Copies it to
<repo>/.agents/skills/<name>/ and points <repo>/.claude/skills/<name>
at ../../.agents/skills/<name>. One link per skill. Does not link the
parent folder. Does not commit.

A template entry that is not a directory is ignored. A link path that
already exists as a real directory or file is refused (exit 2); a
symlink is repointed only when its target differs.

Exit 0 ok, 2 bad input or a blocked link path.
"""
import shutil
import sys
from pathlib import Path

LINK_TARGET_PREFIX = Path("../../.agents/skills")


def install(repo: Path, templates: Path) -> int:
    if not (repo / ".git").exists():
        print(f"not a git repo: {repo}", file=sys.stderr)
        return 2
    if not templates.is_dir():
        print(f"no template folder: {templates}", file=sys.stderr)
        return 2

    skills = sorted(p for p in templates.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not skills:
        print("no skill directories", file=sys.stderr)
        return 2

    agents = repo / ".agents" / "skills"
    claude = repo / ".claude" / "skills"
    blocked = [
        claude / src.name
        for src in skills
        if (claude / src.name).exists() and not (claude / src.name).is_symlink()
    ]
    if blocked:
        print("refusing to replace non-symlinks: " + " ".join(str(p) for p in blocked), file=sys.stderr)
        return 2
    linked_dest = [agents / src.name for src in skills if (agents / src.name).is_symlink()]
    if linked_dest:
        print("refusing to replace symlinks: " + " ".join(str(p) for p in linked_dest), file=sys.stderr)
        return 2

    agents.mkdir(parents=True, exist_ok=True)
    claude.mkdir(parents=True, exist_ok=True)

    for src in skills:
        dest = agents / src.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        link = claude / src.name
        target = LINK_TARGET_PREFIX / src.name
        if link.is_symlink():
            if link.readlink() != target:
                link.unlink()
                link.symlink_to(target)
        else:
            link.symlink_to(target)
        print(f"installed {src.name}")
    return 0


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    repo, templates = (Path(p).expanduser().resolve() for p in sys.argv[1:])
    return install(repo, templates)


if __name__ == "__main__":
    sys.exit(main())
