"""Plan-set structure: the for-all properties an enumerating planner gets for free.

A sampling generator can only estimate these; with every plan in hand they
are exact. Each function here is pure over a `PlanSpace` (or pieces of one)
and is documented against the literature it borrows from in
`docs/research/fun-cross-reference.md`:

  - **intent** (Smith, Butler & Popovic, "Quantifying over Play", FDG 2013):
    does every solution use the idea the level is about, and does none use
    what the author forbade?
  - **uniqueness** (diverse-planning metrics): is a plan just another plan
    plus a detour?
  - **landmarks** (Hoffmann, Porteous & Sebastia, JAIR 2004): what does every
    plan have to achieve?
  - **world chains** (Breath of the Wild's "multiplicative" design): how much
    of the causal work runs through the world rather than through actors?
  - **solution information** (Chen, White & Sturtevant, AIIDE 2023; Shen &
    Sturtevant, AIIDE 2024): how many bits must a player who picks uniformly
    among method alternatives be told to reach a solution?
"""

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

from .canonical import StrategyClass, task_signature
from .extract import Plan, PlanSpace, split_args


# --------------------------------------------------------------------------
# Level declarations
# --------------------------------------------------------------------------

def declared_args(facts: Iterable[str], functor: str) -> List[List[str]]:
    """Argument lists of every `functor(...)` fact, in source order."""
    prefix = functor + "("
    out: List[List[str]] = []
    for fact in facts:
        if fact.startswith(prefix) and fact.endswith(")"):
            out.append(split_args(fact[len(prefix):-1]))
    return out


# --------------------------------------------------------------------------
# Intent: funIntended / funForbidden
# --------------------------------------------------------------------------

@dataclass
class IntentDeclaration:
    groups: Dict[str, List[str]] = field(default_factory=dict)
    forbidden: List[str] = field(default_factory=list)

    @property
    def declared(self) -> bool:
        return bool(self.groups or self.forbidden)


def read_intent(facts: Iterable[str]) -> IntentDeclaration:
    """`funIntended(group, member)`, `funIntended(member)`, `funForbidden(member)`.

    A one-argument `funIntended` is a group of one, named after its member.
    """
    facts = list(facts)
    decl = IntentDeclaration()
    for args in declared_args(facts, "funIntended"):
        if len(args) == 1:
            decl.groups.setdefault(args[0], []).append(args[0])
        elif len(args) == 2:
            decl.groups.setdefault(args[0], []).append(args[1])
    for args in declared_args(facts, "funForbidden"):
        if args:
            decl.forbidden.append(args[0])
    return decl


def plan_uses(plan: Plan, member: str) -> bool:
    """A member is used when an operator has that name, or the plan uses the
    component (mechanism) of that name."""
    if any(op.name == member for op in plan.operators):
        return True
    return any(
        mechanism == member or mechanism.rsplit("/", 1)[-1] == member
        for mechanism in plan.mechanisms()
    )


def intent_violations(space: PlanSpace, decl: IntentDeclaration) -> Dict[str, Any]:
    """Which plans skip an intended group (shortcuts), which use a forbidden member."""
    shortcuts: Dict[str, List[int]] = {}
    for group, members in decl.groups.items():
        missing = [
            p.index for p in space.plans
            if not any(plan_uses(p, m) for m in members)
        ]
        if missing:
            shortcuts[group] = missing
    forbidden: Dict[str, List[int]] = {}
    for member in decl.forbidden:
        hits = [p.index for p in space.plans if plan_uses(p, member)]
        if hits:
            forbidden[member] = hits
    return {"shortcuts": shortcuts, "forbidden": forbidden}


# --------------------------------------------------------------------------
# Uniqueness
# --------------------------------------------------------------------------

def _multiset_key(items: Sequence[str]) -> FrozenSet[Tuple[str, int]]:
    """A multiset as a set, so sub-multiset is a C-speed `issubset`."""
    counts = Counter(items)
    return frozenset((k, i) for k, n in counts.items() for i in range(n))


