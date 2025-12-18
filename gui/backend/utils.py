"""Utility functions for InductorHTN GUI backend"""

import sys
import os

# Add Python directory to path for indhtnpy import
python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/Python'))
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

from indhtnpy import termListToString


def pretty_solution(solution):
    """Convert a solution JSON to human-readable operator sequence.

    Uses termListToString from indhtnpy for proper Prolog formatting.
    """
    return termListToString(solution)
