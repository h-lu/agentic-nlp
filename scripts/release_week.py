#!/usr/bin/env python3
"""Release a week package: merge terms, update TOC/Glossary, run gates, generate RELEASE.md.

Usage:
    python3 scripts/release_week.py --week week_01
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from _common import dump_yaml, load_yaml, normalize_week, repo_root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _merge_terms_into_glossary(root: Path, week: str) -> None:
    week_dir = root / "chapters" / week
    terms_path = week_dir / "TERMS.yml"
    glossary_path = root / "shared" / "glossary.yml"

    terms = load_yaml(terms_path) or []
    glossary = load_yaml(glossary_path) or []
    if not isinstance(terms, list) or not isinstance(glossary, list):
        raise RuntimeError("TERMS.yml and shared/glossary.yml must both be YAML lists")

    glossary_terms: set[str] = set()
    for entry in glossary:
        if isinstance(entry, dict) and isinstance(entry.get("term_zh"), str):
            glossary_terms.add(entry["term_zh"])

    changed = False
    for entry in terms:
        if not isinstance(entry, dict):
            continue
        term_zh = entry.get("term_zh")
        if isinstance(term_zh, str) and term_zh.strip() and term_zh not in glossary_terms:
            glossary.append(entry)
            glossary_terms.add(term_zh)
            changed = True

    if changed:
        glossary.sort(key=lambda x: x.get("term_zh", "") if isinstance(x, dict) else "")
        glossary_path.write_text(dump_yaml(glossary), encoding="utf-8")


def _extract_title_from_chapter(chapter_path: Path, fallback: str) -> str:
    try:
        for line in chapter_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[len("# "):].strip() or fallback
    except FileNotFoundError:
        pass
    return fallback


def _update_toc(root: Path, week: str, title: str) -> None:
    toc_path = root / "chapters" / "TOC.md"
    if not toc_path.exists():
        return

    n = int(week.split("_", 1)[1])
    lines = toc_path.read_text(encoding="utf-8").splitlines()
    # Old list format
    old_re = re.compile(rf"^\s*-\s*\[{re.escape(week)}\]\(")
    # New table format: "| 01 | [标题](week_01/CHAPTER.md) | ... |"
    table_re = re.compile(rf"^\|\s*{n:02d}\s*\|.*{re.escape(week)}/CHAPTER\.md")

    out: list[str] = []
    replaced = False
    for line in lines:
        if old_re.match(line):
            out.append(f"- [{week}]({week}/CHAPTER.md) {title}")
            replaced = True
        elif table_re.match(line):
            # Preserve description column
            parts = line.split("|")
            desc = parts[3].strip() if len(parts) > 3 else ""
            out.append(f"| {n:02d} | [{title}]({week}/CHAPTER.md) | {desc} |")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"- [{week}]({week}/CHAPTER.md) {title}")

    toc_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _update_syllabus_title(root: Path, week: str, title: str) -> None:
    syllabus_path = root / "chapters" / "SYLLABUS.md"
    if not syllabus_path.exists():
        return

    n = int(week.split("_", 1)[1])
    # Old format: "1. Week 01：标题"
    old_pat = re.compile(rf"^(\s*\d+\.\s*Week\s+{n:02d}\s*[:：])\s*(.+?)\s*$")
    # New heading format: "### Week 01：标题"
    new_pat = re.compile(rf"^(#{2,4}\s*Week\s+{n:02d}\s*[:：])\s*(.+?)\s*$")
    lines = syllabus_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    changed = False
    for line in lines:
        m = old_pat.match(line)
        if m:
            out.append(f"{m.group(1)} {title}")
            changed = True
        else:
            m = new_pat.match(line)
            if m:
                out.append(f"{m.group(1)} {title}")
                changed = True
            else:
                out.append(line)

    if changed:
        syllabus_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _strip_week_prefix(week: str, title: str) -> str:
    m = re.match(rf"^{re.escape(week)}\s*[:：]\s*(.+)$", title.strip())
    return m.group(1).strip() if m else title.strip()


def _run_validate(root: Path, week: str) -> int:
    cmd = [sys.executable, str(root / "scripts" / "validate_week.py"), "--week", week, "--mode", "release"]
    proc = subprocess.run(cmd, cwd=root)
    return proc.returncode


def _run_validate_book(root: Path) -> int:
    cmd = [
        sys.executable,
        str(root / "scripts" / "validate_book.py"),
        "--mode",
        "fast",
        "--strict",
    ]
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    if proc.returncode != 0:
        print("[release-week] validate-book failed (cross-week consistency gate).", file=sys.stderr)
        if proc.stdout.strip():
            print(proc.stdout.rstrip(), file=sys.stderr)
        if proc.stderr.strip():
            print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Release a week package (generate RELEASE.md, update TOC/Glossary).")
    parser.add_argument("--week", required=True)
    args = parser.parse_args()

    root = repo_root()
    try:
        week = normalize_week(args.week)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    week_dir = root / "chapters" / week
    if not week_dir.is_dir():
        print(f"error: missing week dir: {week_dir}", file=sys.stderr)
        return 2

    try:
        _merge_terms_into_glossary(root, week)
    except (ModuleNotFoundError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    chapter_path = week_dir / "CHAPTER.md"
    title_line = _extract_title_from_chapter(chapter_path, fallback=f"{week}")

    toc_title = _strip_week_prefix(week, title_line)
    _update_toc(root, week, toc_title)
    _update_syllabus_title(root, week, toc_title)

    rc = _run_validate(root, week)
    if rc != 0:
        return 2

    rc = _run_validate_book(root)
    if rc != 0:
        return 2

    release_md = f"""# {week}：Release

日期：{date.today().isoformat()}

## 交付物

- `CHAPTER.md`
- `ASSIGNMENT.md`
- `RUBRIC.md`
- `QA_REPORT.md`
- `examples/`
- `starter_code/solution.py`
- `tests/`
- `ANCHORS.yml` / `TERMS.yml`

## 验证

```bash
python3 scripts/validate_week.py --week {week} --mode release
python3 -m pytest chapters/{week}/tests -q
```

## 备注

- （TODO）简述本周学习目标与作业要点（可从 CHAPTER/ASSIGNMENT 摘要补齐）。

"""

    (week_dir / "RELEASE.md").write_text(release_md, encoding="utf-8")
    print(f"[release-week] generated: chapters/{week}/RELEASE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
