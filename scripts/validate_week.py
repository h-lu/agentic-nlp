#!/usr/bin/env python3
"""Validate a single week package against DoD gates.

Modes (from most lenient to most strict):
    drafting  — CHAPTER.md content + TERMS.yml format (for writer/polisher stage)
    idle      — all files + QA blocking check, no pytest (for production/QA stage)
    release   — strictest: all files + pytest + anchors + pedagogical checks

Usage:
    python3 scripts/validate_week.py --week week_01 --mode release
    python3 scripts/validate_week.py --week 06 --mode drafting --verbose
    python3 scripts/validate_week.py --week 01 --mode idle
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from _common import (
    add_error,
    load_yaml,
    normalize_week,
    repo_root,
    set_verbose,
    verbose,
    week_number,
)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_required_paths(errors: list[str], week_dir: Path, root: Path, mode: str) -> None:
    # drafting: CHAPTER.md only (for writing/polishing stages)
    # idle/release: everything
    if mode == "drafting":
        required_files = [week_dir / "CHAPTER.md"]
        required_dirs: list[Path] = []
    else:
        required_files = [
            week_dir / "CHAPTER.md",
            week_dir / "ASSIGNMENT.md",
            week_dir / "RUBRIC.md",
            week_dir / "QA_REPORT.md",
            week_dir / "ANCHORS.yml",
            week_dir / "TERMS.yml",
            week_dir / "starter_code" / "solution.py",
        ]
        required_dirs = [
            week_dir / "examples",
            week_dir / "tests",
            week_dir / "starter_code",
        ]

    for p in required_files:
        if not p.is_file():
            add_error(errors, f"missing required file: {p.relative_to(root)}")
        else:
            verbose(f"OK file: {p.relative_to(root)}")
    for p in required_dirs:
        if not p.is_dir():
            add_error(errors, f"missing required dir: {p.relative_to(root)}")
        else:
            verbose(f"OK dir:  {p.relative_to(root)}")

    # At least one test file (only for modes that require tests/)
    if mode != "drafting":
        tests_dir = week_dir / "tests"
        if tests_dir.is_dir():
            if not any(t.name.startswith("test_") and t.suffix == ".py" for t in tests_dir.iterdir()):
                add_error(errors, f"tests dir has no test_*.py files: {tests_dir.relative_to(root)}")


def _check_examples_exist(errors: list[str], week_dir: Path, root: Path) -> None:
    """examples/ must contain at least one .py file."""
    examples_dir = week_dir / "examples"
    if not examples_dir.is_dir():
        return  # already caught by _check_required_paths
    py_files = [f for f in examples_dir.iterdir() if f.suffix == ".py"]
    if not py_files:
        add_error(errors, f"examples/ has no .py files: {examples_dir.relative_to(root)}")
    else:
        verbose(f"examples/ has {len(py_files)} .py file(s)")


def _check_chapter_dod(errors: list[str], chapter_path: Path) -> None:
    try:
        text = chapter_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    if "DoD" not in text and "Definition of Done" not in text and "本周 DoD" not in text:
        add_error(errors, f"CHAPTER.md missing DoD section/mention: {chapter_path.name}")


def _check_chapter_content(errors: list[str], chapter_path: Path, mode: str) -> None:
    """Warn/error if CHAPTER.md is still mostly TODO placeholders."""
    try:
        text = chapter_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        add_error(errors, "CHAPTER.md is empty")
        return

    todo_lines = sum(1 for l in lines if "TODO" in l or "（TODO）" in l)
    ratio = todo_lines / len(lines) if lines else 0
    verbose(f"CHAPTER.md: {len(lines)} non-empty lines, {todo_lines} TODO lines ({ratio:.0%})")

    if mode == "release" and ratio > 0.20:
        add_error(errors, f"CHAPTER.md still has {ratio:.0%} TODO lines (release requires <=20%)")
    elif ratio > 0.50:
        add_error(errors, f"CHAPTER.md has {ratio:.0%} TODO lines (>50% — still a skeleton)")


def _check_solution_customized(errors: list[str], solution_path: Path, mode: str) -> None:
    """In release mode, solution.py must not be the default identity transform."""
    if mode != "release":
        return
    try:
        text = solution_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    # The default scaffold has exactly "return text" as the identity transform.
    if "# Default: identity transform" in text and "return text" in text:
        add_error(errors, "starter_code/solution.py is still the default template (not customised for this week)")


def _check_terms(errors: list[str], root: Path, week: str) -> None:
    week_dir = root / "chapters" / week
    terms_path = week_dir / "TERMS.yml"
    glossary_path = root / "shared" / "glossary.yml"

    terms = load_yaml(terms_path)
    if terms in (None, ""):
        terms = []
    if not isinstance(terms, list):
        add_error(errors, f"TERMS.yml must be a list: {terms_path.relative_to(root)}")
        return

    glossary = load_yaml(glossary_path)
    if glossary in (None, ""):
        glossary = []
    if not isinstance(glossary, list):
        add_error(errors, f"shared/glossary.yml must be a list: {glossary_path.relative_to(root)}")
        return

    glossary_terms: set[str] = set()
    for entry in glossary:
        if isinstance(entry, dict) and isinstance(entry.get("term_zh"), str):
            glossary_terms.add(entry["term_zh"])

    for i, entry in enumerate(terms):
        if not isinstance(entry, dict):
            add_error(errors, f"TERMS.yml item #{i+1} must be a mapping/dict")
            continue
        term_zh = entry.get("term_zh")
        definition_zh = entry.get("definition_zh")
        first_seen = entry.get("first_seen")

        if not isinstance(term_zh, str) or not term_zh.strip():
            add_error(errors, f"TERMS.yml item #{i+1} missing non-empty 'term_zh'")
            continue
        if not isinstance(definition_zh, str) or not definition_zh.strip():
            add_error(errors, f"TERMS.yml item #{i+1} ({term_zh}) missing non-empty 'definition_zh'")
        if first_seen != week:
            add_error(errors, f"TERMS.yml item #{i+1} ({term_zh}) first_seen must be {week!r} (got {first_seen!r})")

        if term_zh not in glossary_terms:
            add_error(errors, f"term missing from shared/glossary.yml: {term_zh!r}")


def _maybe_extract_pytest_nodeid(verification: str) -> str | None:
    v = verification.strip()
    if not v:
        return None
    if v.startswith("pytest:"):
        nodeid = v[len("pytest:"):].strip()
        return nodeid if "::" in nodeid and " " not in nodeid else None
    if "::" in v and " " not in v:
        return v
    return None


def _check_anchors(errors: list[str], root: Path, week: str) -> None:
    week_dir = root / "chapters" / week
    anchors_path = week_dir / "ANCHORS.yml"
    anchors = load_yaml(anchors_path)
    if anchors in (None, ""):
        anchors = []
    if not isinstance(anchors, list):
        add_error(errors, f"ANCHORS.yml must be a list: {anchors_path.relative_to(root)}")
        return

    seen_ids: set[str] = set()
    for i, entry in enumerate(anchors):
        if not isinstance(entry, dict):
            add_error(errors, f"ANCHORS.yml item #{i+1} must be a mapping/dict")
            continue

        anchor_id = entry.get("id")
        claim = entry.get("claim")
        evidence = entry.get("evidence")
        verification = entry.get("verification")

        if not isinstance(anchor_id, str) or not anchor_id.strip():
            add_error(errors, f"ANCHORS.yml item #{i+1} missing non-empty 'id'")
        else:
            if anchor_id in seen_ids:
                add_error(errors, f"duplicate anchor id: {anchor_id!r}")
            seen_ids.add(anchor_id)

        if not isinstance(claim, str) or not claim.strip():
            add_error(errors, f"ANCHORS.yml item #{i+1} ({anchor_id}) missing non-empty 'claim'")
        if not isinstance(evidence, str) or not evidence.strip():
            add_error(errors, f"ANCHORS.yml item #{i+1} ({anchor_id}) missing non-empty 'evidence'")
        if not isinstance(verification, str) or not verification.strip():
            add_error(errors, f"ANCHORS.yml item #{i+1} ({anchor_id}) missing non-empty 'verification'")
            continue

        nodeid = _maybe_extract_pytest_nodeid(verification)
        if nodeid:
            file_part = nodeid.split("::", 1)[0]
            p = Path(file_part)
            candidates = []
            if p.is_absolute():
                candidates.append(p)
            else:
                candidates.append(week_dir / file_part)
                candidates.append(root / file_part)
            if not any(c.exists() for c in candidates):
                add_error(
                    errors,
                    f"ANCHORS.yml item #{i+1} ({anchor_id}) verification refers to missing test file: {file_part!r}",
                )


def _check_qa_blocking(errors: list[str], qa_report_path: Path) -> None:
    text = qa_report_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    start = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("## 阻塞项"):
            start = idx + 1
            break
    if start is None:
        add_error(errors, f"QA_REPORT.md missing '## 阻塞项' section: {qa_report_path.name}")
        return

    end = len(lines)
    for idx in range(start, len(lines)):
        if lines[idx].strip().startswith("## ") and idx > start:
            end = idx
            break

    in_comment = False
    for line in lines[start:end]:
        stripped = line.strip()
        if "<!--" in stripped:
            in_comment = True
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if "- [ ]" in line:
            add_error(errors, "QA blocking item not resolved (found unchecked '- [ ]' under '## 阻塞项')")
            break


def _check_textagent_section(errors: list[str], chapter_path: Path, mode: str) -> None:
    """In release mode, CHAPTER.md must contain a TextAgent progress section."""
    if mode != "release":
        return
    try:
        text = chapter_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    # We don't enforce exact heading text, just a strong signal that the
    # cross-week project line is present in the narrative.
    if "TextAgent" not in text and "textagent" not in text.lower():
        add_error(errors, "CHAPTER.md missing TextAgent progress section (required by CLAUDE.md)")
    else:
        verbose("TextAgent mention found in CHAPTER.md")


def _check_characters(errors: list[str], chapter_path: Path, root: Path, mode: str) -> None:
    """In release mode, CHAPTER.md must use at least 2 recurring characters."""
    if mode != "release":
        return
    try:
        text = chapter_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return

    characters_path = root / "shared" / "characters.yml"
    if not characters_path.is_file():
        verbose("shared/characters.yml not found — skipping character check")
        return

    try:
        characters = load_yaml(characters_path)
    except RuntimeError:
        verbose("failed to load characters.yml — skipping character check")
        return

    if not isinstance(characters, list):
        return

    found: list[str] = []
    for entry in characters:
        if isinstance(entry, dict):
            name = entry.get("name", "")
            if isinstance(name, str) and name and name in text:
                found.append(name)

    if len(found) < 2:
        add_error(
            errors,
            f"CHAPTER.md uses only {len(found)} recurring character(s) "
            f"(found: {found or 'none'}; need at least 2 from shared/characters.yml)",
        )
    else:
        verbose(f"recurring characters found: {found}")


def _check_concept_budget(errors: list[str], root: Path, week: str, mode: str) -> None:
    """In release mode, check that new concepts don't exceed the phase budget."""
    if mode != "release":
        return

    concept_map_path = root / "shared" / "concept_map.yml"
    if not concept_map_path.is_file():
        verbose("shared/concept_map.yml not found — skipping concept budget check")
        return

    try:
        concepts = load_yaml(concept_map_path)
    except RuntimeError:
        verbose("failed to load concept_map.yml — skipping concept budget check")
        return

    if not isinstance(concepts, list):
        return

    n = week_number(week)

    # Determine budget from the 16-week course phases (see CLAUDE.md)
    if n <= 4:
        budget = 4
    elif n <= 12:
        budget = 5
    elif n <= 15:
        budget = 4
    else:
        budget = 3

    # Count concepts introduced this week
    week_concepts = [
        c.get("concept_zh", "?")
        for c in concepts
        if isinstance(c, dict) and c.get("introduced") == week
    ]

    if len(week_concepts) > budget:
        add_error(
            errors,
            f"concept budget exceeded: {len(week_concepts)} concepts introduced in {week} "
            f"(budget: {budget}). Concepts: {week_concepts}",
        )
    else:
        verbose(f"concept budget OK: {len(week_concepts)}/{budget} for {week}")


