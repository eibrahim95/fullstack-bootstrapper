"""Move project artifact dirs to <artifacts_path>, rewrite status.json, mark bootstrap done.

usage: python3 -I move-artifacts.py <project_dir> <artifacts_path> <repo_path>
Idempotent: rerun after a partial failure resumes. Per dir:
  src only -> move; dst only -> already moved; both -> collision (exit 3, nothing moved); neither -> skip.
Collisions are checked for every dir before the first move.
Exit 0 ok, 2 bad input, 3 collision.
"""
import json
import os
import shutil
import sys
from pathlib import Path

ARTIFACT_STEPS = ["idea", "validation", "spec", "journeys", "wireframes", "html-prototype"]


def save(path, data):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def main():
    project_dir, artifacts, repo = (Path(p).expanduser() for p in sys.argv[1:4])
    artifacts, repo = artifacts.resolve(), repo.resolve()
    status_path = project_dir / "status.json"
    if not status_path.is_file():
        print(f"no status.json in {project_dir}", file=sys.stderr)
        return 2
    status = json.loads(status_path.read_text())
    if not (repo / ".git").is_dir():
        print(f"not a git repo: {repo}", file=sys.stderr)
        return 2
    prev = status.get("artifacts_path")
    if prev and Path(prev) != artifacts:
        print(f"status.json already points artifacts_path at {prev}", file=sys.stderr)
        return 2

    steps = {s["id"]: s for s in status["steps"]}
    plan = []  # (step, src, dst)
    for sid in ARTIFACT_STEPS:
        step = steps.get(sid)
        if step is None:
            continue
        p = step.get("path")
        name = Path(p).name if p else sid
        src = project_dir / name
        dst = artifacts / name
        if p and Path(p).is_absolute():
            src = None  # already rewritten by an earlier run
        plan.append((step, src, dst))

    collisions = [str(dst) for _, src, dst in plan if src is not None and src.exists() and dst.exists()]
    if collisions:
        print("collision: " + " ".join(collisions), file=sys.stderr)
        return 3

    artifacts.mkdir(parents=True, exist_ok=True)
    status["repo_path"] = str(repo)
    status["artifacts_path"] = str(artifacts)
    save(status_path, status)

    for step, src, dst in plan:
        if src is not None and src.exists():
            shutil.move(str(src), str(dst))
            print(f"moved {src.name} -> {dst}")
        if step.get("status") == "done" and step.get("path") and dst.exists():
            step["path"] = str(dst)
            save(status_path, status)
        elif step.get("status") == "done" and not dst.exists():
            print(f"warning: {step['id']} done but {dst} missing", file=sys.stderr)

    nn = status.get("id", "")
    boot = steps["bootstrap"]
    boot.update(status="done", path=str(repo), result=f"bootstrap-project: done {nn} {repo}")
    status["state"] = "project-bootstrapped"
    save(status_path, status)
    print(boot["result"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
