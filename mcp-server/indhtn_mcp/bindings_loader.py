"""Robust discovery of the indhtnpy shared library and HtnPlanner class.

The Python wrapper in ``src/Python/indhtnpy.py`` already searches a handful of
locations, but its search is rooted at ``os.getcwd()`` which is unpredictable
when the MCP server is launched from ``claude_desktop_config.json``. This
module extends the search:

  1. ``INDHTN_LIB_PATH`` environment variable (full path to the lib).
  2. Path relative to this file: ``<repo>/build`` and ``<repo>/src/Python``
     (works whether the MCP server is installed in-place or as an editable
     wheel under the repo).
  3. ``INDHTN_REPO_ROOT`` env var + ``build/`` and ``src/Python/``.
  4. Falls back to the wrapper's own search (cwd-based).

Once the library is locatable, importing ``HtnPlanner`` from ``indhtnpy`` will
succeed.
"""

from __future__ import annotations

import logging
import os
import platform as _platform
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _candidate_lib_names() -> list[str]:
    system = _platform.system()
    if system == "Windows":
        return ["indhtnpy.dll"]
    if system == "Darwin":
        return ["libindhtnpy.dylib"]
    return ["libindhtnpy.so"]


def _candidate_dirs() -> list[Path]:
    """Directories to search for the shared library."""
    dirs: list[Path] = []

    here = Path(__file__).resolve()
    # mcp-server/indhtn_mcp/bindings_loader.py -> repo = parents[2]
    repo = here.parents[2]
    dirs.append(repo / "build")
    dirs.append(repo / "build" / "Release")
    dirs.append(repo / "build" / "Debug")
    dirs.append(repo / "src" / "Python")

    env_repo = os.environ.get("INDHTN_REPO_ROOT")
    if env_repo:
        env_repo_path = Path(env_repo)
        dirs.append(env_repo_path / "build")
        dirs.append(env_repo_path / "build" / "Release")
        dirs.append(env_repo_path / "build" / "Debug")
        dirs.append(env_repo_path / "src" / "Python")

    return dirs


def _ensure_indhtnpy_importable() -> Path:
    """Make ``import indhtnpy`` work.

    ``indhtnpy.py`` lives in ``src/Python/`` and isn't on the default path
    when this package is run standalone. Locate the repo via this file and
    add ``src/Python`` to ``sys.path``.

    Returns the repo root for convenience.
    """
    here = Path(__file__).resolve()
    repo = here.parents[2]
    src_python = repo / "src" / "Python"
    if src_python.exists():
        path_str = str(src_python)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
    return repo


def _stage_library_into_search_path() -> tuple[Path | None, str | None]:
    """Ensure the shared library is locatable by ``ctypes`` when indhtnpy loads.

    Strategy: find a usable candidate file, then make sure
    ``os.path.dirname(__file__)`` of the indhtnpy module (which is the first
    search location) contains a copy or symlink — failing that, fall back to
    inserting the directory into the platform's library search path env var.

    Returns (lib_path, library_dir) on success, (None, None) if nothing found.
    """
    explicit = os.environ.get("INDHTN_LIB_PATH")
    if explicit and Path(explicit).exists():
        return Path(explicit), str(Path(explicit).parent)

    names = _candidate_lib_names()
    for d in _candidate_dirs():
        for name in names:
            cand = d / name
            if cand.exists():
                return cand, str(d)

    return None, None


def _augment_search_path_env(lib_dir: str) -> None:
    """Add ``lib_dir`` to the platform's library-search environment variable.

    indhtnpy.py uses ``ctypes.util.find_library`` as a fallback when its
    explicit search paths don't hit — find_library consults DYLD/LD_LIBRARY
    on macOS/Linux and PATH on Windows. We extend whichever is right for
    this OS so that fallback succeeds.
    """
    system = _platform.system()
    if system == "Windows":
        keys = ["PATH"]
    elif system == "Darwin":
        keys = ["DYLD_LIBRARY_PATH", "DYLD_FALLBACK_LIBRARY_PATH"]
    else:
        keys = ["LD_LIBRARY_PATH"]

    for key in keys:
        existing = os.environ.get(key, "")
        if lib_dir in existing.split(os.pathsep):
            continue
        os.environ[key] = (
            lib_dir if not existing else f"{lib_dir}{os.pathsep}{existing}"
        )


def load_planner_class():
    """Return the ``HtnPlanner`` class, ready to instantiate.

    Raises ``RuntimeError`` if the library cannot be located or imported.
    """
    _ensure_indhtnpy_importable()

    lib_path, lib_dir = _stage_library_into_search_path()
    if lib_path is None:
        searched = [str(d) for d in _candidate_dirs()]
        raise RuntimeError(
            "Could not find libindhtnpy shared library. Set INDHTN_LIB_PATH "
            "to its full path, or build the project so it appears in one of: "
            + ", ".join(searched)
        )

    # The wrapper's loader first looks in os.path.dirname(__file__) (the
    # indhtnpy.py location). If the library is somewhere else, augment the
    # OS library-search env var so the find_library fallback hits it. Also
    # chdir-style: indhtnpy looks at os.getcwd() / "src/Python" too, which
    # we already cover when running from the repo root, but not when
    # running from elsewhere.
    if lib_dir:
        _augment_search_path_env(lib_dir)
        # As a belt-and-braces fallback, also pre-load the library so any
        # subsequent ctypes.CDLL call by indhtnpy finds an already-mapped
        # image. (ctypes.CDLL is a no-op for an already-loaded library.)
        try:
            import ctypes

            ctypes.CDLL(str(lib_path))
        except OSError as e:
            logger.warning("Preload of %s failed: %s", lib_path, e)

    try:
        from indhtnpy import HtnPlanner  # type: ignore
    except Exception as e:  # pragma: no cover - import-time
        raise RuntimeError(
            f"Found {lib_path} but failed to import indhtnpy: {e}"
        ) from e

    logger.info("Loaded indhtnpy from %s", lib_path)
    return HtnPlanner
