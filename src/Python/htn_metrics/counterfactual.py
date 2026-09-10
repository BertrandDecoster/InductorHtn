"""Perturb the world, re-plan, see what survives.

Two policies over one cache:

  - **ablation** - remove one fact at a time. Which strategy classes die tells
    us each class's *critical facts*; a fact that kills every class is a
    shared linchpin, and three strategies that all die to one fact were never
    three strategies (F2). Removing every player fact answers whether the
    player is structurally required (F6).

  - **loadout enumeration** - the X-of-Y lattice the level declares as facts.
    Strip every choice's facts from the world, add back only the selected
    ones, and ask whether the *encounter* - the level's own goal, with state
    persisting from one blocker to the next - is still solvable (F4). Each
    blocker is also probed on its own, from a fresh world, as a diagnostic:
    it says which blocker a losing loadout failed, and it exposes the loadouts
    that win every fight taken alone but not the level, which is the signature
    of a resource shared across blockers.

Every probe is a full planner build and `FindAllPlans`, so results are cached
on disk. The cache identity (`world_hash`) covers everything that could change
a probe's answer: the level source, the text of every dependency, the
fingerprint configuration, and the extractor version. A probe that could not
finish - out of memory, plan cap hit, compile error - is `unknown`, and no
conclusion that needs an exhaustive search is drawn from it. Caps are
enforced and **reported**: a sampled result is labelled as an estimate.
"""

import hashlib
import itertools
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .canonical import classify
from .config import Config
from .extract import (
    EXTRACTOR_VERSION,
    PROJECT_ROOT,
    ExtractError,
    LevelPlanner,
    LevelSpec,
    extract_plan_space,
    normalize_fact,
)

CACHE_DIRNAME = ".htn_metrics_cache"
CACHE_VERSION = 2

SOLVABLE, UNSOLVABLE, UNKNOWN = "solvable", "unsolvable", "unknown"

Fingerprint = Tuple[str, ...]


@dataclass
class ProbeResult:
    """What one perturbed planning run tells us.

    `status` is tri-state. `unknown` means the search did not finish (memory
    budget, plan cap, or a world that would not compile) and `error` says
    why. An unknown probe may still carry a positive `plan_count` - a plan
    was found before the cap - which is enough to call a loadout a winner but
    not enough to say which classes survived.
    """

    plan_count: int
    fingerprints: List[List[str]] = field(default_factory=list)
    status: str = UNSOLVABLE
    error: str = ""

    @property
    def solvable(self) -> bool:
        return self.status == SOLVABLE

    @property
    def conclusive(self) -> bool:
        return self.status != UNKNOWN

    @property
    def known_solvable(self) -> bool:
        """A plan exists - true even when the class set is incomplete."""
        return self.plan_count > 0

    def fingerprint_set(self) -> Set[Fingerprint]:
        return {tuple(fp) for fp in self.fingerprints}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_count": self.plan_count,
            "fingerprints": [list(fp) for fp in self.fingerprints],
            "status": self.status,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProbeResult":
        return cls(
            plan_count=int(data.get("plan_count", 0)),
            fingerprints=[list(fp) for fp in data.get("fingerprints", [])],
            status=str(data.get("status", UNSOLVABLE)),
            error=str(data.get("error", "")),
        )


# ==========================================================================
# Cache identity
# ==========================================================================

def dependency_sources(spec: LevelSpec, project_root: str = PROJECT_ROOT) -> List[Tuple[str, str]]:
    """The (component, source text) of every transitive dependency, in load
    order. Read through the same loader that compiles them, so the identity
    tracks exactly what the planner would see."""
    py_dir = os.path.join(project_root, "src", "Python")
    if py_dir not in sys.path:
        sys.path.insert(0, py_dir)
    from htn_components.loader import ComponentLoader, LoadError  # type: ignore

    loader = ComponentLoader(None, project_root, warn=lambda _m: None)
    try:
        return loader.resolve_sources(list(spec.dependencies))
    except LoadError as exc:
        # An unresolvable dependency still changes the answer; hash the error.
        return [("<unresolved>", str(exc))]


