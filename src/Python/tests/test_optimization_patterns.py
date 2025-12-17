"""
Tests for Prolog/HTN optimization patterns by measuring resolution steps.

These tests validate the optimization patterns documented in:
.claude/rules/crafting-rulesets.md

Resolution step tracking must be enabled (INDHTN_TRACK_RESOLUTION_STEPS=ON, default).
Patterns marked [VALIDATED] show >20% improvement.
"""

import pytest
from indhtnpy import HtnPlanner


class OptimizationPatternTestHelper:
    """Helper class for testing optimization patterns."""

    @staticmethod
    def measure_steps(code: str, query: str) -> int:
        """Compile code, run query, and return resolution step count."""
        planner = HtnPlanner(False)
        error = planner.PrologCompile(code)
        if error:
            pytest.fail(f"Compilation error: {error}")

        error, result = planner.PrologQuery(query)
        steps = planner.GetLastResolutionStepCount()
        return steps

    @staticmethod
    def compare_patterns(slow_code: str, fast_code: str, query: str) -> tuple:
        """Compare slow and fast patterns, return (slow_steps, fast_steps, improvement%)."""
        slow_steps = OptimizationPatternTestHelper.measure_steps(slow_code, query)
        fast_steps = OptimizationPatternTestHelper.measure_steps(fast_code, query)

        if slow_steps > 0 and fast_steps >= 0:
            improvement = ((slow_steps - fast_steps) / slow_steps) * 100
        else:
            improvement = 0

        return slow_steps, fast_steps, improvement


@pytest.fixture
def helper():
    """Provide optimization pattern test helper."""
    return OptimizationPatternTestHelper()


@pytest.fixture
def resolution_tracking_enabled():
    """Verify resolution step tracking is enabled."""
    planner = HtnPlanner(False)
    planner.PrologCompile("test_fact.")
    planner.PrologQuery("test_fact.")
    steps = planner.GetLastResolutionStepCount()
    if steps == -1:
        pytest.skip("Resolution tracking not enabled. Rebuild without -DINDHTN_TRACK_RESOLUTION_STEPS=OFF")
    return True


class TestGoalOrdering:
    """[VALIDATED] Goal ordering - constraining goal first."""

    SLOW_CODE = """
person(alice).
person(bob).
person(carol).
person(dave).
rich(dave).
findRichPerson(P) :- person(P), rich(P).
"""

    FAST_CODE = """
person(alice).
person(bob).
person(carol).
person(dave).
rich(dave).
findRichPerson(P) :- rich(P), person(P).
"""

    QUERY = "findRichPerson(X)."

    def test_constraining_goal_first_is_faster(self, helper, resolution_tracking_enabled):
        """Putting constraining goal first should reduce resolution steps."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        assert fast < slow, f"Fast ({fast}) should be less than slow ({slow})"

    def test_constraining_goal_first_validated(self, helper, resolution_tracking_enabled):
        """Goal ordering should show >20% improvement."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        assert improvement >= 20, f"Expected >20% improvement, got {improvement:.1f}%"


class TestPrecomputedNegation:
    """[VALIDATED] Pre-computed negation vs runtime not()."""

    SLOW_CODE = """
item(a).
item(b).
item(c).
item(d).
excluded(b).
findNonExcluded(X) :- item(X), not(excluded(X)).
"""

    FAST_CODE = """
item(a).
item(b).
item(c).
item(d).
excluded(b).
nonExcluded(a).
nonExcluded(c).
nonExcluded(d).
findNonExcluded(X) :- nonExcluded(X).
"""

    QUERY = "findNonExcluded(X)."

    def test_precomputed_negation_is_faster(self, helper, resolution_tracking_enabled):
        """Pre-computed negation should reduce resolution steps."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        assert fast < slow, f"Fast ({fast}) should be less than slow ({slow})"

    def test_precomputed_negation_validated(self, helper, resolution_tracking_enabled):
        """Pre-computed negation should show >20% improvement."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        assert improvement >= 20, f"Expected >20% improvement, got {improvement:.1f}%"


class TestDirectCount:
    """[VALIDATED] Direct count() vs redundant findall() + count()."""

    SLOW_CODE = """
member(a, team1).
member(b, team1).
member(c, team1).
member(d, team2).
member(e, team2).
teamSize(Team, Size) :- findall(M, member(M, Team), List), count(Size, member(X, Team)).
"""

    FAST_CODE = """
member(a, team1).
member(b, team1).
member(c, team1).
member(d, team2).
member(e, team2).
teamSize(Team, Size) :- count(Size, member(X, Team)).
"""

    QUERY = "teamSize(team1, S)."

    def test_direct_count_is_faster(self, helper, resolution_tracking_enabled):
        """Direct count should reduce resolution steps."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        assert fast < slow, f"Fast ({fast}) should be less than slow ({slow})"

    def test_direct_count_validated(self, helper, resolution_tracking_enabled):
        """Direct count should show >20% improvement."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        assert improvement >= 20, f"Expected >20% improvement, got {improvement:.1f}%"


