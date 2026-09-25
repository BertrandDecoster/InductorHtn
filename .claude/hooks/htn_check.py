"""PostToolUse hook: check every .htn file Claude writes or edits.

Runs `python -m htn_components check --fast <file>` (C++ compile + lint). Errors
block with exit 2, so Claude sees them and fixes the file. Warnings are passed
back as context without blocking. Anything that is not a .htn file is ignored.
"""

import json
import os
import subprocess
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".."))


def python_exe():
    for candidate in (os.path.join(ROOT, ".venv", "Scripts", "python.exe"),
                      os.path.join(ROOT, ".venv", "bin", "python")):
        if os.path.exists(candidate):
            return candidate
    return sys.executable


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".htn") or not os.path.exists(path):
        return 0
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src", "Python"), PYTHONIOENCODING="utf-8")
    proc = subprocess.run([python_exe(), "-m", "htn_components", "check", "--fast", path],
                          cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
                          timeout=120)
    report = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        print("htn check found errors. Fix them before going on "
              "(docs/reference/language.md explains each trap):\n" + report, file=sys.stderr)
        return 2
    if report:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "htn check warnings for " + os.path.basename(path) + ":\n" + report}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
