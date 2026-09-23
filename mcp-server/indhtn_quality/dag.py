"""Ruleset -> unlock-DAG: build, measure, render.

Converts a level + goal (+ injected facts, e.g. a loadout) into the union
causal graph over all plans the planner finds:

    fact nodes  (ground fluent facts; initial facts at layer 0)
    op nodes    (ground operator instances)
    edges       produces (op -> fact), enables (fact -> op, via del() or a
                method if() precondition), gates (choice fact -> op)

Layering is strictly causal (see plan_replay): layer(op) = 1 + max layer of
the facts it consumes; authored do() sequencing is NOT depth. This is the
"nodes from a layer unlock deeper nodes" measure — a do() montage of
independent actions stays at depth 1 no matter how many steps it has.

CLI:
    PYTHONPATH=mcp-server python -m indhtn_quality.dag <level.htn> \
        --goal "enterFortress()." \
        --facts "equipped(player, frostNova)" "equipped(companion, shadowStep)" \
        --format summary|mermaid|dot|json [--assert-depth 3:5] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .plan_replay import DEFAULT_MARKER, Replay, replay_plan, verify_replay
from .session_util import DEFAULT_MEMORY_BUDGET, open_session, run
from .static_model import build_static_model

DEFAULT_CHOICE_PREDS = ("equipped",)


@dataclass
class DagResult:
    goal: str
    nodes: List[dict]
    edges: List[dict]
    metrics: dict
    replays: List[Replay] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def _choice_pred_of(fact: str) -> str:
    return fact.split("(", 1)[0]


async def build_dag(*, paths: Optional[Sequence[str]] = None,
                    source: Optional[str] = None,
                    goal: str,
                    facts: Sequence[str] = (),
                    memory_budget: int = DEFAULT_MEMORY_BUDGET,
                    max_plans: Optional[int] = None,
                    choice_preds: Sequence[str] = DEFAULT_CHOICE_PREDS,
                    marker: str = DEFAULT_MARKER,
                    verify_replays: int = 0) -> DagResult:
    async with open_session(paths=paths, source=source, facts=facts,
                            memory_budget=memory_budget) as qs:
        model = build_static_model(qs.source_text)
        initial = await qs.state_facts()
        plans = await qs.find_plans(goal, max_plans=max_plans)
        if not plans.get("ok", False):
            return DagResult(
                goal=goal, nodes=[], edges=[], metrics={"planCount": 0},
                warnings=[f"goal produced no plans: "
                          f"{plans.get('failureContext') or plans}"],
                meta={"paths": list(paths or []), "facts": list(facts)},
            )
        # Fetch every tree BEFORE any verification: verify_replay's
        # apply_operator calls plan a one-op goal, which clobbers the
        # session's stored solutions (and with them get_decomposition_tree).
        deduped = _dedupe(plans["plans"])
        trees = [await qs.tree(plan["index"]) for plan in deduped]
        replays = [replay_plan(model, initial, plan, tree, marker=marker)
                   for plan, tree in zip(deduped, trees)]
        for replay in replays[:verify_replays]:
            for mismatch in await verify_replay(qs, replay):
                replay.warnings.append(f"verify-replay: {mismatch}")

    return _assemble(goal, replays, list(facts), list(paths or []),
                     set(choice_preds))


def _dedupe(plans: List[dict]) -> List[dict]:
    seen, out = set(), []
    for p in plans:
        key = tuple(p["operators"])
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _assemble(goal: str, replays: List[Replay], facts: List[str],
              paths: List[str], choice_preds: set) -> DagResult:
    nodes: Dict[str, dict] = {}
    edges: Dict[Tuple[str, str, str], dict] = {}

    def node(node_id: str, **attrs) -> dict:
        n = nodes.setdefault(node_id, {"id": node_id, "plans": []})
        n.update({k: v for k, v in attrs.items() if k not in n or n[k] is None})
        return n

    def edge(src: str, dst: str, kind: str, plan_idx: int, **attrs):
        e = edges.setdefault((src, dst, kind),
                             {"from": src, "to": dst, "kind": kind, "plans": [],
                              **attrs})
        if plan_idx not in e["plans"]:
            e["plans"].append(plan_idx)

    consumed_per_plan: List[set] = []
    fingerprints: Dict[frozenset, List[int]] = {}

    for pi, replay in enumerate(replays):
        consumed = set()
        for step in replay.steps:
            oid = f"o:{step.op}"
            n = node(oid, kind="op", label=step.op,
                     method=step.method_instance, layer=0,
                     atomTag=list(step.atom_tag) if step.atom_tag else None)
            n["layer"] = max(n["layer"], replay.op_layers[step.index])
            if pi not in n["plans"]:
                n["plans"].append(pi)
            for a in step.adds:
                fid = f"f:{a}"
                fn = node(fid, kind="fact", label=a, cls="fluent", layer=0)
                fn["layer"] = max(fn["layer"], replay.op_layers[step.index])
                if pi not in fn["plans"]:
                    fn["plans"].append(pi)
                edge(oid, fid, "produces", pi)
            for gate in step.gates:
                if _choice_pred_of(gate) in choice_preds:
                    gid = f"f:{gate}"
                    gn = node(gid, kind="fact", label=gate, cls="choice", layer=0)
                    if pi not in gn["plans"]:
                        gn["plans"].append(pi)
                    edge(gid, oid, "gates", pi)
        for link in replay.links:
            consumed.add(link.fact)
            fid = f"f:{link.fact}"
            fn = node(fid, kind="fact", label=link.fact, layer=0)
            fn.setdefault("cls", "fluent")
            if link.producer == -1:
                fn["cls"] = ("choice" if _choice_pred_of(link.fact) in choice_preds
                             else "initial")
            if pi not in fn["plans"]:
                fn["plans"].append(pi)
            consumer = replay.steps[link.consumer]
            edge(fid, f"o:{consumer.op}", "enables", pi, via=link.via)
        consumed_per_plan.append(consumed)
        tags = frozenset(s.atom_tag for s in replay.steps if s.atom_tag)
        fingerprints.setdefault(tags, []).append(pi)

    plan_lengths = [len(r.steps) for r in replays]
    depths = [r.causal_depth for r in replays]
    bottlenecks = sorted(set.intersection(*consumed_per_plan)) if consumed_per_plan else []
    layer_widths: Dict[int, int] = {}
    for n in nodes.values():
        if n["kind"] == "op":
            layer_widths[n["layer"]] = layer_widths.get(n["layer"], 0) + 1

    metrics = {
        "planCount": len(replays),
        "causalDepth": max(depths, default=0),
        "causalDepthMin": min(depths, default=0),
        "minPlanLength": min(plan_lengths, default=0),
        "maxPlanLength": max(plan_lengths, default=0),
        "layerWidths": [layer_widths.get(i, 0)
                        for i in range(1, max(layer_widths, default=0) + 1)],
        "bottleneckFacts": bottlenecks,
        "clusters": [
            {"fingerprint": sorted([list(t) for t in tags]), "plans": plan_idxs}
            for tags, plan_idxs in sorted(
                fingerprints.items(), key=lambda kv: kv[1][0])
        ],
    }
    warnings = [w for r in replays for w in r.warnings]
    return DagResult(
        goal=goal, nodes=list(nodes.values()), edges=list(edges.values()),
        metrics=metrics, replays=replays, warnings=warnings,
        meta={"paths": paths, "facts": facts},
    )


def check_depth(metrics: dict, depth_range: Tuple[int, int]) -> dict:
    lo, hi = depth_range
    depth = metrics.get("causalDepth", 0)
    ok = lo <= depth <= hi
    return {
        "name": "depth-in-range",
        "ok": ok,
        "detail": f"causalDepth {depth} {'in' if ok else 'NOT in'} [{lo},{hi}]"
                  + (f" (shallowest plan: {metrics.get('causalDepthMin')})"
                     if metrics.get("causalDepthMin") != depth else ""),
    }


# ----------------------------------------------------------------------
# Renderers
# ----------------------------------------------------------------------

def render_summary(result: DagResult) -> str:
    m = result.metrics
    lines = [
        f"goal: {result.goal}",
        f"plans: {m.get('planCount', 0)}   "
        f"causalDepth: {m.get('causalDepth', 0)} "
        f"(min over plans: {m.get('causalDepthMin', 0)})   "
        f"planLength: {m.get('minPlanLength', 0)}-{m.get('maxPlanLength', 0)}",
        f"layerWidths (ops per causal layer): {m.get('layerWidths', [])}",
    ]
    if m.get("bottleneckFacts"):
        lines.append("bottleneck facts (consumed in every plan):")
        lines.extend(f"  {f}" for f in m["bottleneckFacts"])
    lines.append(f"solution clusters: {len(m.get('clusters', []))}")
    for c in m.get("clusters", []):
        fp = ", ".join("/".join(pair) for pair in c["fingerprint"]) or "(no markers)"
        lines.append(f"  [{fp}] plans {c['plans']}")
    op_nodes = sorted((n for n in result.nodes if n["kind"] == "op"),
                      key=lambda n: (n["layer"], n["label"]))
    current = None
    lines.append("")
    for n in op_nodes:
        if n["layer"] != current:
            current = n["layer"]
            lines.append(f"layer {current}:")
        lines.append(f"  {n['label']}")
    if result.warnings:
        lines.append("")
        lines.append(f"warnings ({len(result.warnings)}):")
        lines.extend(f"  {w}" for w in sorted(set(result.warnings)))
    return "\n".join(lines)


def _mermaid_id(node_id: str, index: Dict[str, str]) -> str:
    if node_id not in index:
        index[node_id] = f"n{len(index)}"
    return index[node_id]


def render_mermaid(result: DagResult) -> str:
    ids: Dict[str, str] = {}
    lines = ["flowchart TD"]
    layers: Dict[int, List[dict]] = {}
    for n in result.nodes:
        if n["kind"] == "op" or n.get("cls") in ("fluent", "initial"):
            layers.setdefault(n["layer"], []).append(n)
    for layer in sorted(layers):
        title = "initial state" if layer == 0 else f"layer {layer}"
        lines.append(f'  subgraph L{layer}["{title}"]')
        for n in sorted(layers[layer], key=lambda x: x["label"]):
            mid = _mermaid_id(n["id"], ids)
            label = n["label"].replace('"', "'")
            if n["kind"] == "op":
                lines.append(f'    {mid}["{label}"]')
            else:
                lines.append(f'    {mid}("{label}")')
        lines.append("  end")
    choice_nodes = [n for n in result.nodes if n.get("cls") == "choice"]
    for n in sorted(choice_nodes, key=lambda x: x["label"]):
        mid = _mermaid_id(n["id"], ids)
        lines.append(f'  {mid}{{{{"{n["label"]}"}}}}')
    for e in result.edges:
        if e["from"] not in ids or e["to"] not in ids:
            continue
        src, dst = ids[e["from"]], ids[e["to"]]
        if e["kind"] == "gates":
            lines.append(f"  {src} -.-> {dst}")
        else:
            lines.append(f"  {src} --> {dst}")
    return "\n".join(lines)


def render_dot(result: DagResult) -> str:
    ids: Dict[str, str] = {}
    lines = ["digraph unlockdag {", "  rankdir=TB;"]
    for n in result.nodes:
        nid = _mermaid_id(n["id"], ids)
        label = n["label"].replace('"', "'")
        if n["kind"] == "op":
            shape = "box"
        elif n.get("cls") == "choice":
            shape = "hexagon"
        else:
            shape = "ellipse"
        lines.append(f'  {nid} [label="{label}", shape={shape}];')
    for e in result.edges:
        src, dst = ids.get(e["from"]), ids.get(e["to"])
        if src and dst:
            style = ' [style=dashed]' if e["kind"] == "gates" else ""
            lines.append(f"  {src} -> {dst}{style};")
    lines.append("}")
    return "\n".join(lines)


def to_json(result: DagResult) -> dict:
    return {
        "meta": {**result.meta, "goal": result.goal},
        "nodes": result.nodes,
        "edges": result.edges,
        "metrics": result.metrics,
        "warnings": result.warnings,
    }


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="indhtn_quality.dag",
        description="Convert a ruleset + goal into a layered causal unlock-DAG.")
    ap.add_argument("level", help="path to the .htn level file")
    ap.add_argument("--goal", required=True, help='goal, e.g. "enterFortress()."')
    ap.add_argument("--facts", nargs="*", default=[],
                    help="facts to inject before planning (e.g. a loadout)")
    ap.add_argument("--format", choices=["summary", "mermaid", "dot", "json"],
                    default="summary")
    ap.add_argument("--out", help="write output to a file instead of stdout")
    ap.add_argument("--assert-depth", metavar="MIN:MAX",
                    help="exit 1 unless causalDepth is within MIN:MAX")
    ap.add_argument("--verify-replay", type=int, default=0, metavar="N",
                    help="cross-check the first N plans' effects against the "
                         "engine via apply_operator")
    ap.add_argument("--max-plans", type=int)
    ap.add_argument("--memory-budget", type=int, default=DEFAULT_MEMORY_BUDGET)
    ap.add_argument("--choice-preds", default=",".join(DEFAULT_CHOICE_PREDS),
                    help="comma-separated choice predicates (default: equipped)")
    ap.add_argument("--marker", default=DEFAULT_MARKER)
    args = ap.parse_args(argv)

    result = run(build_dag(
        paths=[args.level], goal=args.goal, facts=args.facts,
        memory_budget=args.memory_budget, max_plans=args.max_plans,
        choice_preds=[c for c in args.choice_preds.split(",") if c],
        marker=args.marker, verify_replays=args.verify_replay,
    ))

    renderer = {
        "summary": render_summary,
        "mermaid": render_mermaid,
        "dot": render_dot,
        "json": lambda r: json.dumps(to_json(r), indent=2),
    }[args.format]
    text = renderer(result)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        print(text)

    exit_code = 0
    if result.metrics.get("planCount", 0) == 0:
        print("FAIL: no plans found", file=sys.stderr)
        exit_code = 1
    if args.assert_depth:
        lo, hi = args.assert_depth.split(":")
        checked = check_depth(result.metrics, (int(lo), int(hi)))
        stream = sys.stdout if checked["ok"] else sys.stderr
        print(("PASS: " if checked["ok"] else "FAIL: ") + checked["detail"],
              file=stream)
        if not checked["ok"]:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
