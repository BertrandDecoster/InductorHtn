"""`check`: one command that tells an author what is wrong with a .htn file.

    python -m htn_components check <file.htn> [--goal "task(args)."] [--plans N] [--fast]

1. Compiles the file with the C++ engine, after its manifest's dependencies (so a
   component or level compiles in context). A compile error is reported at the
   file's real line and column.
2. Lints it (gui/backend/htn_linter.py) with the dependencies' signatures known.
3. With --goal, runs FindAllPlans and prints the plan count and the first plans.

Output is one diagnostic per line, `path:line:col: severity CODE message`. The exit
status is 1 if there is any error. --fast skips planning (the PostToolUse hook uses it).
"""

import json
import os
import re
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PY_DIR = os.path.join(PROJECT_ROOT, "src", "Python")


def _dependency_sources(path):
    """Sources of the manifest's dependencies, in load order ([] outside components/levels)."""
    manifest = os.path.join(os.path.dirname(os.path.abspath(path)), "manifest.json")
    if not os.path.exists(manifest):
        return [], None
    sys.path.insert(0, PY_DIR)
    from htn_components.loader import ComponentLoader
    from htn_components.manifest import Manifest
    deps = Manifest.load(manifest).dependencies
    loader = ComponentLoader(None, PROJECT_ROOT)
    return [text for _, text in loader.resolve_sources(deps)], os.path.dirname(os.path.abspath(path))


def _engine(dep_sources, source, goal, max_plans):
    """Compile (and plan) in a child process: the engine can abort on bad input."""
    payload = json.dumps({"deps": dep_sources, "source": source, "goal": goal, "max": max_plans})
    try:
        proc = subprocess.run([sys.executable, __file__, "--child"], input=payload, text=True,
                              capture_output=True, timeout=120, cwd=PY_DIR, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return {"error": "the engine timed out (runaway recursion, or a plan explosion?)"}
    if proc.returncode != 0:
        return {"error": "the engine crashed: " + (proc.stderr or proc.stdout).strip()[-300:]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _child():
    args = json.loads(sys.stdin.read())
    sys.path.insert(0, PY_DIR)
    from indhtnpy import HtnPlanner, findAllPlansResultToPrologStringList
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    for dep in args["deps"]:
        err = planner.HtnCompileCustomVariables(dep)
        if err:
            print(json.dumps({"dep_error": err}))
            return
    err = planner.HtnCompileCustomVariables(args["source"])
    if err:
        print(json.dumps({"compile_error": err}))
        return
    out = {}
    if args["goal"]:
        err, result = planner.FindAllPlansCustomVariables(args["goal"])
        if err:
            out["plan_error"] = err
        else:
            data = json.loads(result)
            if not data or (isinstance(data[0], dict) and "false" in data[0]):
                out["plans"] = []
            else:
                out["plans"] = findAllPlansResultToPrologStringList(result)
    print(json.dumps(out))


def _locate_compile_error(source, msg):
    """The engine reports every error on line 1, but its message ends with the text it
    parsed up to the error ("Line: ..."). Find that text in the source to get the real
    line and column."""
    text = msg.split(" -- file:")[0]
    head = text.split("Prev:")[0]
    reason = " ".join(re.sub(r"Line \d+, Column \d+:", "", head).split())
    parsed = text.split("Line:", 1)[1] if "Line:" in text else ""
    tail = " ".join(parsed.split())[-40:]
    norm, where = [], []
    line, col, prev_space = 1, 1, False
    for ch in source:
        if ch.isspace():
            if not prev_space:
                norm.append(" ")
                where.append((line, col))
            prev_space = True
        else:
            norm.append(ch)
            where.append((line, col))
            prev_space = False
        if ch == "\n":
            line, col = line + 1, 1
        else:
            col += 1
    idx = "".join(norm).rfind(tail) if tail else -1
    if idx < 0:
        return 1, 1, reason
    ln, cl = where[min(idx + len(tail), len(where) - 1)]
    return ln, cl, reason


def _lint(path, source, component_dir):
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "gui", "backend"))
    from htn_linter import HtnLinter
    external = set()
    if component_dir:
        from htn_components.cli import _collect_external_signatures
        external = _collect_external_signatures(component_dir)
    return HtnLinter(source, external_signatures=external).lint()


def run_check(path, goal=None, max_plans=5, fast=False, out=print):
    """Print diagnostics for `path`; return the number of errors."""
    rel = os.path.relpath(path, PROJECT_ROOT) if os.path.isabs(path) else path
    source = open(path, encoding="utf-8").read()
    errors = 0
    try:
        deps, component_dir = _dependency_sources(path)
    except Exception as exc:  # a broken manifest is itself worth reporting
        out(f"{rel}:1:1: error MAN001 cannot load the manifest's dependencies: {exc}")
        return 1

    result = _engine(deps, source, None if fast else goal, max_plans)
    if "dep_error" in result:
        out(f"{rel}:1:1: error DEP001 a dependency does not compile: {result['dep_error']}")
        errors += 1
    elif "compile_error" in result:
        line, col, text = _locate_compile_error(source, result["compile_error"])
        out(f"{rel}:{line}:{col}: error CMP001 does not compile: {text}")
        errors += 1
    elif "error" in result:
        out(f"{rel}:1:1: error ENG001 {result['error']}")
        errors += 1

    for d in _lint(path, source, component_dir):
        sev = getattr(d, "severity", "warning")
        if sev == "error":
            errors += 1
        out(f"{rel}:{d.line}:{d.col}: {sev} {d.code} {d.message}")

    if goal and not fast and "plans" in result or "plan_error" in result:
        if "plan_error" in result:
            out(f"{rel}:1:1: error PLN001 planning {goal} failed: {result['plan_error']} "
                "(an operator deleted a fact that isn't there or added one that is: guard it in the "
                "calling method's if())")
            errors += 1
        else:
            plans = result["plans"]
            out(f"{goal} -> {len(plans)} plan(s)")
            for i, p in enumerate(plans[:max_plans]):
                out(f"  {i + 1}. {p if p else '(empty plan)'}")
            if not plans:
                out("  no plan: find the method that fails with the MCP tool indhtn_method_failures, "
                    "or query each subtask on its own, bottom-up")
    return errors


def cmd_check(args):
    errors = 0
    for path in args.files:
        errors += run_check(path, goal=args.goal, max_plans=args.plans, fast=args.fast)
    return 1 if errors else 0


if __name__ == "__main__" and sys.argv[1:] == ["--child"]:
    _child()
