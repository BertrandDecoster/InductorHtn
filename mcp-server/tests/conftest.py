"""Shared pytest setup for the MCP server test suite.

The MCP server now runs the bindings in-process; there is no subprocess to
manage and no need for a Windows-specific event-loop policy. Each test
creates its own ``IndHTNMCPServer`` instance directly.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_MCP_SERVER = _HERE.parents[1]
_REPO = _MCP_SERVER.parent

# Ensure the MCP package and the C++ bindings wrapper are importable.
sys.path.insert(0, str(_MCP_SERVER))
sys.path.insert(0, str(_REPO / "src" / "Python"))


@pytest.fixture(scope="session")
def project_root() -> Path:
    return _REPO


@pytest.fixture(scope="session")
def examples_dir(project_root: Path) -> Path:
    return project_root / "Examples"


pytest_plugins = ("pytest_asyncio",)