def _check_review_bridges(errors: list[str], chapter_path: Path, root: Path, week: str, mode: str) -> None:
    """In release mode, CHAPTER.md should reference concepts from previous weeks (review bridges)."""
    if mode != "release":
        return

    n = week_number(week)
    if n <= 1:
        verbose("week_01 — review bridge check skipped")
        return

    try:
        text = chapter_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return

    concept_map_path = root / "shared" / "concept_map.yml"
    if not concept_map_path.is_file():
        verbose("shared/concept_map.yml not found — skipping review bridge check")
        return

    try:
        concepts = load_yaml(concept_map_path)
    except RuntimeError:
        verbose("failed to load concept_map.yml — skipping review bridge check")
        return

    if not isinstance(concepts, list):
        return

    # Find concepts from earlier weeks that are supposed to be revisited this week
    bridge_targets = []
    for c in concepts:
        if not isinstance(c, dict):
            continue
        introduced = c.get("introduced", "")
        revisited = c.get("revisited", [])
        if not isinstance(revisited, list):
            continue
        if introduced != week and week in revisited:
            bridge_targets.append(c.get("concept_zh", "?"))

    if not bridge_targets:
        verbose("no review bridge targets found in concept_map.yml for this week")
        return

    # Check how many are mentioned in CHAPTER.md
    found = [t for t in bridge_targets if t in text]
    hit_rate = len(found) / len(bridge_targets) if bridge_targets else 1.0

    # Require at least half of bridge targets to be mentioned
    if hit_rate < 0.5:
        missing = [t for t in bridge_targets if t not in text]
        add_error(
            errors,
            f"review bridges insufficient: only {len(found)}/{len(bridge_targets)} bridge targets "
            f"found in CHAPTER.md (need >=50%). Missing: {missing[:5]}",
        )
    else:
        verbose(f"review bridges OK: {len(found)}/{len(bridge_targets)} targets mentioned")


