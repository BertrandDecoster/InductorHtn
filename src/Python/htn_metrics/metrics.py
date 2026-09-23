"""The six metric families, as pure functions over a `PlanSpace`.

Each function returns a `FamilyResult`: the numbers, a verdict against the
bands in `metrics.json`, and plain-language findings naming what tripped.
Nothing here plans or perturbs; F2's independence and all of F4 take their
counterfactual input as an argument so this module stays cheap and testable.

See `docs/FUN_METRICS.md` for what each metric means and where it is blind.
"""

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set

from .canonical import (
    StrategyClass,
    classify,
    mechanism_disjointness,
    pairwise_distances,
    task_signature,
)
from .agency import ActorConvention
from .causal import CausalGraph, build_causal_graph, decomposition_depth
from .config import Config
from .extract import PlanSpace
from .trie import PlanTrie

PASS, WARN, FAIL, SKIP = "pass", "warn", "fail", "skip"

_SEVERITY = {SKIP: -1, PASS: 0, WARN: 1, FAIL: 2}


@dataclass
class FamilyResult:
    """One family's numbers plus the judgement made from them."""

    key: str
    title: str
    encodes: str
    verdict: str = PASS
    metrics: Dict[str, Any] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)

    def flag(self, verdict: str, message: str) -> None:
        """Record a finding, keeping the worst verdict seen."""
        self.findings.append(message)
        if _SEVERITY[verdict] > _SEVERITY[self.verdict]:
            self.verdict = verdict

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key, "title": self.title, "encodes": self.encodes,
            "verdict": self.verdict, "metrics": self.metrics,
            "findings": self.findings,
        }


# ==========================================================================
# F1 - Multiplicity
# ==========================================================================

def f1_multiplicity(
    space: PlanSpace, classes: Sequence[StrategyClass], cfg: Config,
    lattice: Optional[Dict[str, Any]] = None,
) -> FamilyResult:
    result = FamilyResult(
        key="f1_multiplicity",
        title="Multiplicity - are there several ways?",
        encodes="GDD 3.6: always have at least 2 or 3 ways to defeat an enemy",
    )
    plan_count = space.plan_count
    class_count = len(classes)
    redundancy = (plan_count / class_count) if class_count else 0.0
    across = (lattice or {}).get("strategy_classes_across_loadouts")

    result.metrics = {
        "plan_count": plan_count,
        "truncated": space.truncated,
        "strategy_classes": class_count,
        "strategy_classes_across_loadouts": across,
        "redundancy": round(redundancy, 2),
        "class_sizes": {c.label: c.size for c in classes},
    }

    if space.truncated and "memory" in space.truncation_reason.lower():
        result.flag(
            FAIL,
            f"planner ran out of memory ({space.truncation_reason}) - there is "
            f"no plan set to measure; raise memory_budget_bytes or shrink the level",
        )
        return result
    if plan_count == 0:
        result.flag(FAIL, "no plans at all - the level is unsolvable as declared")
        return result

    low = cfg.band("f1_multiplicity.strategy_classes_min", 2)
    high = cfg.band("f1_multiplicity.strategy_classes_max", 5)
    if class_count < low and across is not None and across >= low:
        # The default kit shows one idea; other kits show others. For a
        # level built around a choice space that is the design working.
        result.flag(
            WARN,
            f"the default kit shows {class_count} strategy class, but winning "
            f"loadouts reach {across} across the choice space - the ideas are "
            f"in the kit choice, not in one kit",
        )
    elif class_count < low:
        result.flag(
            FAIL,
            f"only {class_count} strategy class for {plan_count} plans - "
            f"there is one idea here, found {low - class_count} short of the minimum",
        )
    elif class_count > high:
        result.flag(
            WARN,
            f"{class_count} strategy classes exceeds {high}; more distinct intents "
            f"than an author can hold, or the fingerprint layer is too fine",
        )

    redundancy_cap = cfg.band("f1_multiplicity.redundancy_warn_above", 10.0)
    if redundancy > redundancy_cap:
        result.flag(
            WARN,
            f"redundancy {redundancy:.1f} plans per idea (> {redundancy_cap}) - "
            f"the plan space is mostly re-binding noise",
        )
    return result


