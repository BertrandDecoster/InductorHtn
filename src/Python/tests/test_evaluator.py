"""
Tests for htn_evaluator.py

Verifies that evaluate_level correctly characterises the plan space for
known levels and returns sensible defaults for impossible goals.
"""

import sys
import os
import pytest

# conftest.py (in this directory) already inserts src/Python and gui/backend
# onto sys.path, so htn_evaluator and indhtnpy are importable without any
# manual path manipulation here.


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def puzzle1_planner(project_root):
    """Return an HtnPlanner pre-loaded with the assembled puzzle1 ruleset."""
    from indhtnpy import HtnPlanner

    assembled_path = project_root / "assembled" / "puzzle1" / "latest.htn"
    if not assembled_path.exists():
        pytest.skip(f"assembled/puzzle1/latest.htn not found at {assembled_path}")

    planner = HtnPlanner(False)
    source = assembled_path.read_text(encoding="utf-8")
    error = planner.HtnCompileCustomVariables(source)
    if error is not None:
        pytest.fail(f"Failed to compile assembled puzzle1: {error}")
    return planner


# ---------------------------------------------------------------------------
# Tests for evaluate_level — solvable case
# ---------------------------------------------------------------------------

class TestEvaluateLevelPuzzle1:
    """Tests against the assembled puzzle1 level (completePuzzle goal)."""

    def test_solvable(self, puzzle1_planner):
        """puzzle1 must be solvable."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        assert result["solvable"] is True

    def test_plan_count_at_least_one(self, puzzle1_planner):
        """puzzle1 must have at least one plan."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        assert result["plan_count"] >= 1

    def test_plan_lengths_non_empty_and_positive(self, puzzle1_planner):
        """Each plan must have at least one operator."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        lengths = result["plan_lengths"]
        assert isinstance(lengths, list)
        assert len(lengths) >= 1
        for length in lengths:
            assert isinstance(length, int)
            assert length > 0

    def test_operator_variety_non_empty(self, puzzle1_planner):
        """At least one unique operator name must appear."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        variety = result["operator_variety"]
        assert isinstance(variety, list)
        assert len(variety) >= 1

    def test_operator_variety_are_strings(self, puzzle1_planner):
        """All entries in operator_variety must be non-empty strings."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        for name in result["operator_variety"]:
            assert isinstance(name, str)
            assert len(name) > 0

    def test_plan_lengths_count_matches_plan_count(self, puzzle1_planner):
        """len(plan_lengths) must equal plan_count."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        assert len(result["plan_lengths"]) == result["plan_count"]

    def test_context_switch_cost_is_float(self, puzzle1_planner):
        """context_switch_cost must be a non-negative float."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        csc = result["context_switch_cost"]
        assert isinstance(csc, float)
        assert csc >= 0.0

    def test_difficulty_estimate_is_string(self, puzzle1_planner):
        """difficulty_estimate must be one of the expected labels."""
        from htn_evaluator import evaluate_level
        valid_labels = {"unsolvable", "trivial", "easy", "medium", "hard"}
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        assert result["difficulty_estimate"] in valid_labels

    def test_difficulty_not_unsolvable_when_solvable(self, puzzle1_planner):
        """A solvable level must not be labelled 'unsolvable'."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        assert result["difficulty_estimate"] != "unsolvable"

    def test_choice_data_is_none_or_list(self, puzzle1_planner):
        """choice_data must be None (flag OFF) or a list (flag ON)."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        assert result["choice_data"] is None or isinstance(result["choice_data"], list)

    def test_activation_distribution_consistent_with_choice_data(self, puzzle1_planner):
        """activation_distribution is None iff choice_data is None."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        if result["choice_data"] is None:
            assert result["activation_distribution"] is None
        else:
            assert isinstance(result["activation_distribution"], dict)


# ---------------------------------------------------------------------------
# Tests for evaluate_level — unsolvable case
# ---------------------------------------------------------------------------

