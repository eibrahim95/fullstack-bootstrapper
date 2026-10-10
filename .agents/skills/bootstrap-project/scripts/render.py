"""Copy a stack's files/ tree into the repo, filling placeholders.

usage: python3 -I render.py <files_dir> <repo_dir> <slug> <title> <one_liner>
Placeholders: __SLUG__ __TITLE__ __ONE_LINER__. A file named `_gitignore` becomes `.gitignore`.
Overwrites files of the same path (run after uv init / startproject, which it replaces).
"""
import shutil
import sys
from pathlib import Path


def main():
    files_dir, repo, slug, title, one_liner = sys.argv[1:6]
    files_dir, repo = Path(files_dir), Path(repo)
    subs = {"__SLUG__": slug, "__TITLE__": title, "__ONE_LINER__": one_liner}
    for src in sorted(files_dir.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(files_dir)
        if rel.name == "_gitignore":
            rel = rel.with_name(".gitignore")
        dst = repo / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = src.read_text()
        except UnicodeDecodeError:
            shutil.copyfile(src, dst)
            continue
        for k, v in subs.items():
            text = text.replace(k, v)
        dst.write_text(text)
        print(rel)


if __name__ == "__main__":
    main()