# ==========================================================================
# F2 - Distinctness
# ==========================================================================

def f2_distinctness(
    space: PlanSpace,
    classes: Sequence[StrategyClass],
    cfg: Config,
    ablation: Optional[Dict[str, Any]] = None,
) -> FamilyResult:
    result = FamilyResult(
        key="f2_distinctness",
        title="Distinctness - are the ways actually different?",
        encodes="anti-fake-multiplicity; several names for one idea is still one idea",
    )
    distances = pairwise_distances(classes)
    values = [d for _, _, d in distances]

    result.metrics = {
        "class_pairs": len(values),
        "min_pairwise_distance": round(min(values), 3) if values else None,
        "mean_pairwise_distance": (
            round(sum(values) / len(values), 3) if values else None
        ),
        "mechanism_disjointness": round(mechanism_disjointness(classes), 3),
        "closest_pair": (
            list(min(distances, key=lambda d: d[2])[:2]) if distances else None
        ),
    }

    if not values:
        result.flag(SKIP, "fewer than two strategy classes - nothing to compare")
        return result

    # Ablation is the stronger evidence, so it is read first: a syntactic
    # overlap between two classes that provably depend on disjoint facts is
    # worth a warning, not a failure.
    want_pairs = cfg.band("f2_distinctness.independent_class_pairs_min", 1)
    conclusive = ablation is None or bool(ablation.get("conclusive", True))
    independence_confirmed = (
        ablation is not None and conclusive
        and ablation.get("independent_pairs", 0) >= want_pairs
    )

    floor = cfg.band("f2_distinctness.min_pairwise_distance_min", 0.4)
    lowest = min(values)
    if lowest < floor:
        pair = min(distances, key=lambda d: d[2])
        severe_factor = cfg.band("f2_distinctness.severe_distance_factor", 0.5)
        severe = lowest < floor * severe_factor and not independence_confirmed
        result.flag(
            FAIL if severe else WARN,
            f"closest pair is {lowest:.2f} apart (want >= {floor}): "
            f"'{pair[0]}' and '{pair[1]}' use nearly the same operators"
            + (
                " (ablation shows they do rely on different facts, so this is "
                "surface similarity rather than a duplicate idea)"
                if independence_confirmed else ""
            ),
        )

    mean_floor = cfg.band("f2_distinctness.mean_pairwise_distance_warn_below", 0.5)
    mean_distance = sum(values) / len(values)
    if mean_distance < mean_floor:
        result.flag(
            WARN,
            f"mean distance {mean_distance:.2f} below {mean_floor} - the classes "
            f"share most of their operators",
        )

    if ablation is None:
        result.metrics["independence"] = "not measured (run with --ablate)"
        result.findings.append(
            "independence and shared-linchpin not measured; re-run with --ablate"
        )
        return result

    result.metrics["critical_facts"] = ablation.get("critical_facts", {})
    result.metrics["independent_class_pairs"] = ablation.get("independent_pairs", 0)
    result.metrics["shared_linchpin"] = ablation.get("linchpins", [])
    result.metrics["shared_gates"] = ablation.get("shared_gates", [])
    result.metrics["goal_target_linchpins"] = ablation.get("goal_target_linchpins", [])
    result.metrics["ablation_facts_tested"] = ablation.get("facts_tested", 0)
    result.metrics["ablation_conclusive"] = conclusive
    result.metrics["ablation_unknown_probes"] = ablation.get("unknown_probes", 0)

    if ablation.get("sampled"):
        result.flag(
            WARN,
            f"ablation sampled {ablation.get('facts_tested')} of "
            f"{ablation.get('facts_total')} facts (cap max_ablation_facts) - "
            f"linchpins and independence are estimates, not a sweep",
        )

    if not conclusive:
        reasons = ablation.get("unknown_reasons") or []
        first = f" (first: {reasons[0][0]}: {reasons[0][1]})" if reasons else ""
        result.flag(
            WARN,
            f"ablation inconclusive: {ablation.get('unknown_probes', 0)} probe(s) "
            f"could not finish{first} - shared-linchpin and independence claims "
            f"are withheld",
        )

    # Positive evidence from a probe that did finish still stands.
    linchpins = ablation.get("linchpins", [])
    if linchpins:
        result.flag(
            FAIL,
            f"shared linchpin: removing {linchpins[0]} kills every strategy class "
            f"({len(linchpins)} such fact(s)) - the paths were never independent",
        )

    gates = ablation.get("shared_gates", [])
    if gates:
        result.findings.append(
            f"shared gate: {gates[0]} is required by every route ({len(gates)} "
            f"such fact(s)); the routes are independent elsewhere, so this is "
            f"infrastructure they all pass through, not one idea under several names"
        )

    have_pairs = ablation.get("independent_pairs", 0)
    if conclusive and have_pairs < want_pairs:
        result.flag(
            WARN,
            f"{have_pairs} class pair(s) with disjoint critical facts, want "
            f">= {want_pairs} - the classes lean on the same world facts",
        )
    return result


