#!/usr/bin/env python3
"""Self-test: render fixtures/sample-inventory.json with fixtures/filled-slots.html, then run the checker.

Usage:
  python3 -B -I selftest.py [--keep DIR]

Prints the checker output and exits with its code. Run after changing a script, the CSS, or a layout.
--keep DIR writes the rendered pages to DIR (to screenshot them) instead of a temp dir.
"""
import argparse, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE.parent / "fixtures"


def run(out):
    inv = FIX / "sample-inventory.json"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.html"):
        old.unlink()
    py = [sys.executable, "-B", "-I"]
    render = subprocess.run(py + [str(HERE / "render_wireframes.py"), "--inventory", str(inv), "--out", str(out),
                                  "--round", "1", "--fills", str(FIX / "filled-slots.html")])
    if render.returncode:
        return render.returncode
    return subprocess.run(py + [str(HERE / "check_wireframes.py"), "--inventory", str(inv), "--dir", str(out)]).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep")
    args = ap.parse_args()
    if args.keep:
        return run(Path(args.keep))
    with tempfile.TemporaryDirectory() as tmp:
        return run(Path(tmp))


if __name__ == "__main__":
    sys.exit(main())
