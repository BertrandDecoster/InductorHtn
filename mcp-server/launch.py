#!/usr/bin/env python
"""Launch the InductorHTN MCP server from any platform.

`.mcp.json` runs this with whatever `python` is on PATH; this script then
re-executes the server with the project's virtual environment interpreter,
`INDHTN_REPO_ROOT` (so the bindings library is found under `build/`), and
`PYTHONPATH` joined with the platform's separator - the things a
hand-written `.mcp.json` gets wrong on Windows.

    python mcp-server/launch.py            # start the server (stdio)
    python mcp-server/launch.py --check    # print what would run and exit
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

VENV_PYTHONS = [
    os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe"),
    os.path.join(PROJECT_ROOT, ".venv", "bin", "python"),
]
PYTHONPATH_ENTRIES = [
    os.path.join(PROJECT_ROOT, "mcp-server"),
    os.path.join(PROJECT_ROOT, "gui", "backend"),
    os.path.join(PROJECT_ROOT, "src", "Python"),
]


def resolve_python() -> str:
    for candidate in VENV_PYTHONS:
        if os.path.exists(candidate):
            return candidate
    return sys.executable


def build_env() -> dict:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    parts = PYTHONPATH_ENTRIES + ([existing] if existing else [])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    env.setdefault("INDHTN_REPO_ROOT", PROJECT_ROOT)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def main() -> int:
    python = resolve_python()
    env = build_env()
    command = [python, "-m", "indhtn_mcp.server"]

    if "--check" in sys.argv[1:]:
        print(f"project : {PROJECT_ROOT}")
        print(f"python  : {python}")
        print(f"PYTHONPATH: {env['PYTHONPATH']}")
        print(f"command : {' '.join(command)}")
        try:
            probe = subprocess.run(
                [python, "-c",
                 "import mcp, htn_metrics; "
                 "from indhtn_mcp.bindings_loader import load_planner_class; "
                 "import indhtn_mcp.server; "
                 "load_planner_class(); "
                 "print('imports ok, mcp', getattr(mcp, '__version__', '?'), '| bindings loaded')"],
                cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"probe   : FAILED ({exc})")
            return 1
        print("probe   : " + (probe.stdout.strip() or probe.stderr.strip()))
        return probe.returncode

    # Replace this process where the platform allows it; otherwise wait.
    if os.name != "nt":
        os.chdir(PROJECT_ROOT)
        os.execve(python, command, env)
    return subprocess.call(command, cwd=PROJECT_ROOT, env=env)


if __name__ == "__main__":
    sys.exit(main())