# ==========================================================================
# F3 - Depth
# ==========================================================================

def causal_graphs(space: PlanSpace) -> Dict[int, CausalGraph]:
    """One causal graph per plan, keyed by plan index. Built once and shared
    by F3, F5 and F6."""
    return {p.index: build_causal_graph(p, space.initial_facts) for p in space.plans}


def f3_depth(
    space: PlanSpace, classes: Sequence[StrategyClass], cfg: Config,
    graphs: Optional[Dict[int, CausalGraph]] = None,
) -> FamilyResult:
    result = FamilyResult(
        key="f3_depth",
        title="Depth - is the plan worth executing?",
        encodes="GDD 3.6: not too long, not too short; a combo, not a chore",
    )
    if not space.plans:
        result.flag(FAIL, "no plans to measure")
        return result

    lengths = [p.length for p in space.plans]
    graphs = graphs if graphs is not None else causal_graphs(space)

    depths = [g.depth for g in graphs.values()]
    interlocks = [g.interlock for g in graphs.values()]
    decomps = [decomposition_depth(p) for p in space.plans]

    best_class_depth = 0
    per_class: Dict[str, Dict[str, Any]] = {}
    for cls in classes:
        rep = cls.representative
        if rep is None:
            continue
        graph = graphs.get(rep.index)
        if graph is None:
            continue
        per_class[cls.label] = {
            "length": rep.length,
            "causal_depth": graph.depth,
            "interlock": round(graph.interlock, 2),
        }
        best_class_depth = max(best_class_depth, graph.depth)

    result.metrics = {
        "plan_length": {
            "min": min(lengths),
            "median": statistics.median(lengths),
            "max": max(lengths),
        },
        "causal_depth": {"min": min(depths), "max": max(depths),
                         "best_class": best_class_depth},
        "interlock": {
            "min": round(min(interlocks), 2),
            "mean": round(sum(interlocks) / len(interlocks), 2),
            "max": round(max(interlocks), 2),
        },
        "decomposition_depth": {"min": min(decomps), "max": max(decomps)},
        "per_class": per_class,
    }

    length_min = cfg.band("f3_depth.plan_length_min", 3)
    length_max = cfg.band("f3_depth.plan_length_max", 12)
    median_length = statistics.median(lengths)
    if median_length < length_min:
        result.flag(
            FAIL,
            f"median plan is {median_length} operators (< {length_min}) - "
            f"'I cast fireball and everyone dies'",
        )
    elif median_length > length_max:
        result.flag(
            WARN,
            f"median plan is {median_length} operators (> {length_max}) - "
            f"players will not find a plan this long",
        )

    want_depth = cfg.band("f3_depth.causal_depth_min", 3)
    if best_class_depth < want_depth:
        result.flag(
            WARN,
            f"best class has causal depth {best_class_depth} (want >= {want_depth}) - "
            f"no Primer -> Catalyst -> Detonator chain; operators barely feed each other",
        )

    want_interlock = cfg.band("f3_depth.interlock_min", 0.5)
    mean_interlock = sum(interlocks) / len(interlocks)
    if mean_interlock < want_interlock:
        result.flag(
            WARN,
            f"mean interlock {mean_interlock:.2f} (want >= {want_interlock}) - most "
            f"operators are causally independent, so the plan reads as a chore",
        )
    return result


