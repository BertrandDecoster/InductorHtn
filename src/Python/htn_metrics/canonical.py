"""Grouping plans into *ideas*, and measuring how far apart those ideas are.

A level with 116 plans does not offer the player 116 things to discover. Most
of that count is re-binding: the same idea with companionB instead of
companionA. `strategy_fingerprint` collapses that by looking only at which
*method alternative* was chosen at the layers where alternatives encode a
different intent (goals / strategies / levels by default), ignoring the
primitive layer where alternatives are mechanical, and ignoring choices made
deep inside a decomposition, which are implementation detail rather than a
different plan.

Distance between two classes is a weighted Jaccard over a bag that mixes the
plan's operator-name multiset with its mechanism set, so two classes count as
different when they use different actions *or* different parts of the rule
library.
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .extract import Plan, PlanSpace


# --------------------------------------------------------------------------
# Task-name parsing (the tree gives us rendered task text, not a signature)
# --------------------------------------------------------------------------

def task_signature(task_name: str) -> str:
    """`"planToDamage(gob)"` -> `"planToDamage/1"`.

    Counts arguments at paren depth 1 so nested compound arguments do not
    inflate the arity.
    """
    text = task_name.strip()
    open_idx = text.find("(")
    if open_idx < 0:
        return f"{text}/0"
    functor = text[:open_idx]
    depth = 0
    args = 0
    seen_content = False
    for ch in text[open_idx:]:
        if ch in "([":
            depth += 1
            if depth == 1:
                continue
        elif ch in ")]":
            depth -= 1
            if depth == 0:
                break
        if depth == 1:
            if ch == ",":
                args += 1
            elif not ch.isspace():
                seen_content = True
    if seen_content:
        args += 1
    return f"{functor}/{args}"


def task_functor(task_name: str) -> str:
    text = task_name.strip()
    open_idx = text.find("(")
    return text[:open_idx] if open_idx >= 0 else text


# --------------------------------------------------------------------------
# Fingerprinting
# --------------------------------------------------------------------------

def path_depths(plan: Plan) -> Dict[int, int]:
    """Decomposition depth of every node on the plan's path (root = 0)."""
    by_id = {n.get("treeNodeID"): n for n in plan.path}
    depths: Dict[int, int] = {}

    def depth_of(node_id: int) -> int:
        if node_id in depths:
            return depths[node_id]
        node = by_id.get(node_id)
        if node is None:
            return 0
        parent_id = node.get("parentNodeID", -1)
        value = 0 if parent_id not in by_id else depth_of(parent_id) + 1
        depths[node_id] = value
        return value

    for node in plan.path:
        depth_of(node.get("treeNodeID"))
    return depths


def strategy_fingerprint(
    plan: Plan,
    method_layer: Dict[str, str],
    fingerprint_layers: Sequence[str],
    max_depth: int = 2,
) -> Tuple[str, ...]:
    """The ordered tuple of method choices that make this plan *an idea*.

    Each element is `task/arity#methodIndex`: which task was decomposed and
    which of its alternatives was taken. A node contributes only if it passes
    two filters:

      - its defining component sits in a **fingerprint layer** (primitive-layer
        alternatives are mechanical re-binding, not a different intent), and
      - it sits within `max_depth` of the root.

    The depth cap is what keeps a self-contained level honest, and it applies
    to the `levels` layer only. A component level gets its separation from
    the layer structure - a `goals` or `strategies` method is an idea
    wherever it sits, including under a level method that composes two
    fights - but a level that defines all its methods in `level.htn` has no
    layering to appeal to, and without a cap every phase choice deep inside a
    decomposition would read as a separate strategy. A strategy is a choice
    you make near the top of a plan; choices inside a phase are
    implementation detail.

    Within a component, only the *entry* into it counts: the first method
    of a strategy component reached from outside it is the idea; the
    helper methods it decomposes into (which trap to use, who covers, how
    to finish) are how that idea is carried out.

    Falls back to the operator-name sequence when nothing qualifies, so a
    level still gets meaningful (if coarse) classes rather than one giant one.
    """
    depths = path_depths(plan)
    by_id = {n.get("treeNodeID"): n for n in plan.path}
    elements: List[str] = []
    for node in sorted(plan.path, key=lambda n: n.get("treeNodeID", 0)):
        if node.get("isOperator"):
            continue
        if not node.get("methodSignature"):
            continue
        sig = task_signature(node.get("taskName", ""))
        layer = method_layer.get(sig)
        if layer is None or layer not in fingerprint_layers:
            continue
        if layer == "levels" and depths.get(node.get("treeNodeID"), 0) >= max_depth:
            continue
        if layer != "levels":
            # Nearest ancestor that is a real method, looking through the
            # try()/anyOf wrappers the planner inserts.
            parent = by_id.get(node.get("parentNodeID"))
            while parent is not None and method_layer.get(
                task_signature(parent.get("taskName", ""))
            ) is None and parent.get("parentNodeID", -1) != -1:
                parent = by_id.get(parent.get("parentNodeID"))
            if parent is not None:
                parent_sig = task_signature(parent.get("taskName", ""))
                if method_layer.get(parent_sig) == layer:
                    continue  # a helper inside the same component layer
        elements.append(f"{sig}#{node.get('methodIndex', -1)}")

    if elements:
        return tuple(elements)
    return tuple(f"op:{name}" for name in plan.operator_names())


