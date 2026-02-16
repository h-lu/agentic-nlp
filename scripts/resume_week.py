#!/usr/bin/env python3
"""Show the completion status of a week package — useful for resuming after interruption.

Usage:
    python3 scripts/resume_week.py --week week_01
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

from _common import normalize_week, repo_root


# ---------------------------------------------------------------------------
# Status checks
# ---------------------------------------------------------------------------

def _file_status(path: Path) -> str:
    """Return a human-readable status for a single file."""
    if not path.exists():
        return "MISSING"
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return "EMPTY"

    # Check if it's still a template (mostly TODOs / placeholders)
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return "EMPTY"

    todo_count = sum(1 for l in lines if "TODO" in l or "（TODO）" in l)
    if todo_count > 0:
        ratio = todo_count / len(lines)
        if ratio > 0.5:
            return f"SKELETON ({todo_count} TODOs in {len(lines)} lines)"
        elif ratio > 0.2:
            return f"DRAFT ({todo_count} TODOs remaining)"

    # Check for default solution
    if path.name == "solution.py":
        if "# Default: identity transform" in text and "return text" in text:
            return "DEFAULT (not customised)"

    return f"OK ({len(lines)} lines)"


def _check_examples(examples_dir: Path) -> str:
    if not examples_dir.is_dir():
        return "MISSING dir"
    py_files = sorted(f.name for f in examples_dir.iterdir() if f.suffix == ".py")
    if not py_files:
        return "EMPTY (no .py files)"
    return f"OK ({len(py_files)} files: {', '.join(py_files)})"


def _check_tests(tests_dir: Path) -> str:
    if not tests_dir.is_dir():
        return "MISSING dir"
    test_files = sorted(f.name for f in tests_dir.iterdir() if f.name.startswith("test_") and f.suffix == ".py")
    if not test_files:
        return "NO test_*.py files"
    return f"OK ({len(test_files)} files: {', '.join(test_files)})"


def _run_validate(root: Path, week: str) -> tuple[bool, str]:
    """Run validate_week in task mode and return (passed, summary)."""
    cmd = [sys.executable, str(root / "scripts" / "validate_week.py"), "--week", week, "--mode", "task"]
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    if proc.returncode == 0:
        return True, "PASS"
    # Extract error count
    stderr = proc.stderr.strip()
    error_lines = [l for l in stderr.splitlines() if l.startswith("- ")]
    return False, f"FAIL ({len(error_lines)} issues)"


def _run_pytest(root: Path, week: str) -> tuple[bool, str]:
    """Run pytest and return (passed, summary)."""
    tests_dir = root / "chapters" / week / "tests"
    if not tests_dir.is_dir():
        return False, "NO tests dir"
    cmd = [sys.executable, "-m", "pytest", str(tests_dir), "-q", "--tb=no"]
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    if proc.returncode == 0:
        # Extract "N passed" from output
        m = re.search(r"(\d+) passed", proc.stdout)
        count = m.group(1) if m else "?"
        return True, f"PASS ({count} tests)"
    m = re.search(r"(\d+) failed", proc.stdout)
    failed = m.group(1) if m else "?"
    return False, f"FAIL ({failed} failed)"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Show week completion status for resuming work.")
    parser.add_argument("--week", required=True, help="Week id (e.g. week_01 or 01)")
    args = parser.parse_args()

    root = repo_root()
    try:
        week = normalize_week(args.week)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    week_dir = root / "chapters" / week
    if not week_dir.is_dir():
        print(f"[resume] {week} directory does not exist. Run: make new W={week.split('_')[1]}")
        return 0

    print(f"[resume] Status report for {week}")
    print("=" * 60)

    # File-by-file status
    files = {
        "CHAPTER.md": week_dir / "CHAPTER.md",
        "ASSIGNMENT.md": week_dir / "ASSIGNMENT.md",
        "RUBRIC.md": week_dir / "RUBRIC.md",
        "QA_REPORT.md": week_dir / "QA_REPORT.md",
        "ANCHORS.yml": week_dir / "ANCHORS.yml",
        "TERMS.yml": week_dir / "TERMS.yml",
        "solution.py": week_dir / "starter_code" / "solution.py",
    }

    print("\nFiles:")
    todos: list[str] = []
    for name, path in files.items():
        status = _file_status(path)
        marker = "  " if status.startswith("OK") else ">>"
        print(f"  {marker} {name:20s} {status}")
        if not status.startswith("OK"):
            todos.append(f"Complete {name} ({status})")

    print(f"\nExamples: {_check_examples(week_dir / 'examples')}")
    print(f"Tests:    {_check_tests(week_dir / 'tests')}")

    ex_status = _check_examples(week_dir / "examples")
    if not ex_status.startswith("OK"):
        todos.append(f"Add example .py files ({ex_status})")

    # Validation
    print("\nValidation:")
    v_ok, v_summary = _run_validate(root, week)
    print(f"  validate_week (task): {v_summary}")
    if not v_ok:
        todos.append("Fix validate_week errors")

    p_ok, p_summary = _run_pytest(root, week)
    print(f"  pytest:               {p_summary}")
    if not p_ok:
        todos.append("Fix pytest failures")

    # TODO list
    if todos:
        print(f"\nRemaining work ({len(todos)} items):")
        for i, t in enumerate(todos, 1):
            print(f"  {i}. {t}")
    else:
        print("\nAll checks passed! Ready for: make release W=" + week.split("_")[1])

    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
