"""Run the HTN authoring benchmark against a commit of this repo.

For each task and run:
  1. check out the commit into a temporary git worktree,
  2. delete bench/ from it, so the hidden references and checks cannot be read,
  3. copy the prebuilt engine DLLs in (they are gitignored),
  4. put the task's brief, sample problem and starter files in <worktree>/task/,
  5. run `claude -p` there, headless,
  6. grade <worktree>/task/domain.htn against the hidden instances.

    python bench/htn_authoring/run.py --label baseline [--commit HEAD] [--runs 2]
                                      [--tasks commute,blocks] [--jobs 4]

Results go to bench/results/<label>/: one JSON per run (score, cost, turns, the
domain it wrote, the model's final message) and summary.md.
"""

import argparse
import concurrent.futures
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TASKS_DIR = os.path.join(HERE, "tasks")
RESULTS_DIR = os.path.join(REPO, "bench", "results")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "bench", "calibration"))
import harness  # noqa: E402
import calibrate  # noqa: E402

PROMPT = ("Read task/brief.md and complete the task it describes. You are in a checkout of the "
          "InductorHTN repository; use its documentation, examples and tools as you see fit. "
          "When you finish, task/domain.htn must hold your final domain.")
ALLOWED_TOOLS = "Bash Read Write Edit Glob Grep Skill Agent mcp__indhtn"
DLLS = [os.path.join("src", "Python", "indhtnpy.dll"), os.path.join("build", "Release", "indhtnpy.dll")]


def git(*args, cwd=REPO):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def prepare(commit, task, workroot):
    wt = os.path.join(workroot, task)
    git("worktree", "add", "--detach", wt, commit)
    shutil.rmtree(os.path.join(wt, "bench"), ignore_errors=True)
    for dll in DLLS:
        src = os.path.join(REPO, dll)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(os.path.join(wt, dll)), exist_ok=True)
            shutil.copy2(src, os.path.join(wt, dll))
    tdir = os.path.join(TASKS_DIR, task)
    out = os.path.join(wt, "task")
    os.makedirs(out)
    for name in ("brief.md", "problem.htn"):
        shutil.copy2(os.path.join(tdir, name), out)
    starter = os.path.join(tdir, "starter")
    if os.path.isdir(starter):
        for name in os.listdir(starter):
            shutil.copy2(os.path.join(starter, name), out)
    return wt


def run_claude(wt, timeout_s, model):
    env = dict(os.environ)
    venv_scripts = os.path.join(REPO, ".venv", "Scripts")
    env["PATH"] = venv_scripts + os.pathsep + env.get("PATH", "")
    env["VIRTUAL_ENV"] = os.path.join(REPO, ".venv")
    cmd = ["claude", "-p", PROMPT, "--output-format", "json", "--allowedTools", ALLOWED_TOOLS,
           "--mcp-config", os.path.join(wt, ".mcp.json"), "--strict-mcp-config"]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(cmd, cwd=wt, env=env, capture_output=True, text=True,
                              encoding="utf-8", timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {"is_error": True, "result": f"timeout after {timeout_s}s"}
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"is_error": True, "result": (proc.stdout + proc.stderr)[-2000:]}


def review_domain(domain_path, workroot, name):
    """Score the written domain with the htn-reviewer, from the main repo's rubric."""
    if not os.path.exists(domain_path):
        return {"score": None, "summary": "no domain written"}
    d = os.path.join(workroot, "review", name)
    os.makedirs(d, exist_ok=True)
    shutil.copy2(domain_path, os.path.join(d, "ruleset.htn"))
    prompt = (calibrate.agent_body() + "\n\nThe ruleset to review is this file:\n"
              + os.path.join(d, "ruleset.htn"))
    proc = subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--allowedTools",
                           "Read Grep Glob", "--add-dir", d, "--strict-mcp-config"], cwd=REPO,
                          capture_output=True, text=True, encoding="utf-8", timeout=900)
    try:
        meta = json.loads(proc.stdout)
        m = re.search(r"\{.*\}", meta.get("result", ""), flags=re.S)
        verdict = json.loads(m.group(0))
        verdict["cost_usd"] = meta.get("total_cost_usd")
        return verdict
    except Exception as exc:
        return {"score": None, "summary": f"review failed: {exc!r}"}


