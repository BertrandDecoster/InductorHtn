"""Human ratings next to scorecards: the held-out signal the metrics answer to.

Every plan-set metric in this package is a proxy. None has been validated
against human judgement of fun in cooperative puzzles (see
`docs/research/fun-cross-reference.md` section 4.5), so the bands in
`metrics.json` are intuition until data says otherwise. This module is how
data gets in:

  - `fun-rate` appends one human rating, with the level's flattened
    scorecard and source hash at the moment of rating, to a JSONL log;
  - `fun-calibrate` ranks every numeric metric by its Spearman correlation
    with the ratings.

The rating is deliberately *not* a metric: an agent iterating on a level
never sees it, so a level whose visible numbers rise while its ratings fall
is the signature of the metrics being gamed.
"""

import datetime as _dt
import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .expect import flatten_metrics

MIN_RATINGS = 5

# Metrics keyed by a level's own labels (class names, fact names). They do
# not mean the same thing from one level to the next, so they are not logged.
_PER_LEVEL = (
    "class_sizes", "per_class", "solution_information_per_class",
    "insight_depth_per_class", "critical_facts", "shortcut_plans",
    "forbidden_plans", "intended_groups",
)


def default_log_path(project_root: str) -> str:
    return os.path.join(project_root, "levels", "fun_ratings.jsonl")


def rating_record(
    profile: Any, rating: int, rater: str = "", note: str = "",
    source_hash: str = "",
) -> Dict[str, Any]:
    metrics = {
        f"{family}.{name}": value
        for (family, name), value in flatten_metrics(profile.families).items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        and not any(name == p or name.startswith(p + "_") for p in _PER_LEVEL)
    }
    return {
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        "level": profile.level_id,
        "source_hash": source_hash,
        "rating": rating,
        "rater": rater,
        "note": note,
        "fun_score": profile.fun_score,
        "overall": profile.overall,
        "metrics": metrics,
    }


def append_rating(path: str, record: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def load_ratings(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _ranks(values: Sequence[float]) -> List[float]:
    """Average ranks, so ties share their mean position."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        mean_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = mean_rank
        i = j + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """Spearman rank correlation; None when either side is constant."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx * vy) ** 0.5


def correlate(records: Sequence[Dict[str, Any]]) -> List[Tuple[str, float, int]]:
    """`(metric, rho, n)` for every metric present in enough records,
    strongest correlation first. The composite is included as `fun_score`
    so it can be held to the same standard as the families."""
    names = set()
    for rec in records:
        names.update(rec.get("metrics", {}))
    out: List[Tuple[str, float, int]] = []
    for name in sorted(names) + ["fun_score"]:
        pairs = [
            (rec.get("metrics", {}).get(name) if name != "fun_score"
             else rec.get("fun_score"),
             rec["rating"])
            for rec in records
        ]
        pairs = [(float(x), float(y)) for x, y in pairs if x is not None]
        if len(pairs) < MIN_RATINGS:
            continue
        rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
        if rho is not None:
            out.append((name, rho, len(pairs)))
    out.sort(key=lambda t: -abs(t[1]))
    return out
