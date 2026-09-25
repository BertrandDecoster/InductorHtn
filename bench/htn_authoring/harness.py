"""Plan-set harness for the HTN authoring benchmark.

A task's answer is a domain file (methods, operators, rules; no problem facts).
Each hidden instance is a problem file (facts) plus a goal. The answer passes an
instance when its plan multiset equals the reference domain's on that instance.

Every planner call runs in a child process, because the engine can abort on some
inputs (a duplicate add, `<=`).

    python harness.py plans <domain.htn> <problem.htn> "<goal>."   # print plans as JSON
"""

import json
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_DIR = os.path.join(REPO, "src", "Python")
TIMEOUT = 60


def _plans_in_process(domain_text, problem_text, goal):
    sys.path.insert(0, PY_DIR)
    from indhtnpy import HtnPlanner, findAllPlansResultToPrologStringList

    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    error = planner.HtnCompileCustomVariables(domain_text + "\n" + problem_text + "\n")
    if error:
        return {"error": "compile: " + error}
    error, result = planner.FindAllPlansCustomVariables(goal)
    if error:
        return {"error": "plan: " + error}
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return {"plans": [], "finals": []}
    found = findAllPlansResultToPrologStringList(result)
    finals = []
    for i in range(min(len(found), 20)):
        err, facts = planner.GetSolutionFacts(i)
        finals.append(sorted(json.loads(facts)) if err is None else None)
    return {"plans": found, "finals": finals}


def plans(domain_text, problem_text, goal):
    """Return {"plans": [str, ...]} or {"error": str}. Each plan is one string of
    comma-separated operators, as the engine prints them."""
    payload = json.dumps({"domain": domain_text, "problem": problem_text, "goal": goal})
    try:
        proc = subprocess.run([sys.executable, __file__, "--child"], input=payload, text=True,
                              capture_output=True, timeout=TIMEOUT, cwd=PY_DIR)
    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {TIMEOUT}s"}
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
        return {"error": f"engine crashed (exit {proc.returncode}): " + " | ".join(tail)}
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"error": "no result from engine: " + proc.stdout[-300:]}


def load_task(task_dir):
    with open(os.path.join(task_dir, "hidden", "task.json"), encoding="utf-8") as f:
        return json.load(f)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def same_plan_set(want, got, inst):
    """Default instance check: the plan multisets are equal."""
    if sorted(got["plans"]) == sorted(want["plans"]):
        return True, ""
    missing = [p for p in want["plans"] if p not in got["plans"]]
    extra = [p for p in got["plans"] if p not in want["plans"]]
    return False, (f"{len(got['plans'])} plans, expected {len(want['plans'])}; "
                   f"missing {missing[:2]}; unexpected {extra[:2]}")


def _instance_check(task_dir):
    path = os.path.join(task_dir, "hidden", "check.py")
    if not os.path.exists(path):
        return same_plan_set
    import importlib.util
    spec = importlib.util.spec_from_file_location("task_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check_instance


def check(task_dir, domain_path):
    """Score an answer against the reference on every hidden instance."""
    task = load_task(task_dir)
    check_instance = _instance_check(task_dir)
    reference = read(os.path.join(task_dir, "hidden", "reference.htn"))
    answer = read(domain_path) if os.path.exists(domain_path) else None
    results = []
    for inst in task["instances"]:
        problem = read(os.path.join(task_dir, "hidden", inst["problem"]))
        want = plans(reference, problem, inst["goal"])
        assert "error" not in want, f"reference fails on {inst['problem']}: {want['error']}"
        if answer is None:
            results.append({"instance": inst["problem"], "ok": False, "why": "no domain.htn written"})
            continue
        got = plans(answer, problem, inst["goal"])
        if "error" in got:
            results.append({"instance": inst["problem"], "ok": False, "why": got["error"]})
            continue
        ok, why = check_instance(want, got, inst)
        entry = {"instance": inst["problem"], "goal": inst["goal"], "ok": ok}
        if not ok:
            entry["why"] = why
        results.append(entry)
    passed = sum(r["ok"] for r in results)
    return {"task": os.path.basename(task_dir), "passed": passed, "total": len(results),
            "results": results}


def _main():
    if sys.argv[1:] == ["--child"]:
        args = json.loads(sys.stdin.read())
        print(json.dumps(_plans_in_process(args["domain"], args["problem"], args["goal"])))
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "plans":
        out = plans(read(sys.argv[2]), read(sys.argv[3]), sys.argv[4])
        print(json.dumps(out, indent=1))
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "check":
        print(json.dumps(check(sys.argv[2], sys.argv[3]), indent=1))
        return
    print(__doc__)


if __name__ == "__main__":
    _main()