def _run_pytest(errors: list[str], root: Path, week: str) -> None:
    week_tests = root / "chapters" / week / "tests"
    cmd = [sys.executable, "-m", "pytest", str(week_tests), "-q"]
    verbose(f"running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    if proc.returncode != 0:
        add_error(errors, "pytest failed")
        if proc.stdout:
            add_error(errors, "pytest stdout:\n" + proc.stdout.rstrip())
        if proc.stderr:
            add_error(errors, "pytest stderr:\n" + proc.stderr.rstrip())
    else:
        verbose("pytest passed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a week package against DoD gates.")
    parser.add_argument("--week", required=True, help="Week id (e.g. week_06 or 06)")
    parser.add_argument(
        "--mode", required=True,
        choices=["drafting", "idle", "release"],
        help=(
            "Validation strictness: "
            "drafting (CHAPTER+TERMS for writing stages) | "
            "idle (all files+QA, no pytest for pre-release) | "
            "release (strictest with pytest+pedagogical)"
        ),
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Print details for each check")
    args = parser.parse_args()

    if args.verbose:
        set_verbose(True)

    root = repo_root()
    try:
        week = normalize_week(args.week)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    errors: list[str] = []
    week_dir = root / "chapters" / week
    if not week_dir.is_dir():
        add_error(errors, f"missing week dir: chapters/{week}/ (run scripts/new_week.py first)")
    else:
        verbose(f"validating {week} (mode={args.mode})")

        # --- File existence (mode-aware) ---
        _check_required_paths(errors, week_dir, root, args.mode)

        # --- CHAPTER.md content checks ---
        _check_chapter_dod(errors, week_dir / "CHAPTER.md")
        _check_chapter_content(errors, week_dir / "CHAPTER.md", args.mode)

        # --- Examples (skip for drafting) ---
        if args.mode != "drafting":
            _check_examples_exist(errors, week_dir, root)

        # --- Solution customization (release only) ---
        if args.mode == "release":
            _check_solution_customized(errors, week_dir / "starter_code" / "solution.py", args.mode)

        # --- Pedagogical checks (release only) ---
        _check_textagent_section(errors, week_dir / "CHAPTER.md", args.mode)
        _check_characters(errors, week_dir / "CHAPTER.md", root, args.mode)
        try:
            _check_concept_budget(errors, root, week, args.mode)
            _check_review_bridges(errors, week_dir / "CHAPTER.md", root, week, args.mode)
        except RuntimeError as e:
            add_error(errors, str(e).strip())

        # --- YAML checks (TERMS for all non-drafting; ANCHORS for release only) ---
        if args.mode == "drafting":
            # In drafting mode, check TERMS.yml only if it exists
            try:
                if (week_dir / "TERMS.yml").is_file():
                    _check_terms(errors, root, week)
            except RuntimeError as e:
                add_error(errors, str(e).strip())
        else:
            # idle/release: require TERMS.yml
            try:
                if (week_dir / "TERMS.yml").is_file():
                    _check_terms(errors, root, week)
                else:
                    add_error(errors, f"missing required file: {(week_dir / 'TERMS.yml').relative_to(root)}")
                if args.mode == "release":
                    _check_anchors(errors, root, week)
            except RuntimeError as e:
                add_error(errors, str(e).strip())

        # --- QA blocking (idle/release only) ---
        if args.mode in ("idle", "release"):
            qa_path = week_dir / "QA_REPORT.md"
            if qa_path.is_file():
                _check_qa_blocking(errors, qa_path)

        # --- pytest (release only) ---
        if args.mode == "release":
            _run_pytest(errors, root, week)

    if errors:
        print(f"[validate-week] FAILED (mode={args.mode})", file=sys.stderr)
        print("Problems:", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        return 2

    print(f"[validate-week] OK: {week} (mode={args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
