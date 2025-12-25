"""
HTN Components - Reusable component library for InductorHTN

This package provides tools for creating, testing, and certifying
HTN ruleset components.

Usage:
    python -m htn_components new primitives/tags
    python -m htn_components test primitives/tags
    python -m htn_components certify primitives/tags
    python -m htn_components status
    python -m htn_components assemble levels/puzzle1
"""

__version__ = "0.1.0"

from .manifest import Manifest, ManifestValidationError
from .cli import main

__all__ = ["Manifest", "ManifestValidationError", "main"]
