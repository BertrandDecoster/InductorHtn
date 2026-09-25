"""Check that the htn-reviewer agent agrees with the owner's ratings.

ratings.json holds the owner's 1-5 stars for 34 rulesets (2026-09-25). Each file is
read from the commit it was rated at (the slop has since been deleted), copied to a
temp dir under a neutral name so the path gives nothing away, and reviewed with
`claude -p` using the body of .claude/agents/htn-reviewer.md. The result is the rank
agreement (Spearman) between reviewer scores and stars, plus a per-file table.

    python bench/calibration/calibrate.py [--jobs 6] [--only id1,id2] [--label NAME]
"""

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AGENT = os.path.join(REPO, ".claude", "agents", "htn-reviewer.md")


def agent_body():
    text = open(AGENT, encoding="utf-8").read()
    return re.sub(r"^---.*?---\s*", "", text, flags=re.S)


def extract(item, outdir):
    paths = []
    for i, path in enumerate(item["paths"]):
        text = subprocess.run(["git", "show", f"{item['commit']}:{path}"], cwd=REPO, check=True,
                              capture_output=True, text=True, encoding="utf-8").stdout
        name = "ruleset.htn" if i == 0 else f"part{i + 1}.htn"
        dest = os.path.join(outdir, name)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text)
        paths.append(dest)
    return paths


def review(item, tmproot):
    outdir = os.path.join(tmproot, item["id"])
    os.makedirs(outdir)
    files = extract(item, outdir)
    prompt = (agent_body() + "\n\nThe ruleset to review is these files (together they are one "
              "ruleset; review them as a whole):\n" + "\n".join(files))
    proc = subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--allowedTools",
                           "Read Grep Glob", "--add-dir", outdir, "--strict-mcp-config"],
                          cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=900)
    meta = json.loads(proc.stdout)
    m = re.search(r"\{.*\}", meta.get("result", ""), flags=re.S)
    verdict = json.loads(m.group(0)) if m else {"score": None, "summary": meta.get("result", "")[:300]}
    verdict["cost_usd"] = meta.get("total_cost_usd")
    return verdict


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--label", default="latest")
    args = ap.parse_args()
    items = json.load(open(os.path.join(HERE, "ratings.json"), encoding="utf-8"))
    if args.only:
        keep = set(args.only.split(","))
        items = [i for i in items if i["id"] in keep]
    tmproot = tempfile.mkdtemp(prefix="htncal-")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futs = {pool.submit(review, it, tmproot): it for it in items}
        for fut in concurrent.futures.as_completed(futs):
            it = futs[fut]
            try:
                results[it["id"]] = fut.result()
            except Exception as exc:
                results[it["id"]] = {"score": None, "summary": f"error: {exc!r}"}
            print(f"{it['id']:28s} owner {it['stars']}  reviewer {results[it['id']].get('score')}", flush=True)
    scored = [i for i in items if isinstance(results[i["id"]].get("score"), (int, float))]
    rho = spearman([i["stars"] for i in scored], [results[i["id"]]["score"] for i in scored])
    exact = sum(results[i["id"]]["score"] == i["stars"] for i in scored)
    within1 = sum(abs(results[i["id"]]["score"] - i["stars"]) <= 1 for i in scored)
    cost = sum(r.get("cost_usd") or 0 for r in results.values())
    lines = [f"# Reviewer calibration: {args.label}", "",
             f"Spearman rho = **{rho:.2f}** over {len(scored)} rulesets; exact {exact}, within 1 star "
             f"{within1}; cost ${cost:.2f}.", "", "| ruleset | owner | reviewer | reviewer summary |",
             "|---|---|---|---|"]
    for i in sorted(items, key=lambda i: (-i["stars"], i["id"])):
        r = results[i["id"]]
        lines.append(f"| {i['id']} | {i['stars']} | {r.get('score')} | "
                     f"{(r.get('summary') or '').replace('|', '/')[:160]} |")
    out = os.path.join(HERE, "results")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, f"{args.label}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out, f"{args.label}.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    print("\n".join(lines[:3]))


if __name__ == "__main__":
    main()