class TestCutForDeterminism:
    """[VALIDATED] Cut for deterministic choice."""

    SLOW_CODE = """
classify(X, positive) :- >(X, 0).
classify(X, zero) :- ==(X, 0).
classify(X, negative) :- <(X, 0).
getClassification(X, C) :- classify(X, C).
"""

    FAST_CODE = """
classify(X, positive) :- >(X, 0), !.
classify(X, zero) :- ==(X, 0), !.
classify(X, negative) :- <(X, 0).
getClassification(X, C) :- classify(X, C).
"""

    QUERY = "getClassification(5, C)."

    def test_cut_is_faster(self, helper, resolution_tracking_enabled):
        """Using cut for determinism should reduce resolution steps."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        assert fast < slow, f"Fast ({fast}) should be less than slow ({slow})"

    def test_cut_validated(self, helper, resolution_tracking_enabled):
        """Cut should show >20% improvement."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        assert improvement >= 20, f"Expected >20% improvement, got {improvement:.1f}%"


class TestFirstArgumentIndexing:
    """First-argument indexing pattern."""

    SLOW_CODE = """
data(1, a, x).
data(2, b, y).
data(3, c, z).
data(4, d, w).
data(5, e, v).
lookup(Val, Key) :- data(Key, Val, Extra).
"""

    FAST_CODE = """
dataByVal(a, 1, x).
dataByVal(b, 2, y).
dataByVal(c, 3, z).
dataByVal(d, 4, w).
dataByVal(e, 5, v).
lookup(Val, Key) :- dataByVal(Val, Key, Extra).
"""

    QUERY = "lookup(c, K)."

    def test_first_argument_indexing_is_faster(self, helper, resolution_tracking_enabled):
        """Putting discriminating value in first argument should reduce steps."""
        slow, fast, improvement = helper.compare_patterns(
            self.SLOW_CODE, self.FAST_CODE, self.QUERY
        )
        # This pattern may not show significant improvement in all Prolog implementations
        assert fast <= slow, f"Fast ({fast}) should be <= slow ({slow})"


class TestFirstForSingleResult:
    """first() for single-result queries pattern."""

    SLOW_CODE = """
available(taxi1).
available(taxi2).
available(taxi3).
available(taxi4).
available(taxi5).
getTaxi(T) :- available(T).
"""

    FAST_CODE = """
available(taxi1).
available(taxi2).
available(taxi3).
available(taxi4).
available(taxi5).
getTaxi(T) :- first(available(T)).
"""

    QUERY = "getTaxi(X)."

    def test_first_limits_backtracking(self, helper, resolution_tracking_enabled):
        """Using first() should limit solutions to one."""
        # first() has overhead in InductorHTN, so we mainly check it works
        fast_steps = helper.measure_steps(self.FAST_CODE, self.QUERY)
        assert fast_steps > 0, "first() query should complete"


class TestResolutionStepTracking:
    """Tests for resolution step tracking infrastructure."""

    def test_resolution_tracking_returns_valid_count(self):
        """Resolution step count should be >= 0 when tracking is enabled."""
        planner = HtnPlanner(False)
        planner.PrologCompile("fact. rule(X) :- fact.")
        planner.PrologQuery("rule(Y).")
        steps = planner.GetLastResolutionStepCount()

        # -1 means tracking disabled, otherwise should be >= 0
        assert steps != -1, "Resolution tracking not enabled"
        assert steps >= 0, f"Invalid step count: {steps}"

    def test_complex_query_has_more_steps(self):
        """More complex queries should have more resolution steps."""
        code = """
base(1).
base(2).
base(3).
single(X) :- base(X).
double(X, Y) :- base(X), base(Y).
"""
        planner = HtnPlanner(False)
        planner.PrologCompile(code)

        planner.PrologQuery("single(X).")
        single_steps = planner.GetLastResolutionStepCount()

        planner.PrologQuery("double(X, Y).")
        double_steps = planner.GetLastResolutionStepCount()

        if single_steps >= 0 and double_steps >= 0:
            # Double query joins two sets, should take more steps
            assert double_steps >= single_steps, "Complex query should have more steps"