# ==========================================================================
# F4 - Choice structure
# ==========================================================================

def f4_choice(
    space: PlanSpace, cfg: Config, lattice: Optional[Dict[str, Any]] = None
) -> FamilyResult:
    result = FamilyResult(
        key="f4_choice",
        title="Choice structure - the X-of-Y lattice",
        encodes="pick X of Y; each pick enables several things; cover all blockers",
    )
    declared = any(f.startswith("funChoiceSpace(") for f in space.facts_used)
    if lattice is None:
        result.verdict = SKIP
        result.metrics = {"declared": declared}
        if declared:
            result.findings.append(
                "F4 declared but not measured: re-run with --loadouts to "
                "evaluate the choice lattice"
            )
        else:
            result.findings.append(
                "F4 not declared: this level has no funChoiceSpace/funChoice/"
                "funBlocker facts, so there is no choice lattice to measure "
                "(see docs/FUN_METRICS.md section 3)"
            )
        return result

    if lattice.get("error"):
        result.verdict = SKIP
        result.metrics = {"declared": True, "error": lattice["error"]}
        result.findings.append(f"choice space declared but unusable: {lattice['error']}")
        return result

    result.metrics = {
        "declared": True,
        "space": lattice.get("space"),
        "pick": lattice.get("pick"),
        "choices": lattice.get("choices"),
        "blockers": lattice.get("blockers"),
        "loadouts_evaluated": lattice.get("loadouts_evaluated"),
        "loadouts_total": lattice.get("loadouts_total"),
        "sampled": lattice.get("sampled", False),
        "encounter_goal": lattice.get("encounter_goal"),
        "loadout_feasibility": lattice.get("loadout_feasibility"),
        "loadout_feasibility_independent": lattice.get("loadout_feasibility_independent"),
        "winning_loadout_count": lattice.get("winning_loadout_count"),
        "winning_loadouts": lattice.get("winning_loadouts"),
        "winning_loadouts_independent": lattice.get("winning_loadouts_independent"),
        "shared_resource_loadouts": lattice.get("shared_resource_loadouts"),
        "minimal_cover_count": lattice.get("minimal_cover_count"),
        "multi_use_factor": lattice.get("multi_use_factor"),
        "mandatory_choices": lattice.get("mandatory_choices"),
        "dead_choices": lattice.get("dead_choices"),
        "near_miss_count": lattice.get("near_miss_count"),
        "unknown_probes": lattice.get("unknown_probes", 0),
    }

    if lattice.get("sampled"):
        result.flag(
            WARN,
            f"sampled {lattice.get('subsets_evaluated')} of "
            f"{lattice.get('subsets_total')} subsets "
            f"({lattice.get('loadouts_evaluated')} of {lattice.get('loadouts_total')} "
            f"full loadouts; cap max_loadouts) - feasibility and multi-use are "
            f"estimates, not counts",
        )

    if lattice.get("unknown_probes"):
        result.flag(
            WARN,
            f"{lattice.get('unknown_probes')} loadout probe(s) could not finish - "
            f"those loadouts are counted as neither winners nor losers",
        )

    shared = lattice.get("shared_resource_loadouts") or []
    if shared:
        result.flag(
            WARN,
            f"{len(shared)} loadout(s) win every blocker taken alone but not the "
            f"encounter (e.g. {', '.join(shared[0])}) - a resource is shared "
            f"across blockers; the bands judge the encounter number",
        )

    feasibility = lattice.get("loadout_feasibility")
    low = cfg.band("f4_choice.loadout_feasibility_min", 0.05)
    high = cfg.band("f4_choice.loadout_feasibility_max", 0.4)
    saturated = cfg.band("f4_choice.feasibility_saturated_at", 0.95)
    unsatisfiable = cfg.band("f4_choice.feasibility_unsatisfiable_below", 0.001)
    if feasibility is None:
        result.flag(WARN, "loadout feasibility could not be computed")
    elif feasibility >= saturated:
        result.flag(
            FAIL,
            f"loadout feasibility {feasibility:.0%} - almost any pick wins, so "
            f"there is no scarcity and therefore no choice",
        )
    elif feasibility <= unsatisfiable:
        result.flag(
            FAIL,
            "no loadout clears the encounter - the choice space is unsatisfiable",
        )
    elif feasibility > high:
        result.flag(
            WARN,
            f"loadout feasibility {feasibility:.0%} above {high:.0%} - too forgiving",
        )
    elif feasibility < low:
        result.flag(
            WARN,
            f"loadout feasibility {feasibility:.0%} below {low:.0%} - brittle; "
            f"the player must find one exact answer",
        )

    multi_use = lattice.get("multi_use_factor")
    want_multi = cfg.band("f4_choice.multi_use_factor_min", 1.5)
    if multi_use is not None and multi_use < want_multi:
        result.flag(
            WARN,
            f"multi-use factor {multi_use:.2f} (want >= {want_multi}) - each pick "
            f"solves about one blocker, so this is a matching exercise, not a puzzle",
        )

    mandatory = lattice.get("mandatory_choices") or []
    pick = lattice.get("pick") or 0
    if pick and len(mandatory) >= pick:
        result.flag(
            FAIL,
            f"all {pick} picks are mandatory ({', '.join(mandatory)}) - that is a "
            f"tax the player pays, not a choice they make",
        )
    elif mandatory:
        result.flag(
            WARN,
            f"{len(mandatory)} of {pick} picks are forced: {', '.join(mandatory)}",
        )

    # Dead choices are capped, never required: an option that is useful
    # somewhere can still take judgement to pick, and rewarding red herrings
    # would push authors toward padding the kit.
    dead = lattice.get("dead_choices") or []
    choices = lattice.get("choices") or []
    if choices:
        dead_ratio = len(dead) / len(choices)
        result.metrics["dead_choice_ratio"] = round(dead_ratio, 2)
        cap = cfg.band("f4_choice.dead_choice_ratio_max", 0.4)
        if dead_ratio > cap:
            result.flag(
                WARN,
                f"{dead_ratio:.0%} of choices are dead (> {cap:.0%}): "
                f"{', '.join(dead)} - that is noise, not misdirection",
            )

    near_misses = lattice.get("near_miss_count")
    want_near = cfg.band("f4_choice.near_miss_count_min", 1)
    if near_misses is not None and near_misses < want_near:
        result.flag(
            WARN,
            "no near-miss loadouts - a wrong attempt gives the player no sense of "
            "being close",
        )
    return result


