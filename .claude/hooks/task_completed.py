#!/usr/bin/env python3
"""Hook: TaskCompleted — validate the current week when a task is marked done.

Key design: different pipeline stages use different validation modes.
Planning-stage tasks (syllabus-planner) only need CHAPTER.md to exist;
writing-stage tasks need CHAPTER + TERMS; production-stage tasks need everything.
This prevents early-stage agents from being blocked by missing downstream files.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# hooks live at .claude/hooks/ — add scripts/ to path for _common.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from _common import python_for_repo, read_current_week  # noqa: E402

# ---------------------------------------------------------------------------
# Stage detection from task subject
# ---------------------------------------------------------------------------

# Keywords that indicate a writing/polishing stage (CHAPTER.md only)
# NOTE: "write" alone is too generic (matches "Write assignment") — use specific terms.
_DRAFTING_KW = [
    "draft", "chapter", "polish", "prose", "rewrite",
    "规划", "大纲", "结构", "写正文", "正文", "润色", "改写", "深度",
    "syllabus-planner", "chapter-writer", "prose-polisher",
]

# Keywords that indicate a production/QA stage (all files needed, no pytest)
_IDLE_KW = [
    "assignment", "exercise", "example", "test", "exercise-factory",
    "example-engineer", "test-designer",
    "作业", "练习", "示例", "测试", "qa", "student-qa", "review", "审读", "评分", "四维",
]


def _detect_validation_mode(task_subject: str) -> str:
    """Determine the appropriate validate_week mode from the task subject.

    Returns one of: drafting, idle.
    - drafting: early stages (planning, writing, polishing) - only CHAPTER.md
    - idle: production stages (examples, tests, assignments, QA) - all files, no pytest
    """
    lower = task_subject.lower()
    if any(kw in lower for kw in _DRAFTING_KW):
        return "drafting"
    if any(kw in lower for kw in _IDLE_KW):
        return "idle"
    return "idle"  # Default to idle for unknown tasks


def _parse_week_from_task_subject(task_subject: str | None) -> str | None:
    if not task_subject:
        return None
    m = re.search(r"\[\s*week_(\d{1,2})\s*\]", task_subject, flags=re.IGNORECASE)
    if not m:
        return None
    return f"week_{int(m.group(1)):02d}"


def main() -> int:
    root = _REPO_ROOT
    strict = os.environ.get("TEXTBOOK_HOOK_STRICT", "").strip().lower() in {
        "1", "true", "yes", "on",
    }
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"[TaskCompleted hook] invalid JSON on stdin: {e}", file=sys.stderr)
        return 2 if strict else 0

    task_subject = payload.get("task_subject", "")

    week = _parse_week_from_task_subject(task_subject)
    if not week:
        week = read_current_week(root)
    if not week:
        print(
            "[TaskCompleted hook] cannot determine target week. "
            "Use task subject prefix like '[week_XX] ...' or set chapters/current_week.txt.",
            file=sys.stderr,
        )
        return 0  # Don't block if we can't even determine the week.

    mode = _detect_validation_mode(task_subject)

    python = python_for_repo(root)
    cmd = [python, str(root / "scripts" / "validate_week.py"), "--week", week, "--mode", mode]
    print(f"[TaskCompleted hook] stage={mode!r} (subject: {task_subject!r})", file=sys.stderr)
    print(f"[TaskCompleted hook] running: {' '.join(cmd)}", file=sys.stderr)
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)

    if proc.returncode != 0:
        print("─" * 60, file=sys.stderr)
        if proc.stdout:
            print(proc.stdout.rstrip(), file=sys.stderr)
        if proc.stderr:
            print(proc.stderr.rstrip(), file=sys.stderr)
        print("─" * 60, file=sys.stderr)
        print(f"[TaskCompleted hook] validation FAILED for {week} (mode={mode}).", file=sys.stderr)
    else:
        print(f"[TaskCompleted hook] validation OK for {week} (mode={mode}).", file=sys.stderr)

    # Decision: should we block?
    # - drafting stage: NEVER block (issues are expected at this stage)
    # - idle stage: block only if strict mode is enabled
    if mode == "drafting":
        if proc.returncode != 0:
            print(
                f"[TaskCompleted hook] NOTE: issues above are informational for "
                f"'{mode}' stage — not blocking.",
                file=sys.stderr,
            )
        return 0

    if proc.returncode != 0 and not strict:
        print(
            "[TaskCompleted hook] NOTE: non-blocking "
            "(set TEXTBOOK_HOOK_STRICT=1 to block production-stage tasks).",
            file=sys.stderr,
        )
    return 0 if (proc.returncode == 0 or not strict) else 2


if __name__ == "__main__":
    raise SystemExit(main())
