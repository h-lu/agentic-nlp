#!/usr/bin/env python3
"""Cross-week (book-level) consistency checks.

Usage:
    python3 scripts/validate_book.py --mode fast
    python3 scripts/validate_book.py --mode release --strict --verbose
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from _common import (
    add_error,
    add_warning,
    load_yaml,
    repo_root,
    set_verbose,
    verbose,
)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _norm_title(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _strip_week_prefix(week: str, title: str) -> str:
    """Strip 'Week XX：' prefix from title. The week param is like 'week_01'."""
    t = title.strip()
    # Extract week number from week_01, week_02, etc.
    week_num_match = re.match(r"week_(\d{2})", week)
    if week_num_match:
        week_num = week_num_match.group(1)
        # Match common chapter heading styles:
        # - "Week 01：标题"
        # - "week_01：标题" (project convention)
        # - "week 01: 标题"
        m = re.match(
            rf"^#?\s*week(?:[_\s]+){re.escape(week_num)}\s*[:：]\s*(.+)$",
            t,
            re.IGNORECASE,
        )
        if not m:
            m = re.match(rf"^#?\s*Week\s+{re.escape(week_num)}\s*[:：]\s*(.+)$", t, re.IGNORECASE)
        return _norm_title(m.group(1)) if m else _norm_title(t)
    return _norm_title(t)


def _parse_syllabus(path: Path, errors: list[str]) -> dict[str, str]:
    if not path.exists():
        add_error(errors, f"missing required file: {path}")
        return {}

    weeks: dict[str, str] = {}
    # Support both old format ("1. Week 01：标题") and new heading format ("### Week 01：标题")
    line_re = re.compile(r"^(?:\s*\d+\.\s*|#{2,4}\s*)Week\s+(\d{2})\s*[:：]\s*(.+?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = line_re.match(line)
        if not m:
            continue
        week = f"week_{int(m.group(1)):02d}"
        title = _norm_title(m.group(2))
        if week in weeks:
            add_error(errors, f"SYLLABUS duplicate week title: {week}")
            continue
        weeks[week] = title

    if not weeks:
        add_error(errors, "SYLLABUS.md has no parsable 'Week XX：标题' lines")

    return weeks


def _parse_toc(path: Path, errors: list[str]) -> dict[str, str]:
    if not path.exists():
        add_error(errors, f"missing required file: {path}")
        return {}

    weeks: dict[str, str] = {}
    # Old format: "- [week_01](week_01/CHAPTER.md) 标题"
    list_re = re.compile(r"^\s*-\s*\[(week_\d{2})\]\(\1/CHAPTER\.md\)\s+(.+?)\s*$")
    # New table format: "| 01 | [标题](week_01/CHAPTER.md) | 描述 |"
    table_re = re.compile(r"^\|\s*(\d{2})\s*\|\s*\[(.+?)\]\(week_\d{2}/CHAPTER\.md\)")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = list_re.match(line)
        if m:
            week = m.group(1)
            title = _norm_title(m.group(2))
        else:
            m = table_re.match(line)
            if m:
                week = f"week_{int(m.group(1)):02d}"
                title = _norm_title(m.group(2))
            else:
                continue
        if week in weeks:
            add_error(errors, f"TOC duplicate week entry: {week}")
            continue
        weeks[week] = title

    if not weeks:
        add_error(errors, "TOC.md has no parsable week entries")

    return weeks


def _extract_chapter_heading(chapter_path: Path) -> str | None:
    try:
        for line in chapter_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[len("# "):].strip()
    except FileNotFoundError:
        return None
    return None


# ---------------------------------------------------------------------------
# Validation runners
# ---------------------------------------------------------------------------

def _run_validate_week(root: Path, week: str, mode: str, errors: list[str]) -> None:
    cmd = [sys.executable, str(root / "scripts" / "validate_week.py"), "--week", week, "--mode", mode]
    verbose(f"running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    if proc.returncode != 0:
        add_error(errors, f"validate_week failed for {week} (mode={mode})")
        if proc.stdout.strip():
            add_error(errors, "validate_week stdout:\n" + proc.stdout.rstrip())
        if proc.stderr.strip():
            add_error(errors, "validate_week stderr:\n" + proc.stderr.rstrip())
    else:
        verbose(f"validate_week OK: {week}")


def _check_glossary(root: Path, expected_weeks: set[str], errors: list[str], warnings: list[str]) -> None:
    glossary_path = root / "shared" / "glossary.yml"
    if not glossary_path.exists():
        add_error(errors, f"missing required file: {glossary_path.relative_to(root)}")
        return

    try:
        glossary = load_yaml(glossary_path) or []
    except RuntimeError as e:
        add_error(errors, str(e).strip())
        return

    if not isinstance(glossary, list):
        add_error(errors, f"shared/glossary.yml must be a YAML list: {glossary_path.relative_to(root)}")
        return

    seen: set[str] = set()
    for i, entry in enumerate(glossary):
        if not isinstance(entry, dict):
            add_error(errors, f"shared/glossary.yml item #{i+1} must be a mapping/dict")
            continue
        term_zh = entry.get("term_zh")
        definition_zh = entry.get("definition_zh")
        first_seen = entry.get("first_seen")

        if not isinstance(term_zh, str) or not term_zh.strip():
            add_error(errors, f"shared/glossary.yml item #{i+1} missing non-empty 'term_zh'")
            continue
        if term_zh in seen:
            add_error(errors, f"duplicate term_zh in shared/glossary.yml: {term_zh!r}")
        seen.add(term_zh)

        if not isinstance(definition_zh, str) or not definition_zh.strip():
            add_error(errors, f"shared/glossary.yml item #{i+1} ({term_zh}) missing non-empty 'definition_zh'")

        if not isinstance(first_seen, str) or not first_seen.strip():
            add_error(errors, f"shared/glossary.yml item #{i+1} ({term_zh}) missing non-empty 'first_seen'")
        elif first_seen not in expected_weeks:
            add_warning(
                warnings,
                f"glossary term {term_zh!r} first_seen={first_seen!r} not in SYLLABUS weeks",
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-week (book-level) consistency checks.")
    parser.add_argument("--mode", choices=["fast", "release"], default="fast")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print details for each check")
    args = parser.parse_args()

    if args.verbose:
        set_verbose(True)

    root = repo_root()
    errors: list[str] = []
    warnings: list[str] = []

    syllabus_path = root / "chapters" / "SYLLABUS.md"
    toc_path = root / "chapters" / "TOC.md"

    syllabus_weeks = _parse_syllabus(syllabus_path, errors)
    toc_weeks = _parse_toc(toc_path, errors)

    expected = set(syllabus_weeks.keys())
    toc_set = set(toc_weeks.keys())

    extra_in_toc = sorted(toc_set - expected)
    missing_in_toc = sorted(expected - toc_set)
    if extra_in_toc:
        add_error(errors, f"TOC has weeks not present in SYLLABUS: {', '.join(extra_in_toc)}")
    if missing_in_toc:
        add_error(errors, f"TOC missing weeks present in SYLLABUS: {', '.join(missing_in_toc)}")

    # Titles should match between SYLLABUS and TOC.
    for week in sorted(expected & toc_set):
        a = _norm_title(syllabus_weeks[week])
        b = _norm_title(toc_weeks[week])
        if a != b:
            add_warning(warnings, f"title mismatch for {week}: SYLLABUS={a!r} TOC={b!r}")

    # Existing week dirs: validate individually.
    chapters_dir = root / "chapters"
    existing_weeks = sorted(
        d.name
        for d in chapters_dir.iterdir()
        if d.is_dir() and re.fullmatch(r"week_\d{2}", d.name)
    )

    validate_mode = "idle" if args.mode == "fast" else "release"
    for week in existing_weeks:
        _run_validate_week(root, week, validate_mode, errors)

        chapter_path = root / "chapters" / week / "CHAPTER.md"
        heading = _extract_chapter_heading(chapter_path)
        if heading and week in toc_weeks:
            chapter_title = _strip_week_prefix(week, heading)
            toc_title = _norm_title(toc_weeks[week])

            released = (root / "chapters" / week / "RELEASE.md").is_file()
            if chapter_title != toc_title:
                msg = f"CHAPTER title mismatch for {week}: CHAPTER={chapter_title!r} TOC={toc_title!r}"
                if released:
                    add_error(errors, msg)
                else:
                    add_warning(warnings, msg + " (week not released yet)")

    _check_glossary(root, expected_weeks=expected, errors=errors, warnings=warnings)

    if warnings:
        print("[validate-book] WARNINGS", file=sys.stderr)
        for w in warnings:
            print(w, file=sys.stderr)
        if args.strict:
            errors.extend(warnings)

    if errors:
        print("[validate-book] FAILED", file=sys.stderr)
        print("Problems:", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        return 2

    print("[validate-book] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
