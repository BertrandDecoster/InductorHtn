"""Player-perspective play over a level's plan space.

A playtest, not an oracle. The planner has already enumerated every plan
for the level; this module lets a caller *walk* that space the way the
player would:

  - `observe()`   what the player can see - their region, their skills and
                  charges, where the companions and enemies are, and what
                  each companion says it is about to do. No strategy names.
  - `actions()`   the player's own legal next moves. Companion-only steps
                  are advanced first by the planner's preference (the
                  method order the author wrote), so the player is only
                  asked when there is something to decide. `wait` is offered
                  when a companion could act instead.
  - `act(a)`      take a move. Off-plan moves are refused unless `force=True`,
                  in which case the operator's grounded effects are applied
                  and the level is re-planned from the resulting world -
                  which is how a mistake becomes observable.
  - `undo()`      back to the previous decision.
  - `explain()`   afterwards: the strategy class reached, the ones missed,
                  and the planner's alternatives at every decision.

Every session writes a playthrough JSON so the design loop has a record of
what was offered and what was chosen.
"""

import datetime as _dt
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (os.path.join(PROJECT_ROOT, "src", "Python"),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from htn_metrics.agency import ActorConvention  # noqa: E402
from htn_metrics.canonical import classify  # noqa: E402
from htn_metrics.config import Config  # noqa: E402
from htn_metrics.extract import (  # noqa: E402
    ExtractError,
    OperatorInstance,
    PlanSpace,
    extract_plan_space,
    ground_solution,
    load_level_spec,
    normalize_fact,
    split_args,
)
from htn_metrics.narrate import (  # noqa: E402
    narrate_effects,
    narrate_fact,
    narrate_intention,
    narrate_operator,
    parse_term,
)
from htn_metrics.trie import FINISHED, Choice, PlanTrie  # noqa: E402

WAIT = "wait"
DEFAULT_PLAYTHROUGH_DIR = os.path.join(PROJECT_ROOT, ".playthroughs")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _term_dict(text: str) -> Dict[str, Any]:
    """`"opX(a, f(b))"` -> the planner's JSON term shape `{"opX": [{"a": []}, {"f": [{"b": []}]}]}`."""
    name, args = parse_term(text)
    return {name: [_term_dict(a) for a in args]}


def _fact_args(fact: str) -> Tuple[str, List[str]]:
    return parse_term(fact)


def _apply(facts: Set[str], op: OperatorInstance) -> Set[str]:
    out = set(facts)
    for fact in op.dels:
        out.discard(normalize_fact(fact))
    for fact in op.adds:
        out.add(normalize_fact(fact))
    return out


class _World:
    """One planned world: the plan space, its trie, its classes."""

    def __init__(self, space: PlanSpace, cfg: Config):
        self.space = space
        self.convention = ActorConvention.from_space(space, cfg)
        self.trie = PlanTrie(space, self.convention)
        self.classes = classify(space, cfg.fingerprint_layers, cfg.fingerprint_max_depth)
        self.class_of: Dict[int, str] = {}
        for cls in self.classes:
            for idx in cls.plan_indices:
                self.class_of[idx] = cls.label

    def labels(self, plan_indices: Sequence[int]) -> List[str]:
        seen: List[str] = []
        for idx in plan_indices:
            label = self.class_of.get(idx)
            if label and label not in seen:
                seen.append(label)
        return seen


# --------------------------------------------------------------------------
# The session
# --------------------------------------------------------------------------

class LevelSession:
    def __init__(
        self,
        level: str,
        cfg: Optional[Config] = None,
        playthrough_dir: Optional[str] = None,
    ):
        self.cfg = cfg or Config.load()
        self.spec = load_level_spec(level)
        self.level_id = self.spec.level_id
        self.player = self.cfg.player_atom

        space = self._plan(None)
        self.world = _World(space, self.cfg)
        self.goal = space.goal
        # The classes the level offered at the start. After a forced re-plan
        # the world may hold fewer (or none); "missed" is judged against these.
        self.origin_labels: List[str] = [c.label for c in self.world.classes]

        # The walk is global (every operator applied since the start); the
        # prefix is the walk's tail inside the *current* world's trie, which
        # restarts at () after a forced re-plan.
        self.prefix: Tuple[str, ...] = ()
        self.walk: List[OperatorInstance] = []
        self.facts: Set[str] = set(space.initial_facts)
        self.level_facts: Set[str] = {normalize_fact(f) for f in space.facts_used}
        self.replanned = False
        self.steps: List[Dict[str, Any]] = []
        self._undo: List[Dict[str, Any]] = []

        self._playthrough_dir = playthrough_dir or DEFAULT_PLAYTHROUGH_DIR
        stamp = _dt.datetime.now().strftime("%Y%m%dT%H%M%S_%f")
        self._playthrough_path = os.path.join(self._playthrough_dir, self.level_id, f"{stamp}.json")
        self.started = _dt.datetime.now().isoformat(timespec="seconds")

    # ------------------------------------------------------------ planning

    def _plan(self, facts: Optional[Sequence[str]]) -> PlanSpace:
        return extract_plan_space(
            self.spec.path,
            facts=list(facts) if facts is not None else None,
            spec=self.spec,
            max_plans=self.cfg.cap("max_plans", 5000),
            memory_budget=self.cfg.cap("memory_budget_bytes", 0) or 0,
        )

    # ----------------------------------------------------------- properties

    @property
    def step(self) -> int:
        return len(self.walk)

    @property
    def plans_remaining(self) -> int:
        return len(self.world.trie.surviving(self.prefix))

    @property
    def truncated(self) -> bool:
        return self.world.space.truncated

    def _children(self) -> Dict[str, Choice]:
        return self.world.trie.children(self.prefix)

    @property
    def done(self) -> bool:
        if self.plans_remaining == 0:
            return True
        self._advance()
        return FINISHED in self._children()

    # ------------------------------------------------------------ advancing

    def _advance(self) -> None:
        """Auto-play companion-only steps until the player has a say."""
        target = self.world.trie.auto_advance_companions(self.prefix)
        if target == self.prefix:
            return
        for text in target[len(self.prefix):]:
            op = self._children()[text].op
            assert op is not None
            self._take(op)

    def _take(self, op: OperatorInstance) -> None:
        self.prefix = self.prefix + (op.text,)
        self.walk.append(op)
        self.facts = _apply(self.facts, op)
        self.level_facts = _apply(self.level_facts, op)

    # ------------------------------------------------------------- the view

    def _facts_named(self, functor: str) -> List[List[str]]:
        out: List[List[str]] = []
        for fact in sorted(self.facts):
            name, args = _fact_args(fact)
            if name == functor:
                out.append(args)
        return out

    def _where(self, entity: str) -> Optional[str]:
        for args in self._facts_named("at"):
            if len(args) == 2 and args[0] == entity:
                return args[1]
        return None

    def _statuses(self, entity: str) -> List[str]:
        out: List[str] = []
        for functor in ("status", "hasTag"):
            for args in self._facts_named(functor):
                if len(args) == 2 and args[0] == entity:
                    out.append(args[1])
        return out

    def _cast(self, kind: str) -> List[str]:
        names = [args[0] for args in self._facts_named("role") if len(args) == 2 and args[1] == kind]
        if not names:
            legacy = {"companion": ("companion", "ally"), "enemy": ("isEnemy", "enemy")}
            for functor in legacy.get(kind, ()):
                names = [args[0] for args in self._facts_named(functor) if len(args) == 1]
                if names:
                    break
        return [n for n in names if n != self.player]

    def _next_companion_ops(self) -> Dict[str, List[Tuple[int, OperatorInstance]]]:
        """Per companion, the next operator it would take in each surviving
        plan - the intention it can state."""
        conv = self.world.convention
        out: Dict[str, List[Tuple[int, OperatorInstance]]] = {}
        depth = len(self.prefix)
        for idx in self.world.trie.surviving(self.prefix):
            plan = self.world.space.plans[idx]
            seen: Set[str] = set()
            for op in plan.operators[depth:]:
                actor = conv.actor_of(op)
                if actor is None or actor == self.player or actor in seen:
                    continue
                if not conv.is_consequential(op):
                    continue
                seen.add(actor)
                out.setdefault(actor, []).append((idx, op))
        return out

    def observe(self) -> Dict[str, Any]:
        """What the player sees. No plan counts, no strategy names."""
        intentions = self._next_companion_ops()
        companions = []
        for name in self._cast("companion"):
            options = sorted(intentions.get(name, []), key=lambda t: t[0])
            distinct: List[str] = []
            for _idx, op in options:
                line = narrate_intention(op.text, actor=name, dels=op.dels, adds=op.adds)
                if line not in distinct:
                    distinct.append(line)
            companions.append({
                "name": name,
                "location": self._where(name),
                "statuses": self._statuses(name),
                "intention": distinct[0] if distinct else None,
                "intentions": distinct,
            })
        enemies = [
            {"name": e, "location": self._where(e), "statuses": self._statuses(e)}
            for e in self._cast("enemy")
        ]
        regions: Dict[str, List[str]] = {}
        for args in self._facts_named("regionHas"):
            if len(args) == 2:
                regions.setdefault(args[0], []).append(args[1])
        for functor in ("roomHasHazard", "roomHasTag"):
            for args in self._facts_named(functor):
                if len(args) == 2:
                    regions.setdefault(args[0], []).append(args[1])

        skills = [a[1] for a in self._facts_named("hasSkill") if len(a) == 2 and a[0] == self.player]
        charges = [
            {"skill": a[1], "token": a[2]}
            for a in self._facts_named("charge") if len(a) == 3 and a[0] == self.player
        ]
        carrying = [a[1] for a in self._facts_named("carrying") if len(a) == 2 and a[0] == self.player]

        visible = [
            narrate_fact(f) for f in sorted(self.facts)
            if _fact_args(f)[0] in ("at", "status", "regionHas", "hasTag", "roomHasHazard",
                                    "roomHasTag", "cleared", "hasAggro")
        ]
        return {
            "level": self.level_id,
            "step": self.step,
            "you": self.player,
            "location": self._where(self.player),
            "statuses": self._statuses(self.player),
            "skills": skills,
            "charges": charges,
            "carrying": carrying,
            "companions": companions,
            "enemies": enemies,
            "regions": regions,
            "visible": visible,
            "done": self.done,
        }

    # -------------------------------------------------------------- actions

    def _lookup(self) -> Dict[str, Choice]:
        return {normalize_fact(text): c for text, c in self._children().items() if text != FINISHED}

    def actions(self) -> List[Dict[str, Any]]:
        """The player's own legal moves after the companions have had their turn."""
        if self.plans_remaining == 0:
            return []
        self._advance()
        children = self._children()
        player_choices = [
            c for c in children.values()
            if not c.finished and c.actor == self.player and c.consequential
        ]
        companion_choices = [
            c for c in children.values()
            if not c.finished and c.actor != self.player
        ]
        player_choices.sort(key=lambda c: c.preference)
        out: List[Dict[str, Any]] = []
        for choice in player_choices:
            op = choice.op
            assert op is not None
            out.append({
                "action": op.text,
                "actor": self.player,
                "narration": narrate_operator(op.text, dels=op.dels, adds=op.adds, actor=self.player),
                "consequences": narrate_effects(op.dels, op.adds),
            })
        if companion_choices and not (FINISHED in children and not player_choices):
            best = min(companion_choices, key=lambda c: c.preference)
            op = best.op
            assert op is not None
            out.append({
                "action": WAIT,
                "actor": self.player,
                "narration": "Let the companions act - "
                             + narrate_intention(op.text, actor=best.actor or "companion",
                                                 dels=op.dels, adds=op.adds),
                "consequences": narrate_effects(op.dels, op.adds),
            })
        return out

    def _alternatives(self, offered: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Where each offered action leads, in the planner's terms. Kept out
        of `actions()`; surfaced by `explain()`."""
        lookup = self._lookup()
        children = self._children()
        out: List[Dict[str, Any]] = []
        for item in offered:
            if item["action"] == WAIT:
                companion_choices = [
                    c for c in children.values() if not c.finished and c.actor != self.player
                ]
                if not companion_choices:
                    continue
                choice = min(companion_choices, key=lambda c: c.preference)
            else:
                choice = lookup.get(normalize_fact(item["action"]))
                if choice is None:
                    continue
            out.append({
                "action": item["action"],
                "leads_to": self.world.labels(choice.plan_indices),
                "plans": len(choice.plan_indices),
            })
        return out

    def _snapshot(self) -> Dict[str, Any]:
        return {
            "world": self.world, "prefix": self.prefix, "walk": list(self.walk),
            "facts": set(self.facts), "level_facts": set(self.level_facts),
            "steps": list(self.steps), "replanned": self.replanned,
        }

    def _restore(self, snap: Dict[str, Any]) -> None:
        self.world = snap["world"]
        self.prefix = snap["prefix"]
        self.walk = snap["walk"]
        self.facts = snap["facts"]
        self.level_facts = snap["level_facts"]
        self.steps = snap["steps"]
        self.replanned = snap["replanned"]

    def act(self, action: str, force: bool = False) -> Dict[str, Any]:
        """Take a move. Returns `{accepted, forced, ...}`."""
        offered = self.actions()
        snap = self._snapshot()
        record: Dict[str, Any] = {
            "depth": self.step,
            "observed": self._observed_compact(),
            "companion_intentions": [
                c["intention"] for c in self.observe()["companions"] if c.get("intention")
            ],
            "actions_offered": [a["action"] for a in offered],
            "alternatives": self._alternatives(offered),
            "chosen": action,
            "forced": False,
        }

        children = self._children()
        lookup = self._lookup()
        choice: Optional[Choice] = None
        if action == WAIT:
            companion_choices = [
                c for c in children.values() if not c.finished and c.actor != self.player
            ]
            if companion_choices:
                choice = min(companion_choices, key=lambda c: c.preference)
        else:
            choice = lookup.get(normalize_fact(action))

        if choice is not None and choice.op is not None:
            self._undo.append(snap)
            self._take(choice.op)
            self.steps.append(record)
            self._advance()
            self._write_playthrough()
            return {
                "accepted": True, "forced": False,
                "narration": narrate_operator(choice.op.text, dels=choice.op.dels,
                                              adds=choice.op.adds, actor=choice.actor),
                "step": self.step, "done": self.done,
                "observation": self.observe(),
            }

        if not force:
            return {
                "accepted": False, "forced": False,
                "reason": f"{action} is not one of the player's legal moves here; "
                          f"pass force=true to do it anyway and re-plan from the result",
                "legal": [a["action"] for a in offered],
            }

        if action == WAIT:
            return {"accepted": False, "forced": True, "reason": "nothing for the companions to do here"}

        grounded = ground_solution(
            [_term_dict(action)], self.world.space.sources, self.world.space.operator_owner
        )
        op = grounded[0]
        if not op.effects_resolved:
            return {
                "accepted": False, "forced": True,
                "reason": f"cannot apply {action}: no operator template {op.signature} among the "
                          f"level's sources, or its del/add mention a variable the head does not bind",
            }
        self._undo.append(snap)
        self.walk.append(op)
        self.facts = _apply(self.facts, op)
        self.level_facts = _apply(self.level_facts, op)
        record["forced"] = True
        self.steps.append(record)
        try:
            space = self._plan(sorted(self.level_facts))
        except ExtractError as exc:
            self._undo.pop()
            self._restore(snap)
            return {"accepted": False, "forced": True, "reason": f"re-planning failed: {exc}"}
        self.world = _World(space, self.cfg)
        self.prefix = ()
        self.replanned = True
        self._advance()
        self._write_playthrough()
        return {
            "accepted": True, "forced": True,
            "narration": narrate_operator(op.text, dels=op.dels, adds=op.adds,
                                          actor=self.world.convention.actor_of(op)),
            "step": self.step,
            "plans_remaining": self.plans_remaining,
            "done": self.done,
            "note": (
                "no plan survives from this world - the level cannot be completed from here"
                if self.plans_remaining == 0 else
                f"re-planned from the new world: {self.plans_remaining} plans remain"
            ),
            "observation": self.observe(),
        }

    def undo(self) -> Dict[str, Any]:
        if not self._undo:
            return {"undone": False, "reason": "nothing to undo", "step": self.step}
        self._restore(self._undo.pop())
        self._write_playthrough()
        return {"undone": True, "step": self.step, "observation": self.observe()}

    # ------------------------------------------------------------ afterwards

    def _finished_plans(self) -> List[int]:
        children = self._children()
        if FINISHED in children:
            return sorted(children[FINISHED].plan_indices)
        return []

    def explain(self) -> Dict[str, Any]:
        """After the fact: what was reached, what was missed, and what the
        planner would have offered at every decision."""
        all_labels = list(self.origin_labels)
        for cls in self.world.classes:
            if cls.label not in all_labels:
                all_labels.append(cls.label)
        finished = self._finished_plans()
        surviving = self.world.trie.surviving(self.prefix)
        reached = self.world.labels(finished) if finished else []
        reached_class = reached[0] if reached else None
        still_open = self.world.labels(surviving) if not finished else []
        missed = [label for label in all_labels if label not in reached and label not in still_open]
        decisions = []
        for record in self.steps:
            decisions.append({
                "depth": record["depth"],
                "chosen": record["chosen"],
                "forced": record["forced"],
                "alternatives": record["alternatives"],
            })
        return {
            "level": self.level_id,
            "goal": self.goal,
            "done": self.done,
            "replanned": self.replanned,
            "reached_class": reached_class,
            "reached_plan_index": finished[0] if finished else None,
            "still_open_classes": still_open,
            "missed_classes": missed,
            "all_classes": all_labels,
            "plans_remaining": self.plans_remaining,
            "decisions": decisions,
            "operators": [op.text for op in self.walk],
        }

    def state(self) -> Dict[str, Any]:
        return {
            "level": self.level_id,
            "step": self.step,
            "done": self.done,
            "plans_remaining": self.plans_remaining,
            "truncated": self.truncated,
            "operators": [op.text for op in self.walk],
            "facts": sorted(self.facts),
        }

    # ----------------------------------------------------------- recording

    def _observed_compact(self) -> Dict[str, Any]:
        return {
            "location": self._where(self.player),
            "companions": {c: self._where(c) for c in self._cast("companion")},
            "enemies": {e: self._where(e) for e in self._cast("enemy")},
        }

    def playthrough(self) -> Dict[str, Any]:
        finished = self._finished_plans()
        return {
            "level": self.level_id,
            "goal": self.goal,
            "started": self.started,
            "steps": self.steps,
            "final_class": (self.world.labels(finished) or [None])[0],
            "plan_index": finished[0] if finished else None,
            "operators": [op.text for op in self.walk],
            "done": self.done,
            "replanned": self.replanned,
            "plans_remaining": self.plans_remaining,
        }

    def _write_playthrough(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._playthrough_path), exist_ok=True)
            with open(self._playthrough_path, "w", encoding="utf-8") as f:
                json.dump(self.playthrough(), f, indent=2)
        except OSError:
            pass

    @property
    def playthrough_path(self) -> str:
        return self._playthrough_path


# --------------------------------------------------------------------------
# Module-level helpers the MCP server exposes
# --------------------------------------------------------------------------

def fun_profile(level: str, ablate: bool = False, loadouts: bool = False) -> Dict[str, Any]:
    """The fun scorecard as JSON. Long with `--ablate`/`--loadouts`: many re-plans."""
    from htn_metrics.profile import profile_level
    return profile_level(level, ablate=ablate, loadouts=loadouts).to_dict()


__all__ = ["LevelSession", "WAIT", "fun_profile"]
