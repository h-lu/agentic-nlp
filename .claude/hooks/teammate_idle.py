#!/usr/bin/env python3
"""Hook: TeammateIdle — informational validation when a teammate goes idle.

This hook NEVER blocks (always returns 0). It runs validation and prints
results to stderr as information only. Blocking idle teammates with
validation errors causes deadlocks during multi-stage pipelines where
files are produced incrementally by different agents.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# hooks live at .claude/hooks/ — add scripts/ to path for _common.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from _common import python_for_repo, read_current_week  # noqa: E402


def main() -> int:
    root = _REPO_ROOT
    try:
        _ = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"[TeammateIdle hook] invalid JSON on stdin: {e}", file=sys.stderr)
        return 0  # Never block

    week = read_current_week(root)
    if not week:
        print(
            "[TeammateIdle hook] cannot determine target week. "
            "Set chapters/current_week.txt (e.g. 'week_01' or 'week_06').",
            file=sys.stderr,
        )
        return 0  # Never block

    python = python_for_repo(root)
    cmd = [python, str(root / "scripts" / "validate_week.py"), "--week", week, "--mode", "idle"]
    print(f"[TeammateIdle hook] running: {' '.join(cmd)}", file=sys.stderr)
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    if proc.returncode != 0:
        print("─" * 60, file=sys.stderr)
        if proc.stdout:
            print(proc.stdout.rstrip(), file=sys.stderr)
        if proc.stderr:
            print(proc.stderr.rstrip(), file=sys.stderr)
        print("─" * 60, file=sys.stderr)
        print(
            f"[TeammateIdle hook] validation issues for {week} (informational only).",
            file=sys.stderr,
        )
    else:
        print(f"[TeammateIdle hook] validation OK for {week}.", file=sys.stderr)

    return 0  # ALWAYS return 0 — never block idle teammates


if __name__ == "__main__":
    raise SystemExit(main())
