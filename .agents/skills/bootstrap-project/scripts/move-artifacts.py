"""Move done project artifact dirs to <artifacts_path>, rewrite status.json paths, mark bootstrap done.

usage: python3 -I move-artifacts.py <project_dir> <artifacts_path> <repo_path> [--late]
Only steps with status `done` move. A step still `running` or `pending` (html-prototype built in
parallel) stays; when it finishes, rerun with --late: moves done dirs still relative, touches
nothing else (no bootstrap step, no state change). Needs artifacts_path already in status.json.
Idempotent: rerun after a partial failure resumes. Per dir:
  src only -> move; dst only -> already moved; both -> collision (exit 3, nothing moved); neither -> skip.
Collisions are checked for every dir before the first move.
Writes go through ../../project/scripts/status.py (file lock), safe next to another thread.
Exit 0 ok, 2 bad input, 3 collision.
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ARTIFACT_STEPS = ["idea", "validation", "spec", "journeys", "wireframes", "html-prototype"]
HELPER = Path(__file__).resolve().parents[2] / "project" / "scripts" / "status.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("pipeline_status", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    args = [a for a in sys.argv[1:] if a != "--late"]
    late = "--late" in sys.argv[1:]
    if len(args) != 3 or not HELPER.is_file():
        print(__doc__, file=sys.stderr)
        return 2
    project_dir, artifacts, repo = (Path(p).expanduser() for p in args)
    artifacts, repo = artifacts.resolve(), repo.resolve()
    helper = load_helper()
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
    if late and not prev:
        print("--late needs artifacts_path in status.json (bootstrap has not reached the move)", file=sys.stderr)
        return 2

    plan = []  # (step id, src, dst)
    for step in status["steps"]:
        sid = step["id"]
        if sid not in ARTIFACT_STEPS or step.get("status") != "done":
            continue
        p = step.get("path")
        name = Path(p).name if p else sid
        src = project_dir / name
        dst = artifacts / name
        if p and Path(p).is_absolute():
            src = None  # already rewritten by an earlier run
        plan.append((sid, src, dst))

    collisions = [str(dst) for _, src, dst in plan if src is not None and src.exists() and dst.exists()]
    if collisions:
        print("collision: " + " ".join(collisions), file=sys.stderr)
        return 3

    artifacts.mkdir(parents=True, exist_ok=True)
    if not late:
        helper.update(project_dir, lambda s: s.update(repo_path=str(repo), artifacts_path=str(artifacts)))

    for sid, src, dst in plan:
        if src is not None and src.exists():
            shutil.move(str(src), str(dst))
            print(f"moved {src.name} -> {dst}")
        if dst.exists():
            def rewrite(s, sid=sid, dst=dst):
                next(x for x in s["steps"] if x["id"] == sid)["path"] = str(dst)
            helper.update(project_dir, rewrite)
        else:
            print(f"warning: {sid} done but {dst} missing", file=sys.stderr)

    if late:
        return 0
    nn = status.get("id", "")

    def finish(s):
        boot = next(x for x in s["steps"] if x["id"] == "bootstrap")
        boot.update(status="done", path=str(repo), result=f"bootstrap-project: done {nn} {repo}")
        return boot["result"]

    print(helper.update(project_dir, finish))
    return 0


if __name__ == "__main__":
    sys.exit(main())
