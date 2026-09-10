"""Tests for the counterfactual harness: what a probe *is*, when it can be
trusted, and what F4 measures.

Companion to `test_fun_metrics.py` (which calibrates the families against
degenerate fixtures). These tests pin down the machinery those verdicts rest
on:

  - a probe is identified by fingerprints, not by labels that can be
    reassigned when class sizes shift under perturbation;
  - a cached probe is keyed by everything that could change its answer,
    including the rules of every dependency and the fingerprint config;
  - a probe that could not finish is `unknown`, and no conclusion that needs
    an exhaustive search is drawn from it;
  - a capped sweep is reported as a sample, never passed off as a count;
  - a loadout wins when the *encounter* is solvable with persistent state,
    not when each blocker is solvable from a fresh world.

Run:  python -m pytest tests/test_fun_counterfactual.py -v
"""

import json
import os

import pytest

from test_fun_metrics import FIXTURES, family, profile_for  # noqa: E402

from htn_metrics.config import Config  # noqa: E402
from htn_metrics.counterfactual import (  # noqa: E402
    CounterfactualHarness, run_ablation, run_loadouts,
)
from htn_metrics.extract import extract_plan_space, load_level_spec  # noqa: E402
from htn_metrics.profile import build_profile  # noqa: E402


def _space_for(fixture):
    path = os.path.join(FIXTURES, fixture)
    spec = load_level_spec(path)
    return path, spec, extract_plan_space(path, spec=spec)


# ==========================================================================
# Class identity
# ==========================================================================

def test_probe_result_roundtrip_keeps_fingerprints_and_status():
    """A probe is cached by what it *is*: fingerprints and a tri-state status."""
    from htn_metrics.counterfactual import ProbeResult

    result = ProbeResult(
        plan_count=2, fingerprints=[["a/1#0"], ["a/1#1"]], status="solvable"
    )
    assert ProbeResult.from_dict(result.to_dict()) == result
    unknown = ProbeResult(plan_count=0, status="unknown", error="out of memory")
    assert not unknown.solvable
    assert ProbeResult.from_dict(unknown.to_dict()).error == "out of memory"


def test_ablation_attributes_loss_by_fingerprint_not_by_label():
    """one_shot has three classes all labelled 'defeat [alt N]'.

    When a probe kills two of them, the survivor is relabelled plain 'defeat'
    (no collision, no suffix). Comparing labels would then report *every*
    class lost and invent a shared linchpin. Comparing fingerprints must
    not.
    """
    from htn_metrics.canonical import classify
    from htn_metrics.counterfactual import (
        ProbeResult, _goal_atoms, _mentions_any,
    )

    cfg = Config.load()
    _path, _spec, space = _space_for("one_shot")
    classes = classify(space, cfg.fingerprint_layers, cfg.fingerprint_max_depth)
    assert len(classes) == 3 and all("[alt" in c.label for c in classes), (
        "fixture must produce colliding labels for this test to mean anything"
    )
    victims, survivor = classes[:2], classes[2]
    goal_atoms = _goal_atoms(space.goal)
    target = next(
        f for f in space.facts_used
        if not f.startswith("fun") and not _mentions_any(f, goal_atoms)
    )

    class Stub:
        stats = {"probes_run": 0, "cache_hits": 0}

        def probe(self, facts, goal=None):
            if target in facts:
                return ProbeResult(
                    plan_count=space.plan_count,
                    fingerprints=[list(c.fingerprint) for c in classes],
                    status="solvable",
                )
            return ProbeResult(
                plan_count=survivor.size,
                fingerprints=[list(survivor.fingerprint)],
                status="solvable",
            )

    ablation = run_ablation(Stub(), space, cfg)
    assert target not in ablation["linchpins"], "survivor was relabelled, not lost"
    assert ablation["critical_facts"] == {v.label: [target] for v in victims}


# ==========================================================================
# Cache identity
# ==========================================================================

def test_cache_identity_tracks_dependency_sources_and_fingerprint_config(tmp_path):
    """Editing a dependency's rules, or the fingerprint config, must change
    the identity every cached probe is keyed under. Otherwise a ruleset edit
    reads yesterday's ablation."""
    from htn_metrics.counterfactual import world_hash

    root = tmp_path
    comp = root / "components" / "primitives" / "p"
    comp.mkdir(parents=True)
    (comp / "src.htn").write_text("opX(?a) :- del(), add(done(?a)).\n", encoding="utf-8")
    (comp / "manifest.json").write_text(json.dumps({
        "name": "p", "version": "1.0.0", "layer": "primitive", "dependencies": [],
    }), encoding="utf-8")
    level = root / "levels" / "l"
    level.mkdir(parents=True)
    (level / "level.htn").write_text(
        "ally(player).\ngo :- if(), do(opX(player)).\ngoals(go).\n", encoding="utf-8"
    )
    (level / "manifest.json").write_text(json.dumps({
        "name": "l", "version": "1.0.0", "layer": "level",
        "dependencies": ["primitives/p"],
    }), encoding="utf-8")

    cfg = Config.load()
    spec = load_level_spec(str(level))
    before = world_hash(spec, cfg, project_root=str(root))

    (comp / "src.htn").write_text("opX(?a) :- del(), add(changed(?a)).\n", encoding="utf-8")
    after_edit = world_hash(spec, cfg, project_root=str(root))
    assert after_edit != before, "dependency contents are part of the identity"

    deeper = cfg.with_overrides({"fingerprint_max_depth": 3})
    assert world_hash(spec, deeper, project_root=str(root)) != after_edit, (
        "fingerprint config changes the class labels stored in every probe"
    )


