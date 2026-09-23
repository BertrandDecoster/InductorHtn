#!/usr/bin/env python3
"""fortress-loadout sweep — thin wrapper over the shared quality harness.

The original bespoke driver (P1-P6 + playLevel cross-check) was generalized
into ``mcp-server/indhtn_quality/`` (2026-07-02); the checks now live in
``indhtn_quality.properties`` and this level's gates in ``quality.json``
next to this file. This wrapper is the living regression baseline: the
matrix, the 69-plan cross-check, and P1-P6 ALL PASS must survive any
harness change.

Run:  source .venv/bin/activate && PYTHONPATH=mcp-server python prototypes/fortress-loadout/sweep.py

Direct harness form (same thing, plus --json/--only options):
    PYTHONPATH=mcp-server python -m indhtn_quality.harness \
        prototypes/fortress-loadout/quality.json
"""

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "mcp-server"))
sys.path.insert(0, str(_REPO / "src" / "Python"))

from indhtn_quality.harness import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main([str(Path(__file__).resolve().parent / "quality.json")]))
