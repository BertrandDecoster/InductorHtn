"""Run the ```htn code blocks of a Markdown file against the engine.

A block is a ruleset followed by one or more checks, written as comments:

    % ?- goal.                 FindAllPlans on the goal; the lines below are the plans, in order
    % => walk(home, park)      one line per plan, operators as the engine prints them
    % => (empty plan)          the plan with no operators
    % => no plan               FindAllPlans finds nothing
    % => compile error         the ruleset does not compile (optionally ": <substring>")
    % => crash                 the engine aborts

    % ?: query.                a Prolog query on the compiled ruleset
    % => ?x = 1                one line per solution, bindings as the engine prints them
    % => false                 no solution

Every check runs on a fresh planner, in a child process (the engine aborts on some
inputs). Blocks fenced as ```prolog or ```text are illustrations and are not run.

    python scripts/htn_doctest.py docs/reference/language.md [-v]
"""

import json
import os
import re
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PY_DIR = os.path.join(REPO, "src", "Python")


def parse_blocks(text):
    """Yield (line_no, program, checks); checks = [(kind, goal, expected_lines, line_no)]."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "```htn":
            start = i + 1
            j = start
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            body = lines[start:j]
            program, checks, current = [], [], None
            for k, line in enumerate(body):
                s = line.strip()
                m = re.match(r"%\s*\?([-:])\s*(.+)$", s)
                if m:
                    current = ("plan" if m.group(1) == "-" else "query", m.group(2), [], start + k + 1)
                    checks.append(current)
                elif s.startswith("% =>") and current is not None:
                    current[2].append(s[4:].strip())
                else:
                    program.append(line)
            yield start, "\n".join(program) + "\n", checks
            i = j
        i += 1


def run_child(program, kind, goal):
    payload = json.dumps({"program": program, "kind": kind, "goal": goal})
    try:
        proc = subprocess.run([sys.executable, __file__, "--child"], input=payload, text=True,
                              capture_output=True, timeout=60, cwd=PY_DIR)
    except subprocess.TimeoutExpired:
        return {"outcome": ["timeout"]}
    if proc.returncode != 0:
        return {"outcome": ["crash"], "detail": (proc.stderr or proc.stdout)[-300:]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def child(program, kind, goal):
    sys.path.insert(0, PY_DIR)
    from indhtnpy import HtnPlanner, findAllPlansResultToPrologStringList, queryResultToPrologStringList
    planner = HtnPlanner(False)
    error = planner.HtnCompileCustomVariables(program)
    if error:
        return {"outcome": ["compile error"], "detail": error}
    if kind == "plan":
        error, result = planner.FindAllPlansCustomVariables(goal)
        if error:
            return {"outcome": ["error"], "detail": error}
        data = json.loads(result)
        if not data or (isinstance(data[0], dict) and "false" in data[0]):
            return {"outcome": ["no plan"]}
        return {"outcome": [p if p else "(empty plan)" for p in findAllPlansResultToPrologStringList(result)]}
    error, result = planner.PrologQuery(goal)
    if error:
        return {"outcome": ["error"], "detail": error}
    data = json.loads(result)
    if data and "false" in data[0]:
        return {"outcome": ["false"]}
    return {"outcome": [s if s else "true" for s in queryResultToPrologStringList(result)]}


def matches(expected, got):
    if len(expected) == 1 and expected[0].startswith("compile error"):
        want = expected[0].partition(":")[2].strip()
        return got["outcome"] == ["compile error"] and want in got.get("detail", "")
    return expected == got["outcome"]


def check_file(path, verbose=False):
    text = open(path, encoding="utf-8").read()
    failures, count = [], 0
    for start, program, checks in parse_blocks(text):
        if not checks:
            failures.append(f"{path}:{start}: htn block has no check (add '% ?- goal.' and '% =>')")
        for kind, goal, expected, line in checks:
            count += 1
            got = run_child(program, kind, goal)
            if not matches(expected, got):
                failures.append(f"{path}:{line}: {goal}\n    expected: {expected}\n    got:      "
                                f"{got['outcome']}" + (f"\n    detail:   {got['detail'].strip()}"
                                                           if got.get("detail") else ""))
            elif verbose:
                print(f"ok  {path}:{line}: {goal}")
    return count, failures


def main():
    if sys.argv[1:] == ["--child"]:
        args = json.loads(sys.stdin.read())
        print(json.dumps(child(args["program"], args["kind"], args["goal"])))
        return 0
    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    total, failures = 0, []
    for path in paths:
        n, f = check_file(path, verbose="-v" in sys.argv)
        total += n
        failures += f
    for f in failures:
        print("FAIL " + f)
    print(f"{total - len(failures)}/{total} checks pass")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