# ==========================================================================
# Tri-state probes
# ==========================================================================

def test_probe_reports_unknown_for_compile_errors_and_truncation(tmp_path):
    """A probe that could not finish is not an unsolvable world."""
    cfg = Config.load()
    path = os.path.join(FIXTURES, "reference_good")
    spec = load_level_spec(path)

    harness = CounterfactualHarness(spec, cfg, cache_dir=str(tmp_path))
    broken = harness.probe(list(spec.facts) + ["thisIsNot(valid"])
    assert broken.status == "unknown"
    assert broken.error, "the reason must travel with the result"

    tight = CounterfactualHarness(
        spec, cfg.with_overrides({"caps": {"memory_budget_bytes": 1}}),
        cache_dir=str(tmp_path / "tight"),
    )
    oom = tight.probe(list(spec.facts))
    assert oom.status == "unknown"
    assert "memory" in oom.error.lower()

    assert harness.probe(list(spec.facts)).status == "solvable"


def test_ablation_withholds_conclusions_when_probes_are_inconclusive(tmp_path):
    """Every probe runs out of memory: no linchpin, no independence, and F2
    must say the ablation was inconclusive rather than pass or fail on it."""
    path, spec, space = _space_for("reference_good")
    tight = Config.load().with_overrides({"caps": {"memory_budget_bytes": 1}})
    harness = CounterfactualHarness(spec, tight, cache_dir=str(tmp_path))
    ablation = run_ablation(harness, space, tight)

    assert ablation["conclusive"] is False
    assert ablation["unknown_probes"] >= ablation["facts_tested"]
    assert ablation["linchpins"] == []
    assert ablation["independent_pairs"] == 0
    assert ablation["player_critical"] is None

    profile = build_profile(path, cfg=Config.load(), ablation=ablation, space=space)
    f2 = family(profile, "f2_distinctness")
    assert f2.verdict != "fail"
    assert any("inconclusive" in f for f in f2.findings), f2.findings
    f6 = family(profile, "f6_player")
    assert f6.metrics["player_criticality"] is None


def test_f1_reports_out_of_memory_rather_than_unsolvable():
    path = os.path.join(FIXTURES, "reference_good")
    spec = load_level_spec(path)
    space = extract_plan_space(path, spec=spec, memory_budget=1)
    assert space.truncated
    profile = build_profile(path, cfg=Config.load(), space=space)
    f1 = family(profile, "f1_multiplicity")
    assert not any("unsolvable" in f for f in f1.findings), f1.findings
    assert any("memory" in f.lower() for f in f1.findings), f1.findings


# ==========================================================================
# Sampling is never silent
# ==========================================================================

def test_ablation_sampling_is_reported_by_f2(tmp_path):
    """A capped ablation is an estimate; F2 must say so, not claim a sweep."""
    path, spec, space = _space_for("reference_good")
    cfg = Config.load().with_overrides({"caps": {"max_ablation_facts": 3}})
    harness = CounterfactualHarness(spec, cfg, cache_dir=str(tmp_path))
    ablation = run_ablation(harness, space, cfg)
    assert ablation["sampled"] is True

    profile = build_profile(path, cfg=cfg, ablation=ablation, space=space)
    f2 = family(profile, "f2_distinctness")
    assert f2.verdict == "warn", f2.findings
    assert any("sampled" in f for f in f2.findings), f2.findings


def test_loadout_subset_truncation_is_never_silent(tmp_path):
    """shared_consumable: 3 exact loadouts, 4 smaller subsets, 2 blockers.

    A budget that keeps every exact loadout but drops the smaller subsets
    used to leave `sampled` False while multi_use silently collapsed. Any
    dropped subset must set `sampled`.
    """
    path, spec, space = _space_for("shared_consumable")
    cfg = Config.load().with_overrides({"caps": {"max_loadouts": 9}})
    harness = CounterfactualHarness(spec, cfg, cache_dir=str(tmp_path))
    lattice = run_loadouts(harness, space, cfg)
    assert lattice["subsets_evaluated"] < lattice["subsets_total"]
    assert lattice["sampled"] is True


# ==========================================================================
# F4 - the encounter, not the sum of its blockers
# ==========================================================================

def test_shared_consumable_wins_each_blocker_but_not_the_encounter():
    """{bomb, flare} clears the gate and clears the wall - one at a time.

    With one charge it cannot clear both. Feasibility must be the encounter
    number, with the independent number kept beside it and the gap named.
    """
    profile = profile_for("shared_consumable", loadouts=True)
    f4 = family(profile, "f4_choice")
    m = f4.metrics
    assert m["loadout_feasibility"] == pytest.approx(1 / 3, abs=0.01)
    assert m["loadout_feasibility_independent"] == pytest.approx(2 / 3, abs=0.01)
    assert ["bomb", "flare"] in m["winning_loadouts_independent"]
    assert ["bomb", "flare"] not in m["winning_loadouts"]
    assert ["bomb", "rope"] in m["winning_loadouts"]
    assert any("shared" in f or "encounter" in f for f in f4.findings), f4.findings
