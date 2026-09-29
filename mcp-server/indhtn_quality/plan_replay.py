"""Replay one plan over the initial state and extract causal links.

The decomposition tree supplies, per method instance, the parsed if()
literals (conditionTerms) and their ground bindings (unifiers +
conditionBindings); the static model supplies operator del()/add() templates.
Replaying the plan forward yields, for every operator step:

  needs  — ground fluent facts it consumes (its del() clauses, plus the
           emitting method instances' fluent if() literals, attributed to the
           instance's first descendant operator — temporally correct, since
           forward decomposition evaluates if() exactly at that point)
  gates  — non-fluent if() literals (static data, choice facts like
           equipped/2, axiom heads like canApply/3): they condition the edge
           but are not produced by operators
  causal links — (producer step | initial, fact, consumer step)

Causal layer: layer(op) = 1 + max(layer(producing op) over needs), layer 1
when every need is initial. causal_depth = max layer — the "unlock depth"
gate. Sequencing inside do() bodies is deliberately NOT a layer edge: an
authored montage of independent actions stays depth 1.

Tree caveats (probed 2026-07-02):
  * getDecompositionTree(idx) returns the SEARCH tree for solution idx: the
    shared decomposition prefix plus one appended subtree copy per explored
    alternative (all flagged successful). The current solution's path is the
    latest copy at every choice point — recovered here by backward-greedy
    alignment of tree operator nodes against the plan's operator list.
  * Around parallel() blocks the engine emits duplicate/self-referencing
    node IDs, so ancestry resolution falls back to "attach to the innermost
    open method" when parentNodeID does not resolve to a frame on the stack.
  * beginParallel/endParallel pseudo-operators appear in the plan operator
    list but not as tree operator nodes; both are skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .static_model import (
    StaticModel, ground_effects, match_ground_op, term_from_raw, term_to_str,
)

PSEUDO_OPS = {"beginParallel", "endParallel"}
DEFAULT_MARKER = "opResolveAtom"

_WS = re.compile(r"\s+")


def canon(fact: str) -> str:
    """Whitespace-insensitive canonical fact rendering."""
    return _WS.sub("", fact)


@dataclass
class Need:
    fact: str
    via: str  # "del" | "precondition"


@dataclass
class Link:
    producer: int  # step index, or -1 for the initial state
    fact: str
    consumer: int
    via: str  # "del" | "precondition"


@dataclass
class Step:
    index: int
    op: str
    name: str
    args: List[str]
    method_path: List[str]  # ground task names, outermost first
    method_instance: str    # innermost method instance id (grouping key)
    dels: List[str] = field(default_factory=list)
    adds: List[str] = field(default_factory=list)
    needs: List[Need] = field(default_factory=list)
    gates: List[str] = field(default_factory=list)
    atom_tag: Optional[Tuple[str, str]] = None


@dataclass
class Replay:
    steps: List[Step]
    links: List[Link]
    op_layers: List[int]
    causal_depth: int
    warnings: List[str]
    initial_facts: Set[str]


async def verify_replay(qs, replay: "Replay") -> List[str]:
    """Engine ground-truth check for the statically-grounded effects.

    Applies each step via apply_operator in a snapshot and diffs the state
    facts against the step's dels/adds. Returns mismatch descriptions
    (empty = the static model agrees with the engine). Restores state.
    """
    mismatches: List[str] = []
    snap = "indhtn_quality_verify"
    await qs.call("indhtn_snapshot_state", name=snap)
    try:
        before = {canon(f) for f in await qs.state_facts()}
        for step in replay.steps:
            res = await qs.call("indhtn_apply_operator", operator=step.op + ".")
            if not res.get("ok", False):
                mismatches.append(
                    f"step {step.index} {step.op}: engine refused "
                    f"({res.get('code')}: {res.get('failedPrecondition') or res.get('error')})")
                continue
            after = {canon(f) for f in await qs.state_facts()}
            removed, added = before - after, after - before
            if removed != set(step.dels) or added != set(step.adds):
                mismatches.append(
                    f"step {step.index} {step.op}: engine diff "
                    f"-{sorted(removed)} +{sorted(added)} vs static "
                    f"-{sorted(step.dels)} +{sorted(step.adds)}")
            before = after
    finally:
        await qs.call("indhtn_restore_state", name=snap)
        await qs.call("indhtn_delete_snapshot", name=snap)
    return mismatches


def _bindings_of(node: dict) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    for group in (node.get("unifiers") or []) + (node.get("conditionBindings") or []):
        for k, v in group.items():
            merged[k] = v
    return merged


def _render_cond(term: dict, bindings: Dict[str, str]) -> str:
    if term.get("isVariable"):
        return bindings.get("?" + term["functor"], "?" + term["functor"])
    args = term.get("args") or []
    if not args:
        return term["functor"]
    return term["functor"] + "(" + ",".join(_render_cond(a, bindings) for a in args) + ")"


def _cond_key(term: dict) -> Tuple[str, int]:
    return term["functor"], len(term.get("args") or [])


def _is_checkable(term: dict) -> bool:
    """Positive, non-builtin literal (not(...) and comparisons are search
    control, not consumable facts)."""
    functor = term.get("functor", "")
    return bool(functor) and functor != "not" and functor[0].isalpha()


class _Frame:
    __slots__ = ("node_id", "instance_id", "task", "fluent_literals",
                 "gate_literals", "attributed", "warnings")

    def __init__(self, node: dict, model: StaticModel, ordinal: int):
        self.node_id = node.get("nodeID")
        self.instance_id = f"{node.get('taskName', '?')}#m{ordinal}"
        self.task = node.get("taskName", "?")
        bindings = _bindings_of(node)
        self.fluent_literals: List[str] = []
        self.gate_literals: List[str] = []
        self.warnings: List[str] = []
        for term in node.get("conditionTerms") or []:
            if not _is_checkable(term):
                continue
            rendered = canon(_render_cond(term, bindings))
            if _cond_key(term) in model.fluent_preds:
                if "?" in rendered:
                    self.warnings.append(
                        f"non-ground fluent precondition {rendered} on {self.task}")
                else:
                    self.fluent_literals.append(rendered)
            else:
                self.gate_literals.append(rendered)
        self.attributed = False


@dataclass
class _Candidate:
    op: str
    name: str
    frames: List["_Frame"]  # stack snapshot, outermost first


def _collect_candidates(model: StaticModel, tree: List[dict]) -> List[_Candidate]:
    """All successful operator nodes in tree order, each with its method
    ancestry (a stack snapshot of shared _Frame objects)."""
    out: List[_Candidate] = []
    stack: List[_Frame] = []
    for ordinal, node in enumerate(tree):
        # Failed decomposition attempts stay in the tree (isSuccess false).
        # (isFailed true with isSuccess true = an earlier sibling clause
        # failed but this node succeeded — keep it.)
        if node.get("isSuccess") is False:
            continue
        parent = node.get("parentNodeID", -1)
        # Resolve ancestry: pop to the deepest stack frame matching the
        # parent; on anomaly (parallel-block ID drift) keep the current stack.
        matches = [i for i, f in enumerate(stack) if f.node_id == parent]
        if parent == -1:
            stack.clear()
        elif matches:
            del stack[matches[-1] + 1:]

        if node.get("isOperator"):
            task = canon(node.get("taskName", ""))
            name = task.split("(", 1)[0]
            if name in PSEUDO_OPS:
                continue
            out.append(_Candidate(op=task, name=name, frames=list(stack)))
        elif node.get("methodSignature") or parent == -1:
            stack.append(_Frame(node, model, ordinal))
        # else: structural nodes like the parallel(...) wrapper — skip
    return out


def _select_solution_path(candidates: List[_Candidate], plan_ops: List[str],
                          warnings: List[str]) -> List[_Candidate]:
    """Pick the candidate subsequence that IS this solution.

    The search tree keeps every explored alternative; the current solution
    took the latest copy at each choice point, so match the plan's operator
    list backward-greedily (latest occurrences win).
    """
    chosen: List[Optional[_Candidate]] = [None] * len(plan_ops)
    ci = len(candidates) - 1
    for pi in range(len(plan_ops) - 1, -1, -1):
        while ci >= 0 and candidates[ci].op != plan_ops[pi]:
            ci -= 1
        if ci < 0:
            warnings.append(
                f"plan op {plan_ops[pi]!r} not found in decomposition tree")
            continue
        chosen[pi] = candidates[ci]
        ci -= 1
    return [c for c in chosen if c is not None]


def _walk_tree(model: StaticModel, tree: List[dict], plan_ops: List[str],
               warnings: List[str]) -> List[Step]:
    candidates = _collect_candidates(model, tree)
    selected = _select_solution_path(candidates, plan_ops, warnings)
    steps: List[Step] = []
    for cand in selected:
        step = Step(
            index=len(steps), op=cand.op, name=cand.name, args=[],
            method_path=[f.task for f in cand.frames],
            method_instance=cand.frames[-1].instance_id if cand.frames else "<root>",
        )
        # A method instance's if() literals attach to its first selected
        # descendant operator (the state right before it = the state the
        # engine evaluated the if() against).
        for frame in cand.frames:
            if not frame.attributed:
                step.needs.extend(
                    Need(fact=lit, via="precondition")
                    for lit in frame.fluent_literals)
                step.gates.extend(frame.gate_literals)
                warnings.extend(frame.warnings)
                frame.attributed = True
        steps.append(step)
    return steps


def replay_plan(model: StaticModel, initial_facts: List[str], plan: dict,
                tree: List[dict], marker: str = DEFAULT_MARKER) -> Replay:
    warnings: List[str] = []
    plan_ops = [canon(op) for op in plan.get("operators", [])
                if op.split("(", 1)[0] not in PSEUDO_OPS]
    steps = _walk_tree(model, tree, plan_ops, warnings)
    if [s.op for s in steps] != plan_ops:
        warnings.append(
            f"tree/plan operator mismatch: tree={[s.op for s in steps]} "
            f"plan={plan_ops}")

    # Ground effects from the raw terms (structured, no string parsing).
    raws = [r for r in plan.get("operatorsRaw", [])
            if next(iter(r)) not in PSEUDO_OPS]
    for step, raw in zip(steps, raws):
        term = term_from_raw(raw)
        step.args = [canon(term_to_str(a)) for a in term.args]
        matched = match_ground_op(model, term)
        if matched is None:
            warnings.append(f"no operator template for {step.op}")
            continue
        tmpl, bindings = matched
        dels, adds = ground_effects(tmpl, bindings)
        step.dels = [canon(d) for d in dels]
        step.adds = [canon(a) for a in adds]
        step.needs.extend(Need(fact=d, via="del") for d in step.dels)
        if step.name == marker and len(step.args) >= 2:
            step.atom_tag = (step.args[0], step.args[1])

    # Forward replay: provenance map fact -> producing step (-1 = initial).
    initial = {canon(f) for f in initial_facts}
    provenance: Dict[str, int] = {f: -1 for f in initial}
    layers: List[int] = []
    links: List[Link] = []
    for step in steps:
        layer = 1
        seen: Set[Tuple[str, str]] = set()
        for need in step.needs:
            if (need.fact, need.via) in seen:
                continue
            seen.add((need.fact, need.via))
            if need.fact in provenance:
                producer = provenance[need.fact]
                links.append(Link(producer=producer, fact=need.fact,
                                  consumer=step.index, via=need.via))
                if producer >= 0:
                    layer = max(layer, layers[producer] + 1)
            else:
                warnings.append(
                    f"step {step.index} {step.op} needs {need.fact} "
                    f"(via {need.via}) but it is not in the replayed state")
        layers.append(layer)
        for d in step.dels:
            provenance.pop(d, None)
        for a in step.adds:
            provenance[a] = step.index

    return Replay(
        steps=steps, links=links, op_layers=layers,
        causal_depth=max(layers, default=0), warnings=warnings,
        initial_facts=initial,
    )