def one(commit, task, run, workroot, timeout_s, model, outdir):
    wt = prepare(commit, task, os.path.join(workroot, f"r{run}"))
    try:
        started = datetime.datetime.now()
        meta = run_claude(wt, timeout_s, model)
        domain_path = os.path.join(wt, "task", "domain.htn")
        score = harness.check(os.path.join(TASKS_DIR, task), domain_path)
        review = review_domain(domain_path, workroot, f"{task}.r{run}")
        record = {
            "task": task, "run": run, "commit": commit,
            "passed": score["passed"], "total": score["total"], "results": score["results"],
            "cost_usd": meta.get("total_cost_usd"), "turns": meta.get("num_turns"),
            "duration_s": round((datetime.datetime.now() - started).total_seconds()),
            "is_error": meta.get("is_error"), "final_message": meta.get("result"),
            "review_score": review.get("score"), "review": review,
            "domain": harness.read(domain_path) if os.path.exists(domain_path) else None,
        }
        with open(os.path.join(outdir, f"{task}.r{run}.json"), "w", encoding="utf-8") as f:
            json.dump(record, f, indent=1)
        return record
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", wt], cwd=REPO, capture_output=True)


def summarize(records, label, commit):
    rows = sorted(records, key=lambda r: (r["task"], r["run"]))
    tasks = sorted({r["task"] for r in rows})
    lines = [f"# Benchmark: {label}", "", f"Commit `{commit}`, {len(rows)} runs.", "",
             "| task | run | instances passed | solved | review /5 | cost $ | turns | minutes |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['task']} | {r['run']} | {r['passed']}/{r['total']} | "
                     f"{'yes' if r['passed'] == r['total'] else 'no'} | {r.get('review_score')} | "
                     f"{(r['cost_usd'] or 0):.2f} | {r['turns']} | {r['duration_s'] / 60:.1f} |")
    solved = sum(r["passed"] == r["total"] for r in rows)
    inst = sum(r["passed"] for r in rows), sum(r["total"] for r in rows)
    reviewed = [r["review_score"] for r in rows if isinstance(r.get("review_score"), (int, float))]
    mean_review = sum(reviewed) / len(reviewed) if reviewed else float("nan")
    lines += ["", f"**Tasks solved: {solved}/{len(rows)}. Instances passed: {inst[0]}/{inst[1]}. "
              f"Mean review score: {mean_review:.2f}/5.**",
              "", "Per task (solved runs / runs): " +
              ", ".join(f"{t} {sum(r['passed'] == r['total'] for r in rows if r['task'] == t)}/"
                        f"{sum(r['task'] == t for r in rows)}" for t in tasks)]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--tasks", default="")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--model", default="")
    args = ap.parse_args()

    commit = git("rev-parse", "--short", args.commit).strip()
    tasks = args.tasks.split(",") if args.tasks else sorted(os.listdir(TASKS_DIR))
    outdir = os.path.join(RESULTS_DIR, args.label)
    os.makedirs(outdir, exist_ok=True)
    workroot = tempfile.mkdtemp(prefix="htnbench-")
    jobs = [(t, r) for r in range(1, args.runs + 1) for t in tasks]
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(one, commit, t, r, workroot, args.timeout, args.model, outdir): (t, r)
                   for t, r in jobs}
        for fut in concurrent.futures.as_completed(futures):
            t, r = futures[fut]
            try:
                rec = fut.result()
                records.append(rec)
                print(f"{t} r{r}: {rec['passed']}/{rec['total']}  ${(rec['cost_usd'] or 0):.2f}", flush=True)
            except Exception as exc:  # keep the other runs going
                print(f"{t} r{r}: FAILED {exc!r}", flush=True)
    summary = summarize(records, args.label, commit)
    with open(os.path.join(outdir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)
    print(summary)
    shutil.rmtree(workroot, ignore_errors=True)
    subprocess.run(["git", "worktree", "prune"], cwd=REPO)


if __name__ == "__main__":
    main()
