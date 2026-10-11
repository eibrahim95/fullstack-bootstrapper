"""Locked, atomic update of a project's status.json. Safe when two threads write at once.

usage:
  python3 -I status.py <project_dir> step <step-id> [status=..] [path=..] [result=..] [thread=..]
  python3 -I status.py <project_dir> set key=value [key=value ...]
Value `null` stores JSON null. Only the named step or keys change. `state` is recomputed
from all steps: state of the last done step in pipeline order. Prints the changed object as JSON.
Exit 0 ok, 2 bad input.
"""
import fcntl
import json
import os
import sys
from pathlib import Path

ORDER = ["idea", "validation", "spec", "journeys", "wireframes", "html-prototype", "bootstrap"]
STATE = {
    "idea": "idea-captured", "validation": "idea-validated", "spec": "spec-created",
    "journeys": "journey-drawn", "wireframes": "wireframes-created",
    "html-prototype": "html-prototype-created", "bootstrap": "project-bootstrapped",
}
STATUSES = {"pending", "running", "done", "failed", "skipped"}


def update(project_dir, mutate):
    """Read fresh under an exclusive lock, apply mutate(status), recompute state, write atomically."""
    project_dir = Path(project_dir)
    path = project_dir / "status.json"
    if not path.is_file():
        raise SystemExit(f"no status.json in {project_dir}")
    with open(project_dir / ".status.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        status = json.loads(path.read_text())
        result = mutate(status)
        done = [s["id"] for s in status["steps"] if s.get("status") == "done"]
        for sid in reversed(ORDER):
            if sid in done:
                status["state"] = STATE[sid]
                break
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    return result


def parse(pairs):
    out = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"bad pair: {pair}")
        k, v = pair.split("=", 1)
        out[k] = None if v == "null" else v
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    project_dir, mode = argv[0], argv[1]
    if mode == "step":
        sid, pairs = argv[2], parse(argv[3:])
        if sid not in ORDER:
            print(f"unknown step {sid}", file=sys.stderr)
            return 2
        if pairs.get("status") not in (None, *STATUSES):
            print(f"bad status {pairs['status']}", file=sys.stderr)
            return 2
        bad = set(pairs) - {"status", "path", "result", "thread"}
        if bad:
            print(f"bad keys {sorted(bad)}", file=sys.stderr)
            return 2

        def mutate(status):
            step = next(s for s in status["steps"] if s["id"] == sid)
            for k, v in pairs.items():
                if k == "thread" and v is None:
                    step.pop("thread", None)
                else:
                    step[k] = v
            return step
    elif mode == "set":
        pairs = parse(argv[2:])
        if set(pairs) & {"steps", "state", "id", "flow"}:
            print("refusing to set steps, state, id, flow", file=sys.stderr)
            return 2

        def mutate(status):
            status.update(pairs)
            return pairs
    else:
        print(__doc__, file=sys.stderr)
        return 2
    print(json.dumps(update(project_dir, mutate), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
