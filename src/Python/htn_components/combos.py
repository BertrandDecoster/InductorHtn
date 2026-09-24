"""Skill-combination validator: does a level need a team, and a real choice?

A level opts in by declaring who picks and from what:

    comboSeat(player, 1).        % the player picks one skill ...
    comboSeat(mage, 1).          % ... and so does the mage
    comboPool(sunder).           % from this pool
    comboPool(gust).
    comboMinWins(3).             % optional: at least 3 winning assignments (default 2)
    comboMinMethods(2).          % optional: at least 2 distinct methods (default 2)

Every seat's own `knows(seat, X)` facts are stripped; other companions keep
theirs. The validator then replans the level's goal (`goals(...)`) for:

  - every single skill, given to every seat at once: none may win;
  - every assignment (each seat picks its count from the pool): some must win.

and reports, across the winning plans:

  - solo plans: a plan whose casts are all one companion's (must be 0);
  - methods: distinct sets of skills cast in a winning plan (at least N);
  - skill usage: how many winning assignments use each skill; dead skills.

Each replan runs on a fresh planner in a worker process with a timeout (a
failed search locks the rule set, and some levels are slow).
"""

import itertools
import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


# The planner's default budget (1 MB) is too small for area pushes and spilled
# zones over several entities; each replan gets this much instead.
MEMORY_BUDGET = 256 * 1024 * 1024


def _facts(text: str, pred: str) -> List[List[str]]:
    out = []
    for m in re.finditer(rf"^{pred}\(([^?\n]*?)\)\.\s*$", text, flags=re.M):
        out.append([a.strip() for a in m.group(1).split(",")])
    return out


@dataclass
class ComboSpec:
    level_dir: str
    text: str
    goal: str
    seats: List[Tuple[str, int]]
    pool: List[str]
    companions: List[str]
    min_wins: int = 2
    min_methods: int = 2

    @classmethod
    def load(cls, level_dir: str) -> "ComboSpec":
        with open(os.path.join(level_dir, "level.htn"), encoding="utf-8") as f:
            text = f.read()
        goals = re.search(r"^goals\((.*)\)\.\s*$", text, flags=re.M)
        if not goals:
            raise ValueError("level.htn declares no goals(...)")
        seats = [(s, int(n)) for s, n in _facts(text, "comboSeat")]
        pool = [p for (p,) in _facts(text, "comboPool")]
        if not seats or not pool:
            raise ValueError("level.htn declares no comboSeat/2 or comboPool/1")
        companions = [e for e, r in _facts(text, "role") if r in ("player", "companion")]
        mw = _facts(text, "comboMinWins")
        mm = _facts(text, "comboMinMethods")
        return cls(level_dir, text, goals.group(1).strip() + ".", seats, pool, companions,
                   int(mw[0][0]) if mw else 2, int(mm[0][0]) if mm else 2)

    def stripped(self) -> str:
        text = self.text
        for seat, _ in self.seats:
            text = re.sub(rf"^knows\({seat},\s*\w+\)\.\s*\n", "", text, flags=re.M)
        return text


def _plan(project_root: str, level_dir: str, text: str, kit: str, goal: str) -> dict:
    """Worker: plan `goal` on a fresh planner with `kit` added. Returns the
    solutions (operator lists) or an error."""
    sys.path.insert(0, os.path.join(project_root, "src", "Python"))
    from indhtnpy import HtnPlanner
    from htn_components.loader import ComponentLoader
    from htn_components.manifest import Manifest

    planner = HtnPlanner(False)
    planner.SetMemoryBudget(MEMORY_BUDGET)
    loader = ComponentLoader(planner, project_root, warn=lambda m: None)
    manifest = Manifest.load(os.path.join(level_dir, "manifest.json"))
    for dep in manifest.dependencies:
        loader.load(dep)
    err = planner.HtnCompileCustomVariables(text + kit)
    if err:
        return {"error": err}
    err, result = planner.FindAllPlansCustomVariables(goal)
    if err:
        return {"error": err}
    sols = json.loads(result)
    if not sols or (isinstance(sols[0], dict) and "false" in sols[0]):
        return {"plans": []}
    plans = []
    for sol in sols:
        ops = []
        for op in sol:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            ops.append((name, args))
        plans.append(ops)
    return {"plans": plans}