def world_hash(spec: LevelSpec, cfg: Config, project_root: str = PROJECT_ROOT) -> str:
    """Everything a cached probe's answer depends on, in one hash.

    Level source, dependency sources, the fingerprint configuration (which
    decides what class identities a probe records), the actor convention,
    and the extractor/cache versions.
    """
    payload = json.dumps(
        {
            "level": spec.source_hash(),
            "deps": dependency_sources(spec, project_root),
            "fingerprint_layers": list(cfg.fingerprint_layers),
            "fingerprint_max_depth": cfg.fingerprint_max_depth,
            "actor_position": cfg.get("actor_position", 0),
            "extractor": EXTRACTOR_VERSION,
            "cache": CACHE_VERSION,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ==========================================================================
# The harness
# ==========================================================================

class CounterfactualHarness:
    """Runs and caches perturbed planning probes for one level."""

    def __init__(
        self,
        spec: LevelSpec,
        cfg: Config,
        cache_dir: Optional[str] = None,
        project_root: str = PROJECT_ROOT,
    ):
        self.spec = spec
        self.cfg = cfg
        self._probes = 0
        self._cache_hits = 0
        self._dirty = False
        self.identity = world_hash(spec, cfg, project_root)

        self._cache_dir = cache_dir or os.path.join(project_root, CACHE_DIRNAME)
        self._cache_path = os.path.join(
            self._cache_dir, f"{spec.level_id}-{self.identity}.json"
        )
        self._cache: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._cache = {}

    # ------------------------------------------------------------- probing

    def probe(self, facts: Sequence[str], goal: Optional[str] = None) -> ProbeResult:
        """Plan with `facts` as the world, returning a small summary.

        Only the summary is cached - plan objects are large and nothing
        downstream needs them.
        """
        key = self._key(facts, goal)
        cached = self._cache.get(key)
        if cached is not None:
            self._cache_hits += 1
            return ProbeResult.from_dict(cached)

        self._probes += 1
        try:
            space = extract_plan_space(
                self.spec.path,
                goal=goal,
                facts=list(facts),
                spec=self.spec,
                max_plans=self.cfg.cap("max_plans", 5000),
                memory_budget=self.cfg.cap("memory_budget_bytes", 0) or 0,
            )
        except ExtractError as exc:
            # A world that will not compile, or that has no goal, is not an
            # unsolvable world - it is a probe that could not run.
            result = ProbeResult(plan_count=0, status=UNKNOWN, error=str(exc))
        else:
            classes = classify(
                space, self.cfg.fingerprint_layers, self.cfg.fingerprint_max_depth
            )
            fingerprints = [list(c.fingerprint) for c in classes]
            if space.truncated:
                status, error = UNKNOWN, space.truncation_reason
            elif space.plan_count > 0:
                status, error = SOLVABLE, ""
            else:
                status, error = UNSOLVABLE, ""
            result = ProbeResult(
                plan_count=space.plan_count, fingerprints=fingerprints,
                status=status, error=error,
            )

        self._cache[key] = result.to_dict()
        self._dirty = True
        return result

    def _key(self, facts: Sequence[str], goal: Optional[str]) -> str:
        payload = json.dumps(
            {"w": self.identity, "f": sorted(facts), "g": goal or ""},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # --------------------------------------------------------- bookkeeping

    @property
    def stats(self) -> Dict[str, int]:
        return {"probes_run": self._probes, "cache_hits": self._cache_hits}

    def close(self) -> None:
        """Flush the cache to disk."""
        if not self._dirty:
            return
        try:
            os.makedirs(self._cache_dir, exist_ok=True)
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except OSError:
            pass
        self._dirty = False


# ==========================================================================
# Ablation (F2 independence, F6 player criticality)
# ==========================================================================

def _fact_mentions(fact: str, atom: str) -> bool:
    """True when `atom` appears as an argument of `fact`."""
    open_idx = fact.find("(")
    if open_idx < 0:
        return False
    inner = fact[open_idx + 1: fact.rfind(")")]
    return any(part.strip() == atom for part in _split_args(inner))


def _split_args(inner: str) -> List[str]:
    """Split an argument list on top-level commas."""
    parts: List[str] = []
    depth = 0
    buf: List[str] = []
    for ch in inner:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _goal_atoms(goal: str) -> Set[str]:
    """The constants named in a goal term: `planToDamage(gob)` -> `{gob}`."""
    open_idx = goal.find("(")
    if open_idx < 0:
        return set()
    inner = goal[open_idx + 1: goal.rfind(")")]
    return {
        part for part in _split_args(inner)
        if part and "(" not in part and not part.startswith("?")
    }


def _mentions_any(fact: str, atoms: Set[str]) -> bool:
    return any(_fact_mentions(fact, atom) for atom in atoms)


def _is_bookkeeping(fact: str) -> bool:
    """`fun*` facts declare the metrics' own inputs; they are never world."""
    open_idx = fact.find("(")
    functor = fact if open_idx < 0 else fact[:open_idx]
    return functor.startswith("fun")


def _declared_choice_facts(space) -> Set[str]:
    """The facts a level's `funChoiceFact` declarations control.

    They belong to F4's world: their criticality is what `mandatory_choices`
    and `dead_choices` measure. Ablating them here would report the default
    kit as a shared linchpin of every route.
    """
    out: Set[str] = set()
    for fact in space.facts_used:
        if not fact.startswith("funChoiceFact("):
            continue
        inner = fact[fact.find("(") + 1: fact.rfind(")")]
        args = _split_args(inner)
        if len(args) >= 2:
            out.add(normalize_fact(args[1]))
    return out


def _split_gates(
    harness, space, cfg: Config, linchpins: List[str], unknown: List[Tuple[str, str]]
) -> Tuple[List[str], List[str]]:
    """Partition linchpins into (gates, true linchpins).

    A linchpin is a *gate* when removing it also makes one of the level's
    declared blocker goals (`funBlockerGoal`) unsolvable: every route died
    because the breach died, and every route passes through the breach. A
    level that declares no blockers has no gates - a fact every strategy
    needs is then exactly what it looks like.
    """
    spec = getattr(harness, "spec", None)
    if spec is None:
        return [], list(linchpins)
    try:
        choice_space = read_choice_space(spec, cfg)
    except ExtractError:
        choice_space = None
    if choice_space is None or not choice_space.blockers:
        return [], list(linchpins)

    gates: List[str] = []
    true_linchpins: List[str] = []
    for fact in linchpins:
        remaining = [f for f in space.facts_used if f != fact]
        gated = False
        for blocker in choice_space.blockers:
            result = harness.probe(remaining, goal=choice_space.blocker_goals[blocker])
            if not result.conclusive:
                unknown.append((f"{fact} / {blocker}", result.error))
                continue
            if not result.solvable:
                gated = True
                break
        (gates if gated else true_linchpins).append(fact)
    return gates, true_linchpins


def run_ablation(harness: CounterfactualHarness, space, cfg: Config) -> Dict[str, Any]:
    """Remove each fact in turn; report which classes each fact keeps alive.

    A fact is *critical* for a class when the class disappears without it. Two
    classes with disjoint critical sets are genuinely independent routes; a
    fact critical for every class is a shared linchpin - or, when the classes
    are independent elsewhere, a shared *gate* that every route passes through
    before diverging. Classes are matched by fingerprint, never by label:
    labels are reassigned when class sizes shift under perturbation.

    Probes that could not finish are counted, reported, and excluded. When
    any probe is unknown the sweep is `conclusive: False`, and the absence of
    a linchpin or the independence of a pair is not claimed.
    """
    baseline = classify(space, cfg.fingerprint_layers, cfg.fingerprint_max_depth)
    label_of: Dict[Fingerprint, str] = {c.fingerprint: c.label for c in baseline}
    baseline_fps: Set[Fingerprint] = set(label_of)

    choice_facts = _declared_choice_facts(space)
    candidates = [
        f for f in space.facts_used
        if not _is_bookkeeping(f) and f not in choice_facts
    ]
    facts_total = len(candidates)

    # Facts that name the goal's own target are load-bearing for every plan by
    # construction - delete `enemy(gob)` and there is nothing to plan against.
    # They are tracked but never counted as a design flaw, and they are
    # excluded when comparing classes, since a shared target is shared by
    # definition and would otherwise mask genuine independence.
    goal_atoms = _goal_atoms(space.goal)

    cap = cfg.cap("max_ablation_facts", 120)
    sampled = False
    facts = candidates
    if len(facts) > cap:
        stride = max(1, len(facts) // cap)
        facts = facts[::stride][:cap]
        sampled = True

    critical: Dict[str, List[str]] = {label: [] for label in label_of.values()}
    linchpins: List[str] = []
    goal_target_linchpins: List[str] = []
    dead_facts: List[str] = []
    unknown: List[Tuple[str, str]] = []

    for fact in facts:
        remaining = [f for f in space.facts_used if f != fact]
        result = harness.probe(remaining)
        if not result.conclusive:
            unknown.append((fact, result.error))
            continue
        survivors = result.fingerprint_set()
        for fp in baseline_fps - survivors:
            critical.setdefault(label_of[fp], []).append(fact)
        if not result.solvable:
            dead_facts.append(fact)
        if baseline_fps and not survivors & baseline_fps:
            if _mentions_any(fact, goal_atoms):
                goal_target_linchpins.append(fact)
            else:
                linchpins.append(fact)

    # A fact every route needs *because the declared blockers need it* is a
    # gate the routes all pass through - the breach before the heist - not one
    # idea under three names. It is reported as infrastructure and set aside
    # when judging whether the routes are independent of each other.
    shared_gates: List[str] = []
    if linchpins:
        shared_gates, linchpins = _split_gates(harness, space, cfg, linchpins, unknown)
    gate_set = set(shared_gates)

    # Independence is judged on the facts that *distinguish* classes.
    distinguishing = {
        label: [
            f for f in items
            if not _mentions_any(f, goal_atoms) and f not in gate_set
        ]
        for label, items in critical.items()
    }
    independent_pairs = 0
    labels = sorted(distinguishing)
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            set_a, set_b = set(distinguishing[labels[i]]), set(distinguishing[labels[j]])
            if set_a and set_b and not (set_a & set_b):
                independent_pairs += 1

    player = cfg.player_atom
    player_facts = [f for f in space.facts_used if _fact_mentions(f, player)]
    player_critical: Optional[bool] = None
    if player_facts:
        without_player = [f for f in space.facts_used if f not in set(player_facts)]
        probe = harness.probe(without_player)
        if probe.conclusive:
            player_critical = not probe.solvable
        else:
            unknown.append(("<all player facts>", probe.error))

    return {
        "facts_tested": len(facts),
        "facts_total": facts_total,
        "choice_facts_skipped": len(choice_facts),
        "sampled": sampled,
        "conclusive": not unknown,
        "unknown_probes": len(unknown),
        "unknown_reasons": unknown[:5],
        "critical_facts": {k: v for k, v in critical.items() if v},
        "distinguishing_critical_facts": {k: v for k, v in distinguishing.items() if v},
        "linchpins": linchpins,
        "shared_gates": shared_gates,
        "goal_target_linchpins": goal_target_linchpins,
        "unsolvable_without": dead_facts,
        "independent_pairs": independent_pairs,
        "player_critical": player_critical,
        "player_facts_removed": len(player_facts),
        "probe_stats": harness.stats,
    }


# ==========================================================================
# The declared X-of-Y choice space (F4)
# ==========================================================================

def _query_all(planner, query: str, variables: Sequence[str]) -> List[Tuple[str, ...]]:
    """Run a Prolog query and return bindings for `variables`, in that order.

    Bindings must be looked up **by name**: the planner returns each solution
    as a dict whose key order does not follow the order the variables appear
    in the query, so reading `.values()` positionally silently transposes
    arguments.

    Returns [] when the predicate is undeclared, which is the normal case for
    levels that do not opt into F4.
    """
    from .extract import _import_planner

    _, term_to_string = _import_planner()
    error, result = planner.PrologQuery(query)
    if error or not result:
        return []
    try:
        solutions = json.loads(result)
    except json.JSONDecodeError:
        return []
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []

    out: List[Tuple[str, ...]] = []
    for solution in solutions:
        if not isinstance(solution, dict):
            continue
        if not all(name in solution for name in variables):
            continue
        out.append(
            tuple(normalize_fact(term_to_string(solution[name])) for name in variables)
        )
    return out


@dataclass
class ChoiceSpace:
    """A level's declared X-of-Y lattice. Blockers keep their declared order,
    which is the order the encounter meets them."""

    name: str
    pick: int
    choices: List[str]
    choice_facts: Dict[str, List[str]]
    blockers: List[str]
    blocker_goals: Dict[str, str]


def read_choice_space(spec: LevelSpec, cfg: Config) -> Optional[ChoiceSpace]:
    """Read `funChoiceSpace` / `funChoice` / `funChoiceFact` / `funBlocker`.

    Returns None when the level declares nothing, so F4 can report "not
    declared" rather than a misleading zero.
    """
    planner, _loader = LevelPlanner(spec).build()

    spaces = _query_all(planner, "funChoiceSpace(?space, ?pick).", ["?space", "?pick"])
    if not spaces:
        return None

    name, pick_text = spaces[0]
    try:
        pick = int(pick_text)
    except ValueError:
        raise ExtractError(
            f"funChoiceSpace({name}, {pick_text}) - the pick count must be an integer"
        )

    choices = [
        c for s, c in _query_all(planner, "funChoice(?s, ?c).", ["?s", "?c"])
        if s == name
    ]
    choice_facts: Dict[str, List[str]] = {c: [] for c in choices}
    for choice, fact in _query_all(planner, "funChoiceFact(?c, ?f).", ["?c", "?f"]):
        if choice in choice_facts:
            choice_facts[choice].append(fact)

    blockers = [b for (b,) in _query_all(planner, "funBlocker(?b).", ["?b"])]
    blocker_goals = {
        b: g for b, g in
        _query_all(planner, "funBlockerGoal(?b, ?g).", ["?b", "?g"])
    }

    # Fall back to the level's own goal shape: `planToDamage(gob)` for blocker
    # `gob` when the level declares goals(planToDamage(...)). An atomic goal
    # (`goals(breakOut)`) has no shape to borrow, so the blocker goal must be
    # declared.
    if spec.goals and "(" in spec.goals[0]:
        functor = spec.goals[0].split("(")[0]
        for blocker in blockers:
            blocker_goals.setdefault(blocker, f"{functor}({blocker})")
    missing = [b for b in blockers if b not in blocker_goals]
    if missing:
        raise ExtractError(
            "funBlockerGoal missing for " + ", ".join(missing)
            + " and the level goal has no argument shape to borrow"
        )

    return ChoiceSpace(
        name=name, pick=pick, choices=sorted(choices),
        choice_facts=choice_facts, blockers=blockers,
        blocker_goals=blocker_goals,
    )


def run_loadouts(harness: CounterfactualHarness, space, cfg: Config) -> Optional[Dict[str, Any]]:
    """Evaluate the declared choice lattice.

    Enumerates every subset of size <= pick (the smaller ones are needed to
    tell a *minimal* cover from a padded one, and to ask whether a choice is
    actually pulling its weight). A subset **wins** when the encounter - the
    level's own goal - is solvable with those picks and nothing else from the
    choice space. Each blocker is also probed alone from a fresh world; those
    answers explain a loss and expose loadouts that win every fight but not
    the level.
    """
    try:
        choice_space = read_choice_space(harness.spec, cfg)
    except ExtractError as exc:
        return {"error": str(exc)}
    if choice_space is None:
        return None
    if not choice_space.blockers:
        return {"error": "funChoiceSpace declared but no funBlocker facts"}
    if not choice_space.choices:
        return {"error": f"funChoiceSpace({choice_space.name}) has no funChoice facts"}
    if choice_space.pick > len(choice_space.choices):
        return {"error": (
            f"funChoiceSpace picks {choice_space.pick} but only "
            f"{len(choice_space.choices)} choices are declared"
        )}

    all_choice_facts: Set[str] = set()
    for facts in choice_space.choice_facts.values():
        all_choice_facts.update(facts)
    baseline = [f for f in space.facts_used if f not in all_choice_facts]

    pick = choice_space.pick
    choices = choice_space.choices
    blockers = choice_space.blockers
    exact = list(itertools.combinations(choices, pick))
    smaller: List[Tuple[str, ...]] = []
    for size in range(0, pick):
        smaller.extend(itertools.combinations(choices, size))
    total_exact, total_smaller = len(exact), len(smaller)

    # One encounter probe plus one probe per blocker, per subset.
    cap = cfg.cap("max_loadouts", 400)
    budget = max(1, cap // (1 + len(blockers)))
    if len(exact) + len(smaller) > budget:
        if budget > len(smaller):
            keep_exact = min(len(exact), max(1, budget - len(smaller)))
        else:
            keep_exact = min(len(exact), budget)
        if keep_exact < len(exact):
            stride = max(1, len(exact) // keep_exact)
            exact = exact[::stride][:keep_exact]
        smaller = smaller[: max(0, budget - len(exact))]
    sampled = len(exact) < total_exact or len(smaller) < total_smaller

    encounter: Dict[Tuple[str, ...], str] = {}       # win | lose | unknown
    solved: Dict[Tuple[str, ...], Set[str]] = {}     # blockers won alone
    ideas: Set[Fingerprint] = set()                   # classes across winning kits
    unknown_probes = 0
    for loadout in list(exact) + smaller:
        facts = list(baseline)
        for choice in loadout:
            facts.extend(choice_space.choice_facts.get(choice, []))

        whole = harness.probe(facts, goal=space.goal)
        if whole.known_solvable:
            encounter[loadout] = "win"
            if len(loadout) == pick:
                ideas |= whole.fingerprint_set()
        elif whole.conclusive:
            encounter[loadout] = "lose"
        else:
            encounter[loadout] = "unknown"
            unknown_probes += 1

        wins: Set[str] = set()
        for blocker in blockers:
            result = harness.probe(facts, goal=choice_space.blocker_goals[blocker])
            if result.known_solvable:
                wins.add(blocker)
            elif not result.conclusive:
                unknown_probes += 1
        solved[loadout] = wins

    blocker_set = set(blockers)
    winners = [lo for lo in exact if encounter.get(lo) == "win"]
    winners_independent = [lo for lo in exact if solved.get(lo, set()) == blocker_set]
    shared_resource = [lo for lo in winners_independent if encounter.get(lo) == "lose"]
    near_misses = [
        lo for lo in exact if len(blocker_set - solved.get(lo, set())) == 1
    ]

    all_winners = [lo for lo, verdict in encounter.items() if verdict == "win"]
    minimal_covers = [
        lo for lo in all_winners
        if not any(set(other) < set(lo) for other in all_winners)
    ]

    # A choice "addresses" a blocker when dropping it from some evaluated
    # loadout loses that blocker - i.e. the choice is doing the work, rather
    # than riding along with something else that also solves it.
    addressed: Dict[str, Set[str]] = {c: set() for c in choices}
    for loadout, wins in solved.items():
        for choice in loadout:
            without = tuple(c for c in loadout if c != choice)
            if without not in solved:
                continue
            addressed[choice] |= wins - solved[without]

    # Averaged over the choices that do something. Dead choices are measured
    # separately by `dead_choices`; letting them drag this mean down would
    # conflate "my picks are single-purpose" with "some picks are red
    # herrings", which are different design problems with different fixes.
    live = [v for v in addressed.values() if v]
    multi_use = sum(len(v) for v in live) / len(live) if live else 0.0

    used_in_wins: Set[str] = set()
    for loadout in winners:
        used_in_wins.update(loadout)
    mandatory = [
        c for c in choices if winners and all(c in lo for lo in winners)
    ]
    dead = [c for c in choices if c not in used_in_wins]

    return {
        "space": choice_space.name,
        "pick": pick,
        "choices": choices,
        "blockers": blockers,
        "encounter_goal": space.goal,
        "loadouts_evaluated": len(exact),
        "loadouts_total": total_exact,
        "subsets_evaluated": len(encounter),
        "subsets_total": total_exact + total_smaller,
        "sampled": sampled,
        "conclusive": unknown_probes == 0,
        "unknown_probes": unknown_probes,
        "loadout_feasibility": round(len(winners) / len(exact), 3) if exact else None,
        "loadout_feasibility_independent": (
            round(len(winners_independent) / len(exact), 3) if exact else None
        ),
        "winning_loadout_count": len(winners),
        "winning_loadouts": [list(lo) for lo in winners[:20]],
        "winning_loadout_count_independent": len(winners_independent),
        "winning_loadouts_independent": [list(lo) for lo in winners_independent[:20]],
        "shared_resource_loadouts": [list(lo) for lo in shared_resource[:20]],
        "strategy_classes_across_loadouts": len(ideas),
        "minimal_cover_count": len(minimal_covers),
        "minimal_covers": [list(lo) for lo in minimal_covers[:20]],
        "multi_use_factor": round(multi_use, 2),
        "choice_coverage": {c: sorted(v) for c, v in addressed.items()},
        "mandatory_choices": mandatory,
        "dead_choices": dead,
        "near_miss_count": len(near_misses),
        "probe_stats": harness.stats,
    }