# ==========================================================================
# F5 - Discovery difficulty
# ==========================================================================

def f5_discovery(
    space: PlanSpace, classes: Sequence[StrategyClass], cfg: Config,
    graphs: Optional[Dict[int, CausalGraph]] = None,
) -> FamilyResult:
    result = FamilyResult(
        key="f5_discovery",
        title="Discovery difficulty - is it a puzzle to find?",
        encodes="fun to solve (weakest family - proxies, expect to iterate)",
    )
    breadth = decision_breadth(space)
    herrings, entities = red_herrings(space)
    graphs = graphs if graphs is not None else causal_graphs(space)

    class_insight = [
        graphs[c.representative.index].insight_depth
        for c in classes
        if c.representative is not None and c.representative.index in graphs
    ]
    insight = min(class_insight) if class_insight else 0

    lengths = [p.length for p in space.plans] or [1]
    steps = space.resolution_steps
    search_cost = (
        round(steps / statistics.median(lengths), 1) if steps and steps > 0 else None
    )
    herring_ratio = (len(herrings) / len(entities)) if entities else 0.0

    result.metrics = {
        "decision_breadth": round(breadth, 2),
        "insight_depth": insight,
        "insight_depth_per_class": class_insight,
        "search_cost": search_cost if search_cost is not None else "unavailable",
        "resolution_steps": steps,
        "red_herring_ratio": round(herring_ratio, 2),
        "red_herrings": sorted(herrings)[:20],
        "world_entities": len(entities),
        "planner_dead_ends": sum(p.dead_end_nodes for p in space.plans),
        "planner_nodes_explored": sum(p.explored_nodes for p in space.plans),
    }

    want_breadth = cfg.band("f5_discovery.decision_breadth_min", 2.0)
    if breadth < want_breadth:
        result.flag(
            WARN,
            f"decision breadth {breadth:.2f} (want >= {want_breadth}) - most tasks "
            f"have a single applicable method, so there is nothing to choose between",
        )

    want_insight = cfg.band("f5_discovery.insight_depth_min", 1)
    if insight < want_insight:
        result.flag(
            WARN,
            f"insight depth {insight} (want >= {want_insight}) - at least one class "
            f"is solvable greedily, with no move that only pays off later",
        )

    # Scenery is capped, not required: red herrings are a tool the author may
    # reach for, and a scorecard that demanded them would reward noise.
    high = cfg.band("f5_discovery.red_herring_ratio_max", 0.6)
    if herring_ratio > high:
        result.flag(
            WARN,
            f"red-herring ratio {herring_ratio:.0%} above {high:.0%} - most of the "
            f"world is inert scenery",
        )

    if search_cost is None:
        result.findings.append(
            "search_cost unavailable: the planner reported no resolution-step count "
            "for this run (FindAllPlans does not update the Prolog step counter)"
        )
    return result