@dataclass
class ComboReport:
    level: str
    singles_winning: List[str] = field(default_factory=list)
    assignments: int = 0
    winning: List[Dict[str, List[str]]] = field(default_factory=list)
    timeouts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    solo_plans: int = 0
    methods: List[List[str]] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    dead_skills: List[str] = field(default_factory=list)
    min_wins: int = 2
    min_methods: int = 2

    @property
    def failures(self) -> List[str]:
        out = []
        if self.singles_winning:
            out.append(f"a single skill wins: {', '.join(self.singles_winning)}")
        if len(self.winning) < self.min_wins:
            out.append(f"{len(self.winning)} winning assignment(s), want >= {self.min_wins}")
        if self.solo_plans:
            out.append(f"{self.solo_plans} plan(s) carried by one companion")
        if len(self.methods) < self.min_methods:
            out.append(f"{len(self.methods)} method(s), want >= {self.min_methods}")
        if self.errors:
            out.append(f"{len(self.errors)} replan error(s)")
        return out

    def to_dict(self) -> dict:
        return {
            "level": self.level, "singles_winning": self.singles_winning,
            "assignments": self.assignments, "winning_count": len(self.winning),
            "winning": self.winning, "timeouts": self.timeouts, "errors": self.errors,
            "solo_plans": self.solo_plans, "methods": self.methods, "usage": self.usage,
            "dead_skills": self.dead_skills, "failures": self.failures,
            "passed": not self.failures,
        }

    def text(self) -> str:
        lines = [f"Combos: {self.level}", "=" * (8 + len(self.level))]
        lines.append(f"single skills that win : {', '.join(self.singles_winning) or 'none'}")
        lines.append(f"winning assignments    : {len(self.winning)} of {self.assignments}")
        for w in self.winning:
            lines.append("    " + "  ".join(f"{s}={'+'.join(k)}" for s, k in w.items()))
        lines.append(f"methods (skills cast)  : {len(self.methods)}")
        for m in self.methods:
            lines.append("    " + " + ".join(m))
        lines.append(f"solo plans             : {self.solo_plans}")
        lines.append("skill usage            : " + ", ".join(f"{k} {v}" for k, v in
                                                            sorted(self.usage.items(), key=lambda x: -x[1])))
        lines.append(f"dead skills            : {', '.join(self.dead_skills) or 'none'}")
        if self.timeouts:
            lines.append(f"timeouts               : {len(self.timeouts)} ({'; '.join(self.timeouts[:3])})")
        for e in self.errors[:3]:
            lines.append(f"error                  : {e}")
        lines.append("")
        lines.append("RESULT: PASS" if not self.failures else "RESULT: FAIL - " + "; ".join(self.failures))
        return "\n".join(lines)


def run_combos(level_dir: str, project_root: str, timeout: float = 180.0,
               workers: Optional[int] = None) -> ComboReport:
    spec = ComboSpec.load(level_dir)
    base = spec.stripped()
    report = ComboReport(os.path.basename(os.path.normpath(level_dir)),
                         min_wins=spec.min_wins, min_methods=spec.min_methods)

    singles = {s: "".join(f"knows({seat}, {s}).\n" for seat, _ in spec.seats) for s in spec.pool}
    choices = [list(itertools.combinations(spec.pool, n)) for _, n in spec.seats]
    assignments = []
    for pick in itertools.product(*choices):
        kit = "".join(f"knows({seat}, {s}).\n" for (seat, _), skills in zip(spec.seats, pick)
                      for s in skills)
        assignments.append(({seat: list(skills) for (seat, _), skills in zip(spec.seats, pick)}, kit))
    report.assignments = len(assignments)

    workers = workers or max(1, (os.cpu_count() or 2) // 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        single_futs = {s: pool.submit(_plan, project_root, level_dir, base, kit, spec.goal)
                       for s, kit in singles.items()}
        assign_futs = [(a, pool.submit(_plan, project_root, level_dir, base, kit, spec.goal))
                       for a, kit in assignments]

        for s, fut in single_futs.items():
            try:
                res = fut.result(timeout=timeout)
            except FutureTimeout:
                report.timeouts.append(f"single {s}")
                continue
            if "error" in res:
                report.errors.append(f"single {s}: {res['error']}")
            elif res["plans"]:
                report.singles_winning.append(s)

        methods = set()
        usage = {s: 0 for s in spec.pool}
        for a, fut in assign_futs:
            label = " ".join(f"{k}={'+'.join(v)}" for k, v in a.items())
            try:
                res = fut.result(timeout=timeout)
            except FutureTimeout:
                report.timeouts.append(label)
                continue
            if "error" in res:
                report.errors.append(f"{label}: {res['error']}")
                continue
            if not res["plans"]:
                continue
            report.winning.append(a)
            for s in {s for v in a.values() for s in v}:
                usage[s] += 1
            for plan in res["plans"]:
                # Acting means casting: a companion that only walks is not
                # a second pair of hands.
                actors = {args[0] for name, args in plan if name == "opCast" and args}                     & set(spec.companions)
                if len(actors) < 2:
                    report.solo_plans += 1
                cast = sorted({args[1] for name, args in plan if name == "opCast" and len(args) > 1})
                if cast:
                    methods.add(tuple(cast))
    report.methods = [list(m) for m in sorted(methods)]
    report.usage = usage
    report.dead_skills = [s for s, n in usage.items() if n == 0]
    return report
