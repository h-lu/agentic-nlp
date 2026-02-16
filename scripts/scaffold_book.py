#!/usr/bin/env python3
"""Scaffold week_01..week_08 directories and templates from TOC.

Usage:
    python3 scripts/scaffold_book.py
    python3 scripts/scaffold_book.py --start 2 --end 8
    python3 scripts/scaffold_book.py --force
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from _common import read_current_week, repo_root


def _parse_toc_titles(toc_path: Path) -> dict[str, str]:
    titles: dict[str, str] = {}
    # Old format: "- [week_01](week_01/CHAPTER.md) 标题"
    list_re = re.compile(r"^\s*-\s*\[(week_\d{2})\]\(\1/CHAPTER\.md\)\s+(.+?)\s*$")
    # New table format: "| 01 | [标题](week_01/CHAPTER.md) | 描述 |"
    table_re = re.compile(r"^\|\s*(\d{2})\s*\|\s*\[(.+?)\]\(week_\d{2}/CHAPTER\.md\)")
    for line in toc_path.read_text(encoding="utf-8").splitlines():
        m = list_re.match(line)
        if m:
            titles[m.group(1)] = m.group(2).strip()
        else:
            m = table_re.match(line)
            if m:
                titles[f"week_{int(m.group(1)):02d}"] = m.group(2).strip()
    return titles


def _run_new_week(root: Path, week: str, title: str, *, force: bool) -> int:
    cmd = [
        sys.executable,
        str(root / "scripts" / "new_week.py"),
        "--week",
        week,
        "--title",
        title,
    ]
    if force:
        cmd.append("--force")
    proc = subprocess.run(cmd, cwd=root)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold week_01..week_08 directories and templates from TOC.")
    parser.add_argument("--start", type=int, default=1, help="Start week number (default: 1)")
    parser.add_argument("--end", type=int, default=8, help="End week number (default: 8)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing week files (DANGEROUS; default is to keep existing files)",
    )
    args = parser.parse_args()

    if args.start < 1 or args.end < args.start:
        print("error: invalid range (--start/--end)", file=sys.stderr)
        return 2

    root = repo_root()
    toc_path = root / "chapters" / "TOC.md"
    if not toc_path.exists():
        print("error: missing chapters/TOC.md (used as title source of truth)", file=sys.stderr)
        return 2

    titles = _parse_toc_titles(toc_path)
    if not titles:
        print("error: no week titles found in chapters/TOC.md", file=sys.stderr)
        return 2

    current_week_path = root / "chapters" / "current_week.txt"
    original_current_week = read_current_week(root)

    rc = 0
    for n in range(args.start, args.end + 1):
        week = f"week_{n:02d}"
        title = titles.get(week)
        if not title:
            print(f"error: missing title for {week} in chapters/TOC.md", file=sys.stderr)
            rc = 2
            break
        if _run_new_week(root, week, title, force=args.force) != 0:
            rc = 2
            break

    # Restore current_week so scaffolding doesn't disrupt your writing session.
    # If there was no current_week before scaffolding, remove the file we created.
    if original_current_week:
        current_week_path.write_text(original_current_week + "\n", encoding="utf-8")
    else:
        if current_week_path.exists():
            current_week_path.unlink()

    if rc == 0:
        print(f"[scaffold-book] OK: weeks {args.start:02d}..{args.end:02d}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