def decision_breadth(space: PlanSpace) -> float:
    """Mean method alternatives per task actually encountered in plans.

    Static: counts how many rules define each task signature, averaged over
    the signatures that appear on some plan's decomposition path. Restricting
    to encountered tasks avoids rewarding a library full of methods the level
    never reaches.
    """
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

    encountered: Set[str] = set()
    for plan in space.plans:
        for node in plan.path:
            if node.get("isOperator"):
                continue
            if not node.get("methodSignature"):
                continue
            encountered.add(task_signature(node.get("taskName", "")))

    counts = [alternatives.get(sig, 1) for sig in encountered]
    return sum(counts) / len(counts) if counts else 0.0


def red_herrings(space: PlanSpace):
    """World entities that appear in no plan, and the full entity set.

    Entities are the atomic arguments of the level's own facts - the nouns the
    author put in the world.

    Two exclusions. `fun*` bookkeeping facts themselves never contribute, and
    neither do the atoms those facts *declare* - the tools and blockers of the
    choice space. Those belong to F4's world, are measured there by
    `dead_choices`, and would otherwise be counted twice: once as a designed
    choice and again as inert scenery, since the main goal does not touch them.
    """
    declared: Set[str] = set()
    for fact in space.facts_used:
        open_idx = fact.find("(")
        if open_idx < 0 or not fact[:open_idx].startswith("fun"):
            continue
        inner = fact[open_idx + 1: fact.rfind(")")]
        for token in _top_level_args(inner):
            if "(" not in token:
                declared.add(token)

    entities: Set[str] = set()
    for fact in space.facts_used:
        open_idx = fact.find("(")
        if open_idx < 0:
            continue
        if fact[:open_idx].startswith("fun"):
            continue
        inner = fact[open_idx + 1: fact.rfind(")")]
        for token in _top_level_args(inner):
            if token and "(" not in token and not token.startswith("?"):
                entities.add(token)
    entities -= declared

    used: Set[str] = set()
    for plan in space.plans:
        for op in plan.operators:
            used.update(op.args)
    return entities - used, entities