def fingerprint_label(fingerprint: Sequence[str]) -> str:
    """Human-readable name for a class: the task functors it chose."""
    parts: List[str] = []
    for element in fingerprint:
        if element.startswith("op:"):
            parts.append(element[3:])
            continue
        sig = element.split("#")[0]
        name = sig.split("/")[0]
        if not parts or parts[-1] != name:
            parts.append(name)
    return " > ".join(parts) if parts else "(empty)"


# --------------------------------------------------------------------------
# Equivalence classes
# --------------------------------------------------------------------------

@dataclass
class StrategyClass:
    """All plans sharing one fingerprint."""

    fingerprint: Tuple[str, ...]
    label: str
    plan_indices: List[int] = field(default_factory=list)
    representative: Optional[Plan] = None

    @property
    def size(self) -> int:
        return len(self.plan_indices)

    def to_dict(self) -> Dict[str, Any]:
        rep = self.representative
        return {
            "label": self.label,
            "fingerprint": list(self.fingerprint),
            "size": self.size,
            "plan_indices": self.plan_indices,
            "representative": {
                "length": rep.length if rep else 0,
                "operators": [op.text for op in rep.operators] if rep else [],
                "mechanisms": sorted(rep.mechanisms()) if rep else [],
            },
        }


def classify(
    space: PlanSpace,
    fingerprint_layers: Sequence[str],
    max_depth: int = 2,
) -> List[StrategyClass]:
    """Group a plan space into strategy classes, largest first.

    The representative is the shortest plan in the class, ties broken
    lexicographically on the operator sequence, so reports are stable across
    runs and a class is illustrated by its cleanest member.
    """
    buckets: Dict[Tuple[str, ...], List[Plan]] = {}
    for plan in space.plans:
        fp = strategy_fingerprint(
            plan, space.method_layer, fingerprint_layers, max_depth
        )
        buckets.setdefault(fp, []).append(plan)

    classes: List[StrategyClass] = []
    for fp, plans in buckets.items():
        rep = min(plans, key=lambda p: (p.length, tuple(op.text for op in p.operators)))
        classes.append(
            StrategyClass(
                fingerprint=fp,
                label=fingerprint_label(fp),
                plan_indices=sorted(p.index for p in plans),
                representative=rep,
            )
        )
    classes.sort(key=lambda c: (-c.size, c.label))
    _disambiguate_labels(classes)
    return classes


def _disambiguate_labels(classes: List[StrategyClass]) -> None:
    """Suffix colliding labels so a scorecard never lists the same name twice.

    Two classes can share a label when they differ only in *which* alternative
    of a task they took - the task functor is the same either way. The full
    fingerprint always distinguishes them and is kept in the JSON output.
    """
    seen: Dict[str, int] = {}
    counts = Counter(c.label for c in classes)
    for cls in classes:
        if counts[cls.label] < 2:
            continue
        index = seen.get(cls.label, 0) + 1
        seen[cls.label] = index
        cls.label = f"{cls.label} [alt {index}]"


# --------------------------------------------------------------------------
# Distance
# --------------------------------------------------------------------------

def plan_profile(plan: Plan) -> Counter:
    """The bag a distance is computed over: operator names + mechanisms.

    Operator *names* rather than full ground terms: "companionA burns it" and
    "companionB burns it" are the same idea and must not read as distinct.
    Mechanisms are added so two classes using different components register as
    far apart even when their operator names overlap.
    """
    bag = Counter(plan.operator_names())
    for mechanism in plan.mechanisms():
        bag[f"mech:{mechanism}"] += 1
    return bag


def weighted_jaccard(a: Counter, b: Counter) -> float:
    """Sum-of-mins over sum-of-maxes. 1.0 for identical bags, 0.0 for disjoint."""
    keys = set(a) | set(b)
    if not keys:
        return 1.0
    inter = sum(min(a.get(k, 0), b.get(k, 0)) for k in keys)
    union = sum(max(a.get(k, 0), b.get(k, 0)) for k in keys)
    return inter / union if union else 1.0


def pairwise_distances(classes: Sequence[StrategyClass]) -> List[Tuple[str, str, float]]:
    """`(label_a, label_b, 1 - weighted_jaccard)` for every class pair."""
    out: List[Tuple[str, str, float]] = []
    for i in range(len(classes)):
        for j in range(i + 1, len(classes)):
            rep_a, rep_b = classes[i].representative, classes[j].representative
            if rep_a is None or rep_b is None:
                continue
            distance = 1.0 - weighted_jaccard(plan_profile(rep_a), plan_profile(rep_b))
            out.append((classes[i].label, classes[j].label, distance))
    return out


def mechanism_disjointness(classes: Sequence[StrategyClass]) -> float:
    """Fraction of class pairs whose mechanism sets are not nested.

    Nesting matters more than overlap: if class B uses every component class A
    uses plus one more, B is A with a garnish, not a second idea.
    """
    pairs = 0
    disjointish = 0
    for i in range(len(classes)):
        for j in range(i + 1, len(classes)):
            rep_a, rep_b = classes[i].representative, classes[j].representative
            if rep_a is None or rep_b is None:
                continue
            set_a, set_b = rep_a.mechanisms(), rep_b.mechanisms()
            pairs += 1
            if not (set_a <= set_b or set_b <= set_a):
                disjointish += 1
    return disjointish / pairs if pairs else 0.0