def plan_uniqueness(space: PlanSpace, cap: int = 1500) -> Tuple[float, bool]:
    """Fraction of plans whose ground-operator multiset does not strictly
    contain another plan's.

    A plan that is another plan plus a detour inflates every count without
    adding an idea. Plans that are re-bindings of each other (companionA
    instead of companionB) are *not* supersets and are left to F1's classes.

    Returns (uniqueness, sampled). Beyond `cap` distinct multisets the check
    runs on the first `cap` of them, in planner order.
    """
    if not space.plans:
        return 0.0, False
    keyed: Dict[FrozenSet[Tuple[str, int]], int] = {}
    for plan in space.plans:
        key = _multiset_key([op.text for op in plan.operators])
        keyed[key] = keyed.get(key, 0) + 1
    keys = list(keyed)
    sampled = len(keys) > cap
    if sampled:
        keys = keys[:cap]
    keys.sort(key=len)

    padded_plans = 0
    total_plans = 0
    for i, key in enumerate(keys):
        total_plans += keyed[key]
        if any(len(other) < len(key) and other < key for other in keys[:i]):
            padded_plans += keyed[key]
    return (1.0 - padded_plans / total_plans if total_plans else 0.0), sampled


def padded_classes(classes: Sequence[StrategyClass]) -> List[Tuple[str, str]]:
    """`(padded, base)` pairs: the padded class's representative runs every
    ground operator the base's does, and more. That is the base idea plus a
    garnish.

    Ground operators, not names: a route that freezes the oil into sludge and
    then ignites the *sludge* is not the burn route plus a detour, although
    by name it runs every operator the burn route does. Name-level overlap
    is F2's distance; this check is for literal padding.
    """
    reps = [
        (c.label, _multiset_key([op.text for op in c.representative.operators]))
        for c in classes if c.representative is not None
    ]
    out: List[Tuple[str, str]] = []
    for label_a, key_a in reps:
        for label_b, key_b in reps:
            if label_a != label_b and key_b and key_b < key_a:
                out.append((label_a, label_b))
                break
    return out


# --------------------------------------------------------------------------
# Landmarks
# --------------------------------------------------------------------------

def landmarks(space: PlanSpace) -> Dict[str, Any]:
    """Facts every plan adds and operator names every plan uses.

    Over an enumerated plan set a landmark is an intersection. The goal's own
    effects are always among them; what else is there is the level's
    bottleneck - the step every route must pass through.
    """
    if not space.plans:
        return {"landmark_facts": [], "landmark_operators": [], "landmark_ratio": 0.0}
    achieved = [
        {fact for op in plan.operators for fact in op.adds} for plan in space.plans
    ]
    facts = set.intersection(*achieved) if achieved else set()
    operators = set.intersection(*(set(p.operator_names()) for p in space.plans))
    mean_achieved = sum(len(a) for a in achieved) / len(achieved)
    return {
        "landmark_facts": sorted(facts),
        "landmark_operators": sorted(operators),
        "landmark_ratio": round(len(facts) / mean_achieved, 3) if mean_achieved else 0.0,
    }


# --------------------------------------------------------------------------
# World chains
# --------------------------------------------------------------------------

def fact_atoms(fact: str) -> Set[str]:
    """Top-level atomic arguments of a fact."""
    open_idx = fact.find("(")
    if open_idx < 0:
        return set()
    return {a for a in split_args(fact[open_idx + 1: fact.rfind(")")]) if "(" not in a}


def world_chain_ratio(graphs: Dict[int, Any], actors: Set[str]) -> Optional[float]:
    """Share of causal edges whose linking fact names no actor.

    `wet(goblin)` enabling an electrocution is the world doing the work;
    `inside(companionA)` enabling a door opening is an actor's own state.
    None when no plan has a causal edge.
    """
    total = 0
    world = 0
    for graph in graphs.values():
        for reason in graph.reasons.values():
            _, _, fact = reason.partition(" ")
            total += 1
            if not (fact_atoms(fact) & actors):
                world += 1
    return round(world / total, 3) if total else None