def _top_level_args(inner: str) -> List[str]:
    """Split an argument list on commas at depth 0."""
    parts: List[str] = []
    depth = 0
    buf: List[str] = []
    for ch in inner:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


# ==========================================================================
# F6 - Cooperation: does any one companion carry the plan alone?
# ==========================================================================

def f6_player(
    space: PlanSpace,
    cfg: Config,
    ablation: Optional[Dict[str, Any]] = None,
    graphs: Optional[Dict[int, CausalGraph]] = None,
    convention: Optional[ActorConvention] = None,
    trie: Optional[PlanTrie] = None,
) -> FamilyResult:
    """Cooperation, not human presence.

    The player character and the AI companions are all companions with the
    same abilities; they differ only by who controls them. The pillar (GDD 2
    and 3.6) is that no single companion carries a plan alone, whoever
    controls it: `single_actor_plans`, the family's only hard fail. Two
    companions finishing a plan while the controlled companion stands idle
    is acceptable by design; `soloable_plans`, `player_load` and the
    decision points describe that seat and are warnings at most. They say
    which companion the human should be, or that the seat needs a role,
    never that cooperation failed. Both counts are taken over consequential
    operators only: an operator that changes the world and is not declared
    `funNoop`, with its actor read from the first argument by convention or
    the index a `funActor` fact names. Being named as the target of someone
    else's operator is passive involvement and is reported apart. Teamwork
    is read off the causal graph as edges between operators of different
    actors, and the player's decisions are the trie's forks among the
    controlled companion's actions.
    """
    result = FamilyResult(
        key="f6_player",
        title="Cooperation - does any one companion carry the plan alone?",
        encodes="GDD 2 + 3.6: no single companion carries a plan alone, whoever controls it; the seat metrics describe the controlled companion's part",
    )
    player = cfg.player_atom
    if not space.plans:
        result.flag(FAIL, "no plans to measure")
        return result

    conv = convention or ActorConvention.from_space(space, cfg)
    graphs = graphs if graphs is not None else causal_graphs(space)
    trie = trie or PlanTrie(space, conv)

    soloable: List[int] = []
    single_actor: List[int] = []
    total_ops = 0
    consequential_total = 0
    player_actions = 0
    passive = 0
    teamwork_ratios: List[float] = []
    causal_out_ratios: List[float] = []

    for plan in space.plans:
        ops = plan.operators
        consequential = [op for op in ops if conv.is_consequential(op)]
        actions = [op for op in consequential if conv.actor_of(op) == player]
        total_ops += len(ops)
        consequential_total += len(consequential)
        player_actions += len(actions)
        passive += sum(1 for op in ops if conv.is_passive_mention(op))
        if not actions:
            soloable.append(plan.index)
        actors = {conv.actor_of(op) for op in consequential} - {None}
        if consequential and len(actors) == 1:
            single_actor.append(plan.index)

        graph = graphs.get(plan.index)
        if graph is None:
            continue
        if graph.edges:
            mixed = sum(
                1 for a, b in graph.edges
                if conv.actor_of(ops[a]) != conv.actor_of(ops[b])
            )
            teamwork_ratios.append(mixed / len(graph.edges))
        action_idx = [i for i, op in enumerate(ops) if conv.is_player_action(op)]
        if action_idx:
            feeding = sum(1 for i in action_idx if graph.successors(i))
            causal_out_ratios.append(feeding / len(action_idx))

    load = player_actions / consequential_total if consequential_total else 0.0
    passive_ratio = passive / total_ops if total_ops else 0.0
    teamwork = (
        sum(teamwork_ratios) / len(teamwork_ratios) if teamwork_ratios else 0.0
    )
    causal_out = (
        sum(causal_out_ratios) / len(causal_out_ratios) if causal_out_ratios else 0.0
    )
    decision_points = trie.player_decision_points()

    result.metrics = {
        "player_atom": player,
        "actor_position": conv.position,
        "actor_overrides": dict(conv.overrides),
        "noop_operators": sorted(conv.noops),
        "consequential_operators": consequential_total,
        "single_actor_plans": len(single_actor),
        "single_actor_plan_indices": single_actor[:20],
        "soloable_plans": len(soloable),
        "soloable_plan_indices": soloable[:20],
        "player_load": round(load, 2),
        "passive_involvement": round(passive_ratio, 2),
        "teamwork_edge_ratio": round(teamwork, 2),
        "player_causal_out": round(causal_out, 2),
        "player_decision_points": decision_points,
    }

    single_max = cfg.band("f6_player.single_actor_plans_max", 0)
    if len(single_actor) > single_max:
        result.flag(
            FAIL,
            f"{len(single_actor)} of {space.plan_count} plans are carried by one "
            f"companion alone - mandatory cooperation (GDD 2) is violated, whoever "
            f"controls that companion",
        )

    soloable_max = cfg.band("f6_player.soloable_plans_max", 0)
    if len(soloable) > soloable_max:
        result.flag(
            WARN,
            f"{len(soloable)} of {space.plan_count} plans contain no consequential "
            f"action by the controlled companion - the other companions finish those "
            f"while the human's seat is idle; a seat diagnostic (hand the human another "
            f"companion, or give the encounter a role this kit fills), not a "
            f"cooperation failure",
        )

    low = cfg.band("f6_player.player_load_min", 0.2)
    high = cfg.band("f6_player.player_load_max", 0.6)
    if load < low:
        result.flag(
            WARN,
            f"player load {load:.0%} below {low:.0%} - the player is a spectator"
            + (
                f" (passive involvement {passive_ratio:.0%}: named, not acting)"
                if passive_ratio > 0 else ""
            ),
        )
    elif load > high:
        result.flag(
            WARN,
            f"player load {load:.0%} above {high:.0%} - the player is "
            f"micromanaging, not conducting",
        )

    want_teamwork = cfg.band("f6_player.teamwork_edge_ratio_min", 0.2)
    if teamwork_ratios and teamwork < want_teamwork:
        result.flag(
            WARN,
            f"teamwork edge ratio {teamwork:.0%} (want >= {want_teamwork:.0%}) - "
            f"operators feed operators of the same actor; nobody sets up anyone else",
        )

    want_decisions = cfg.band("f6_player.player_decision_points_min", 1)
    if decision_points < want_decisions:
        result.flag(
            WARN,
            f"{decision_points} player decision point(s) (want >= {want_decisions}) - "
            f"the plans never fork on a player action, so the player's part is a "
            f"fixed step, not a choice",
        )

    if ablation is not None:
        critical = ablation.get("player_critical")
        result.metrics["player_criticality"] = critical
        if critical is False:
            result.flag(
                WARN,
                "removing every fact that mentions the player still leaves plans - "
                "the controlled companion's seat is not structurally required "
                "(a seat diagnostic, not the pillar)",
            )
    return result


def compute_all(
    space: PlanSpace,
    cfg: Config,
    ablation: Optional[Dict[str, Any]] = None,
    lattice: Optional[Dict[str, Any]] = None,
) -> List[FamilyResult]:
    """Run every family. Classes, causal graphs, the actor convention and the
    plan trie are computed once and shared."""
    classes = classify(space, cfg.fingerprint_layers, cfg.fingerprint_max_depth)
    graphs = causal_graphs(space)
    convention = ActorConvention.from_space(space, cfg)
    trie = PlanTrie(space, convention)
    return [
        f1_multiplicity(space, classes, cfg, lattice),
        f2_distinctness(space, classes, cfg, ablation),
        f3_depth(space, classes, cfg, graphs),
        f4_choice(space, cfg, lattice),
        f5_discovery(space, classes, cfg, graphs),
        f6_player(space, cfg, ablation, graphs, convention, trie),
    ]
