"""Pytest configuration for the chapters test suite.

Ensures that the project root is in sys.path so that shared helpers
are importable during tests.
"""
from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure(config):
    """Add project root to sys.path so that shared helpers are importable."""
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
