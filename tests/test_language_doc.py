"""docs/reference/language.md must agree with the engine: every htn block runs."""

import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_language_spec_examples_match_the_engine():
    proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "htn_doctest.py"),
                           os.path.join(ROOT, "docs", "reference", "language.md")],
                          capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stdout + proc.stderr