class TestEvaluateLevelUnsolvable:
    """Tests with a goal that provably has no plan."""

    def test_solvable_is_false(self, puzzle1_planner):
        """An impossible goal must return solvable=False."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "thisGoalDoesNotExistAnywhere.")
        assert result["solvable"] is False

    def test_plan_count_is_zero(self, puzzle1_planner):
        """plan_count must be 0 when unsolvable."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "thisGoalDoesNotExistAnywhere.")
        assert result["plan_count"] == 0

    def test_plan_lengths_is_empty(self, puzzle1_planner):
        """plan_lengths must be empty when unsolvable."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "thisGoalDoesNotExistAnywhere.")
        assert result["plan_lengths"] == []

    def test_operator_variety_is_empty(self, puzzle1_planner):
        """operator_variety must be empty when unsolvable."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "thisGoalDoesNotExistAnywhere.")
        assert result["operator_variety"] == []

    def test_difficulty_estimate_is_unsolvable(self, puzzle1_planner):
        """difficulty_estimate must be 'unsolvable' when no plans exist."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "thisGoalDoesNotExistAnywhere.")
        assert result["difficulty_estimate"] == "unsolvable"

    def test_choice_data_is_none_or_list(self, puzzle1_planner):
        """choice_data must be None or a list even for unsolvable goals."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "thisGoalDoesNotExistAnywhere.")
        assert result["choice_data"] is None or isinstance(result["choice_data"], list)


# ---------------------------------------------------------------------------
# Tests for evaluate_level — result structure completeness
# ---------------------------------------------------------------------------

class TestEvaluateLevelStructure:
    """Verify that all required keys are always present."""

    REQUIRED_KEYS = {
        "solvable",
        "plan_count",
        "plan_lengths",
        "operator_variety",
        "context_switch_cost",
        "difficulty_estimate",
        "choice_data",
        "activation_distribution",
        "choice_stats",
    }

    def test_solvable_result_has_all_keys(self, puzzle1_planner):
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle.")
        for key in self.REQUIRED_KEYS:
            assert key in result, f"Missing key '{key}' in solvable result"

    def test_unsolvable_result_has_all_keys(self, puzzle1_planner):
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "nonExistentGoal99.")
        for key in self.REQUIRED_KEYS:
            assert key in result, f"Missing key '{key}' in unsolvable result"

    def test_goal_without_trailing_period(self, puzzle1_planner):
        """evaluate_level must accept goals without a trailing period."""
        from htn_evaluator import evaluate_level
        result = evaluate_level(puzzle1_planner, "completePuzzle")
        # Should still work — evaluator appends '.' if missing
        assert isinstance(result["solvable"], bool)


# ---------------------------------------------------------------------------
# Unit tests for _build_activation_distribution (fix 1: correct JSON keys)
# ---------------------------------------------------------------------------

class TestBuildActivationDistribution:
    """Direct tests for the helper that maps C++ choice-data records to a
    per-functor distribution dict.  Injected with fake records so the test
    does not require a library built with INDHTN_CHOICE_TRACKING=ON."""

    def _call(self, records):
        from htn_evaluator import _build_activation_distribution
        return _build_activation_distribution(records)

    def test_none_input_returns_none(self):
        assert self._call(None) is None

    def test_empty_list_returns_empty_dict(self):
        result = self._call([])
        assert result == {}

    def test_camel_case_keys_are_read_correctly(self):
        """C++ emits 'taskFunctor', 'unifyingMethods', 'viableMethods' (arrays)."""
        records = [
            {
                "taskFunctor": "defeatEnemy",
                "taskFull": "defeatEnemy(guard1)",
                "depth": 2,
                "unifyingMethods": ["theBurn(guard1)", "theSlipstream(guard1)"],
                "viableMethods": ["theBurn(guard1)"],
            }
        ]
        dist = self._call(records)
        assert "defeatEnemy" in dist
        entry = dist["defeatEnemy"]
        assert entry["activation_count"] == 1
        assert entry["unifying_count"] == 2
        assert entry["viable_count"] == 1
        assert entry["depth"] == 2

    def test_snake_case_keys_are_ignored(self):
        """Old wrong keys ('task_functor', 'unifying_count') produce no entries."""
        records = [
            {
                "task_functor": "shouldBeIgnored",
                "unifying_count": 5,
                "viable_count": 3,
            }
        ]
        dist = self._call(records)
        assert "shouldBeIgnored" not in dist
        assert dist == {}

    def test_multiple_records_for_same_functor_accumulate(self):
        """Two records for the same functor merge correctly."""
        records = [
            {
                "taskFunctor": "clearRoom",
                "depth": 1,
                "unifyingMethods": ["m1", "m2"],
                "viableMethods": ["m1"],
            },
            {
                "taskFunctor": "clearRoom",
                "depth": 3,
                "unifyingMethods": ["m1"],
                "viableMethods": ["m1"],
            },
        ]
        dist = self._call(records)
        entry = dist["clearRoom"]
        assert entry["activation_count"] == 2
        assert entry["unifying_count"] == 3   # 2 + 1
        assert entry["viable_count"] == 2      # 1 + 1
        assert entry["depth"] == 1             # minimum of (1, 3)

    def test_records_with_missing_optional_fields_default_gracefully(self):
        """Records with no unifyingMethods / viableMethods default to 0."""
        records = [{"taskFunctor": "foo", "depth": 0}]
        dist = self._call(records)
        assert dist["foo"]["unifying_count"] == 0
        assert dist["foo"]["viable_count"] == 0


