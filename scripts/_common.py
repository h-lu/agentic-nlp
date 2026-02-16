"""Shared utilities for all scripts and hooks in the textbook factory.

Every script/hook should ``from _common import ...`` (or
``sys.path.insert(0, ...); from _common import ...`` for hooks) instead
of duplicating these helpers.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def repo_root() -> Path:
    """Return the repository root (parent of ``scripts/``)."""
    return Path(__file__).resolve().parents[1]


def python_for_repo(root: Path | None = None) -> str:
    """Return the best Python interpreter for running project scripts.

    Prefers the repo-local ``.venv`` so that hooks/scripts work without
    requiring ``pyyaml`` or ``pytest`` in the global site-packages.

    If no venv is found a warning is printed to stderr once.
    """
    if root is None:
        root = repo_root()
    for p in [
        root / ".venv" / "bin" / "python",
        root / ".venv" / "bin" / "python3",
    ]:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)

    print(
        "[_common] WARNING: repo .venv not found. Using system Python.\n"
        "  Recommended: run  bash scripts/setup_env.sh  to create it.",
        file=sys.stderr,
    )
    return sys.executable


# ---------------------------------------------------------------------------
# Week normalisation
# ---------------------------------------------------------------------------

def normalize_week(week_raw: str) -> str:
    """Normalise a week identifier to the canonical ``week_XX`` form.

    Accepts ``01``, ``1``, ``week_01``, ``week_1``, etc.

    Raises ``ValueError`` for invalid input.
    """
    m = re.search(r"(\d{1,2})", week_raw)
    if not m:
        raise ValueError(
            f"invalid week identifier: {week_raw!r} "
            "(expected 1–2 digits, e.g. '06' or 'week_06')"
        )
    n = int(m.group(1))
    if n < 1 or n > 99:
        raise ValueError(f"week number out of range: {n} (expected 1..99)")
    return f"week_{n:02d}"


def week_number(week: str) -> int:
    """Extract the integer week number from a normalised ``week_XX`` string."""
    return int(week.split("_", 1)[1])


def read_current_week(root: Path | None = None) -> str | None:
    """Read ``chapters/current_week.txt`` and return the normalised week id, or *None*."""
    if root is None:
        root = repo_root()
    p = root / "chapters" / "current_week.txt"
    try:
        s = p.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    if not s:
        return None
    if not re.fullmatch(r"week_\d{2}", s):
        return None
    return s


# ---------------------------------------------------------------------------
# YAML helpers
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> Any:
    """Load a YAML file, raising ``RuntimeError`` with a helpful message on failure."""
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        raise RuntimeError(
            "missing dependency: pyyaml. Install with:\n"
            "  python3 -m pip install -r requirements-dev.txt\n"
            "  (or: bash scripts/setup_env.sh)"
        )
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RuntimeError(f"missing required file: {path}")
    try:
        return yaml.safe_load(raw)
    except Exception as e:  # pragma: no cover – PyYAML exception types vary
        raise RuntimeError(f"failed to parse YAML ({path}): {e}")


def dump_yaml(data: Any) -> str:
    """Dump data to a YAML string (unicode-safe, preserves key order)."""
    import yaml  # type: ignore

    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


# ---------------------------------------------------------------------------
# Verbose / error formatting helpers
# ---------------------------------------------------------------------------

_VERBOSE = False


def set_verbose(v: bool) -> None:
    global _VERBOSE
    _VERBOSE = v


def is_verbose() -> bool:
    return _VERBOSE


def verbose(msg: str) -> None:
    """Print *msg* to stderr only when verbose mode is enabled."""
    if _VERBOSE:
        print(f"  [verbose] {msg}", file=sys.stderr)


def add_error(errors: list[str], msg: str) -> None:
    """Append a formatted error line."""
    errors.append(f"- {msg}")


def add_warning(warnings: list[str], msg: str) -> None:
    """Append a formatted warning line."""
    warnings.append(f"- {msg}")