# --------------------------------------------------------------------------
# Solution information
# --------------------------------------------------------------------------

def method_alternatives(space: PlanSpace) -> Dict[str, int]:
    """Rules defining each task signature, across every source the level loads."""
    from .extract import _import_parse_htn

    parse_htn = _import_parse_htn()
    alternatives: Dict[str, int] = {}
    for _component, text in space.sources:
        rules, _diags = parse_htn(text)
        for rule in rules:
            if not rule.is_method or rule.head is None:
                continue
            sig = f"{rule.head.name}/{len(rule.head.args)}"
            alternatives[sig] = alternatives.get(sig, 0) + 1
    return alternatives


Decision = Tuple[str, int, int]  # (task signature, method index, alternatives)


def plan_decisions(plan: Plan, alternatives: Dict[str, int]) -> Tuple[Decision, ...]:
    """The method choices along a plan, in decomposition order."""
    out: List[Decision] = []
    for node in sorted(plan.path, key=lambda n: n.get("treeNodeID", 0)):
        if node.get("isOperator") or not node.get("methodSignature"):
            continue
        sig = task_signature(node.get("taskName", ""))
        k = alternatives.get(sig, 1)
        out.append((sig, node.get("methodIndex", -1), max(1, k)))
    return tuple(out)


def _success_probability(sequences: Iterable[Tuple[Decision, ...]]) -> float:
    """P(a uniform-over-methods policy completes some sequence).

    The sequences form a trie. At each node the next decision is a task with
    k alternatives, and each distinct method some plan took there contributes
    P(child) / k. Children that decide a *different* task at the same point
    are binding variants - the same method choices landing on different
    ground tasks - which the policy does not choose between, so the best of
    them counts, not their sum.
    """
    trie: Dict[Any, Any] = {}
    for seq in sequences:
        node = trie
        for decision in seq:
            node = node.setdefault(decision, {})
        node[None] = {}

    def prob(node: Dict[Any, Any]) -> float:
        if None in node:
            return 1.0
        by_task: Dict[str, float] = {}
        for decision, child in node.items():
            sig, _method, k = decision
            by_task[sig] = by_task.get(sig, 0.0) + prob(child) / k
        return min(1.0, max(by_task.values())) if by_task else 0.0

    return prob(trie)


def solution_information(
    space: PlanSpace,
    classes: Sequence[StrategyClass] = (),
    alternatives: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Bits a uniform-over-methods player needs to be told to solve the level.

    At each task on the way to a solution the player picks uniformly among
    the k rules that define it - Pelanek's "alternatives to refute". The
    successful choices are the methods some plan took there.

      solution_information_bits = -log2 P(the policy completes some plan)
      easiest_plan_bits         = min over plans of sum log2 k  (the MSI analogue)
    """
    if alternatives is None:
        alternatives = method_alternatives(space)
    per_plan: Dict[int, float] = {}
    sequences: Set[Tuple[Decision, ...]] = set()
    for plan in space.plans:
        seq = plan_decisions(plan, alternatives)
        per_plan[plan.index] = sum(math.log2(k) for _, _, k in seq)
        sequences.add(seq)

    if not sequences:
        return {"solution_information_bits": None, "easiest_plan_bits": None,
                "solution_information_per_class": {}, "decision_sequences": 0}

    probability = _success_probability(sequences)
    total_bits = -math.log2(probability) if 0.0 < probability < 1.0 else 0.0
    per_class = {
        c.label: round(min(per_plan[i] for i in c.plan_indices if i in per_plan), 2)
        for c in classes
        if any(i in per_plan for i in c.plan_indices)
    }
    return {
        "solution_information_bits": round(total_bits, 2),
        "easiest_plan_bits": round(min(per_plan.values()), 2),
        "solution_information_per_class": per_class,
        "decision_sequences": len(sequences),
    }