# ---------------------------------------------------------------------------
# Unit tests for the by-atom / by-method report views (offline — synthetic
# GetChoiceStats() payloads, no native library required).
# ---------------------------------------------------------------------------

class TestChoiceStatsViews:
    """Direct tests for _build_by_atom_view / _build_by_method_view using a
    synthetic {byAtom, byMethod} payload matching the C++ JSON schema."""

    # Mirrors the headline TwoSubtaskPartition example:
    #   head(): 9 groundings, 4 success, func1 fails 3, func2 fails 2.
    SAMPLE = {
        "byAtom": [
            {"atomFunctor": "func1", "isOperator": False, "tested": 9, "fail": 3,
             "clears": [{"method": "func1(?x) => if(path(?x, c)), do(op1(?x))",
                         "methodDocOrder": 3, "count": 6}]},
            {"atomFunctor": "func2", "isOperator": False, "tested": 6, "fail": 2,
             "clears": []},
            {"atomFunctor": "op1", "isOperator": True, "tested": 4, "fail": 0,
             "clears": []},
        ],
        "byMethod": [
            {"clauseDocOrder": 1, "clauseSignature": "head => if(...), do(...)",
             "methodType": "normal", "subtaskCount": 2, "groundingsN": 9, "successS": 4,
             "gateFailCount": 0, "furthestCompleted": [3, 2, 4],
             "positions": [
                 {"positionIndex": 1, "atomFunctor": "func2", "tested": 6, "fail": 2, "clears": []},
                 {"positionIndex": 0, "atomFunctor": "func1", "tested": 9, "fail": 3, "clears": []},
             ]},
            {"clauseDocOrder": -1, "clauseSignature": "goal", "methodType": "goal",
             "subtaskCount": 0, "groundingsN": 0, "successS": 0, "gateFailCount": 0,
             "furthestCompleted": [],
             "positions": [
                 {"positionIndex": 0, "atomFunctor": "head", "tested": 1, "fail": 0, "clears": []},
             ]},
        ],
    }

    def test_none_returns_none(self):
        from htn_evaluator import _build_by_atom_view, _build_by_method_view
        assert _build_by_atom_view(None) is None
        assert _build_by_method_view(None) is None

    def test_by_atom_sorted_by_tested_desc(self):
        from htn_evaluator import _build_by_atom_view
        view = _build_by_atom_view(self.SAMPLE)
        tested = [a["tested"] for a in view]
        assert tested == sorted(tested, reverse=True)
        assert view[0]["atomFunctor"] == "func1"

    def test_by_method_partition_invariant(self):
        from htn_evaluator import _build_by_method_view
        view = _build_by_method_view(self.SAMPLE)
        for clause in view:
            if clause["methodType"] != "normal":
                continue
            sum_fail = sum(p["fail"] for p in clause["positions"])
            assert clause["successS"] + sum_fail == clause["groundingsN"]

    def test_furthest_completed_histogram_sums_to_groundings(self):
        """sum(furthestCompleted) == groundingsN; last bucket == successS."""
        from htn_evaluator import _build_by_method_view
        view = _build_by_method_view(self.SAMPLE)
        head = next(c for c in view if c["clauseDocOrder"] == 1)
        hist = head["furthestCompleted"]
        assert sum(hist) == head["groundingsN"]
        assert hist[head["subtaskCount"]] == head["successS"]
        # The histogram tells which own subtask blocks: fail@func1=3, fail@func2=2.
        assert hist == [3, 2, 4]

    def test_by_method_positions_sorted_and_goal_first(self):
        from htn_evaluator import _build_by_method_view
        view = _build_by_method_view(self.SAMPLE)
        # Goal clause (-1) sorts first.
        assert view[0]["clauseDocOrder"] == -1
        # Each clause's positions are sorted by index.
        head = next(c for c in view if c["clauseDocOrder"] == 1)
        indices = [p["positionIndex"] for p in head["positions"]]
        assert indices == sorted(indices)


# ---------------------------------------------------------------------------
# Tests for library_coverage dead_methods detection (fix 3)
# ---------------------------------------------------------------------------

class TestLibraryCoverageDeadMethods:
    """Verify that dead_methods lists operators defined in source but never
    appearing in any plan solution.  Uses a temporary level directory with
    an assembled HTN file containing one reachable and one dead operator."""

    @pytest.fixture
    def temp_level_with_dead_op(self, tmp_path):
        """Build a minimal assembled HTN with opAlive (reachable) and
        opDead (defined but unreachable from the goal)."""
        htn_source = (
            "opAlive() :- del(), add(done).\n"
            "opDead() :- del(), add(shouldNeverHappen).\n"
            "doTask() :- if(), do(opAlive()).\n"
            "goals(doTask()).\n"
        )
        level_dir = tmp_path / "test_level"
        level_dir.mkdir()
        manifest = {
            "name": "test_level",
            "version": "0.1.0",
            "layer": "level",
            "description": "test",
            "dependencies": [],
            "certified": False,
            "certification": {
                "linter": False,
                "tests_pass": False,
                "design_match": False,
                "last_checked": None,
            },
            "provides": [],
            "requires": [],
        }
        import json as _json
        (level_dir / "manifest.json").write_text(_json.dumps(manifest))
        # Write the assembled source as latest.htn so strategy 1 is used
        assembled_dir = tmp_path / "assembled" / "test_level"
        assembled_dir.mkdir(parents=True)
        (assembled_dir / "latest.htn").write_text(htn_source)
        return tmp_path

    @pytest.fixture(autouse=True)
    def _patch_project_root(self, temp_level_with_dead_op, monkeypatch):
        """Make library_coverage resolve assembled/ relative to tmp_path."""
        import htn_evaluator as _ev
        monkeypatch.setattr(_ev, "_find_project_root", lambda: str(temp_level_with_dead_op))

    def test_activated_operator_has_nonzero_count(self, temp_level_with_dead_op):
        from htn_evaluator import library_coverage
        levels_dir = str(temp_level_with_dead_op / "test_level")
        report = library_coverage(levels_dir)
        counts = report["method_activation_counts"]
        assert counts.get("opAlive", 0) >= 1, "opAlive must appear in plans"

    def test_dead_operator_appears_in_dead_methods_when_parser_available(
        self, temp_level_with_dead_op
    ):
        """opDead is defined in source but never appears in any plan solution."""
        from htn_evaluator import library_coverage
        import os as _os
        project_root = _os.path.abspath(
            _os.path.join(_os.path.dirname(__file__), "../../..")
        )
        backend_path = _os.path.join(project_root, "gui", "backend")
        if not _os.path.exists(_os.path.join(backend_path, "htn_parser.py")):
            pytest.skip("htn_parser not available")

        levels_dir = str(temp_level_with_dead_op / "test_level")
        report = library_coverage(levels_dir)
        assert "opDead" in report["dead_methods"], (
            f"opDead must be detected as dead. Got: {report['dead_methods']}"
        )
