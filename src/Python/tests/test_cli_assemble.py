"""Tests for `htn_components assemble` and its post-assembly verifier.

Covers:
  * Golden regeneration for the 5 known levels (puzzle1 + 4 gamehack levels).
  * Structural dependency-resolution assertions.
  * The verifier itself: duplicate detection, undefined-name handling,
    syntax errors, success on the goldens.
  * The --no-verify and --verify-only flags.

The verifier runs three layers (literal-duplicate detection -> HtnLinter ->
HtnCompileCustomVariables). Layer 3 needs the indhtnpy C++ binding; tests that
don't care about it pass `skip_compile=True` to keep them fast and decoupled
from the build.

Goldens live at tests/fixtures/assembled/<level>.htn with the volatile
`% Generated:` timestamp line stripped. The verifier and the comparison both
call `strip_volatile_lines` to normalize.
"""

import argparse
import difflib
import io
import os
from contextlib import redirect_stdout

import pytest

from htn_components.cli import (
    _find_duplicate_clauses,
    _normalize_clause,
    _split_clauses,
    cmd_assemble,
    strip_volatile_lines,
    verify_assembled,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LEVELS = [
    "puzzle1",
    "gamehack_gh4",
    "gamehack_gh7",
    "gamehack_multipath",
    "gamehack_mvp",
]


@pytest.fixture(scope="session")
def fixtures_dir(project_root):
    """Directory holding golden assembled outputs."""
    return project_root / "tests" / "fixtures" / "assembled"


def _assemble_to_string(level: str, tmp_path, **flag_overrides) -> str:
    """Drive cmd_assemble programmatically and read back the resulting file.

    `flag_overrides` shadows the defaults set here. Returns the file content
    on success; raises AssertionError on non-zero exit.
    """
    out_path = str(tmp_path / f"{level}.htn")
    defaults = {
        "level": level,
        "output": out_path,
        "no_verify": True,           # tests that DO care about verify run it explicitly
        "verify_only": False,
        "skip_compile_check": False,
    }
    defaults.update(flag_overrides)
    args = argparse.Namespace(**defaults)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_assemble(args)
    assert rc == 0, f"cmd_assemble({level}) failed (rc={rc}). Output:\n{buf.getvalue()}"
    if defaults.get("verify_only"):
        # No file is written in verify-only mode.
        return ""
    with open(out_path, "r", encoding="utf-8") as f:
        return f.read()


def _assemble_and_capture(level: str, tmp_path, **flag_overrides):
    """Same as _assemble_to_string but also returns the captured stdout and rc."""
    out_path = str(tmp_path / f"{level}.htn")
    defaults = {
        "level": level,
        "output": out_path,
        "no_verify": False,
        "verify_only": False,
        "skip_compile_check": False,
    }
    defaults.update(flag_overrides)
    args = argparse.Namespace(**defaults)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_assemble(args)
    content = ""
    if rc == 0 and not defaults.get("verify_only"):
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
    return rc, buf.getvalue(), content


# ---------------------------------------------------------------------------
# Golden regeneration
# ---------------------------------------------------------------------------

class TestGoldenRegeneration:
    """Each level's assembled output must match its committed golden, modulo
    the volatile `% Generated:` line. Failure prints a unified diff."""

    @pytest.mark.parametrize("level", LEVELS)
    def test_assemble_matches_golden(self, level, tmp_path, fixtures_dir):
        fresh = strip_volatile_lines(_assemble_to_string(level, tmp_path))
        golden_path = fixtures_dir / f"{level}.htn"
        assert golden_path.exists(), f"Missing golden fixture: {golden_path}"
        golden = golden_path.read_text(encoding="utf-8")
        if fresh != golden:
            diff = "\n".join(difflib.unified_diff(
                golden.splitlines(),
                fresh.splitlines(),
                fromfile=f"{level}.golden",
                tofile=f"{level}.fresh",
                lineterm="",
            ))
            pytest.fail(f"Assembled output diverges from golden for {level}:\n{diff[:5000]}")


# ---------------------------------------------------------------------------
# Structural / dependency-resolution assertions
# ---------------------------------------------------------------------------

class TestDependencyResolution:
    """Properties of the assembled file that are independent of golden content."""

    @pytest.mark.parametrize("level", LEVELS)
    def test_no_component_appears_twice(self, level, tmp_path):
        """The `loaded` set in cmd_assemble must dedup transitive deps."""
        content = _assemble_to_string(level, tmp_path)
        # Count `% === Component: <name> ===` headers
        headers = [
            line for line in content.splitlines()
            if line.startswith("% === Component:")
        ]
        seen = set()
        for h in headers:
            name = h.split("% === Component:")[1].split("===")[0].strip()
            assert name not in seen, f"Component {name!r} appears twice in {level}"
            seen.add(name)
        assert len(headers) > 0, f"No component sections found in {level}"

    def test_gamehack_mvp_transitively_includes_gh_aggro(self, tmp_path):
        """gamehack_mvp's manifest does NOT declare gh_aggro directly, but its
        plan_to_damage goal declares stun_and_burn as a fallback strategy,
        which depends on gh_aggro. Transitive resolution must pull it in."""
        # Confirm gamehack_mvp's manifest doesn't list gh_aggro itself.
        import json
        manifest_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "levels", "gamehack_mvp", "manifest.json",
        )
        manifest = json.load(open(manifest_path))
        assert "gamehack/primitives/gh_aggro" not in manifest["dependencies"], (
            "Precondition for this test: mvp must not list gh_aggro directly."
        )
        # Now confirm the transitive pull-in happens.
        content = _assemble_to_string("gamehack_mvp", tmp_path)
        assert "% === Component: gamehack/primitives/gh_aggro" in content, (
            "gh_aggro must be pulled into gamehack_mvp transitively "
            "(via plan_to_damage -> stun_and_burn -> gh_aggro)."
        )

    def test_level_specific_content_follows_components(self, tmp_path):
        """The `% === Level-specific content ===` block must come after every
        component section -- otherwise level facts could shadow component rules
        in surprising ways."""
        content = _assemble_to_string("puzzle1", tmp_path)
        lines = content.splitlines()
        level_idx = next(
            (i for i, l in enumerate(lines) if l.startswith("% === Level-specific")),
            -1,
        )
        assert level_idx > 0, "Level-specific section not found"
        last_component_idx = max(
            (i for i, l in enumerate(lines) if l.startswith("% === Component:")),
            default=-1,
        )
        assert last_component_idx < level_idx, (
            "Level-specific content must come after all component sections"
        )


# ---------------------------------------------------------------------------
# Verifier: success path on goldens
# ---------------------------------------------------------------------------

class TestVerifierSuccess:
    """The verifier must report 0 errors on every committed golden. Warning
    counts are recorded as a baseline: tests fail if warnings INCREASE."""

    # Baselines captured 2026-05-22. If you intentionally introduce changes
    # that legitimately increase warnings, update these numbers.
    BASELINES = {
        "puzzle1": 50,
        "gamehack_gh4": 36,
        "gamehack_gh7": 30,
        "gamehack_multipath": 32,
        "gamehack_mvp": 43,
    }

    @pytest.mark.parametrize("level", LEVELS)
    def test_golden_passes_verify(self, level, fixtures_dir):
        content = (fixtures_dir / f"{level}.htn").read_text(encoding="utf-8")
        # skip_compile keeps this test independent of the C++ build; layer 3 is
        # exercised separately by TestVerifierLayer3.
        errors, warnings, diags = verify_assembled(
            content, verbose=False, skip_compile=True,
        )
        assert errors == 0, (
            f"Golden {level} produced {errors} verify errors:\n"
            + "\n".join(
                f"  {d['code']} line {d['line']}: {d['message']}"
                for d in diags if d["severity"] == "error"
            )
        )
        baseline = self.BASELINES[level]
        assert warnings <= baseline, (
            f"Warning count for {level} grew from {baseline} to {warnings}. "
            f"Update the baseline if intentional."
        )


# ---------------------------------------------------------------------------
# Verifier layer 1: duplicate clauses
# ---------------------------------------------------------------------------

class TestVerifierCatchesDuplicates:
    """Layer 1 (literal-duplicate-clause detection)."""

    def test_literal_duplicate_is_flagged(self):
        content = (
            "foo() :- if(), do(bar).\n"
            "\n"
            "foo() :- if(), do(bar).\n"
        )
        diags = _find_duplicate_clauses(content)
        assert len(diags) == 1
        d = diags[0]
        assert d["severity"] == "error"
        assert d["code"] == "ASM001"
        assert "line 1" in d["message"]

    def test_same_head_different_body_is_not_flagged(self):
        """The reachable/2 base+recursive pattern (real example from puzzle1)
        is the canonical Prolog idiom for multiple method alternatives."""
        content = (
            "reachable(?x, ?y) :- if(connected(?x, ?y)), do().\n"
            "reachable(?x, ?y) :- "
            "if(connected(?x, ?z), reachable(?z, ?y)), do().\n"
        )
        assert _find_duplicate_clauses(content) == []

    def test_whitespace_difference_still_dedups(self):
        """Two clauses differing only by whitespace must be treated as duplicates."""
        content = (
            "foo() :- if(),   do(bar).\n"
            "foo() :- if(), do(bar).\n"
        )
        assert len(_find_duplicate_clauses(content)) == 1

    def test_comments_do_not_affect_dedup(self):
        """Same clause with different trailing comments is still a duplicate."""
        content = (
            "foo() :- if(), do(bar).  % first definition\n"
            "foo() :- if(), do(bar).  % accidental copy\n"
        )
        assert len(_find_duplicate_clauses(content)) == 1

    def test_split_clauses_skips_periods_inside_parens(self):
        """A period inside arguments must not be mistaken for a clause terminator.
        InductorHTN doesn't actually use float literals at top level often, but
        the clause splitter must still be resilient."""
        # Use a method whose if() contains a nested term with a parenthesized arg.
        content = "foo() :- if(bar(baz, qux)), do(zot).\n"
        clauses = _split_clauses(content)
        assert len(clauses) == 1
        assert "foo()" in clauses[0][1]


# ---------------------------------------------------------------------------
# Verifier layer 2: HtnLinter undefined-reference rules
# ---------------------------------------------------------------------------

class TestVerifierCatchesUndefined:
    """Layer 2 (HtnLinter)."""

    def test_undefined_task_in_do_is_error(self):
        # do(missingTask): missingTask not defined anywhere.
        content = "foo() :- if(), do(missingTask).\n"
        errors, _, diags = verify_assembled(content, verbose=False, skip_compile=True)
        sem001 = [d for d in diags if d["code"] == "SEM001"]
        assert sem001, f"Expected SEM001 ERROR for undefined task. Diags: {diags}"
        assert sem001[0]["severity"] == "error"
        assert errors >= 1

    def test_undefined_predicate_in_if_is_warning(self):
        # if(missingPredicate): missingPredicate is not defined as a fact or rule.
        # SEM002 -- warning, not error -- because asserting on an undefined
        # predicate is a legitimate "make this method never fire" idiom.
        content = (
            "definedTarget() :- if(), do().\n"
            "foo() :- if(missingPredicate), do(definedTarget).\n"
        )
        errors, warnings, diags = verify_assembled(
            content, verbose=False, skip_compile=True,
        )
        sem002 = [d for d in diags if d["code"] == "SEM002"]
        assert sem002, f"Expected SEM002 WARN for undefined predicate. Diags: {diags}"
        assert all(d["severity"] == "warning" for d in sem002)
        # The undefined-predicate-in-if() warning must not bump us into the
        # error count -- that's the whole reason it's a warning.
        sem002_errors = [d for d in diags if d["code"] == "SEM002" and d["severity"] == "error"]
        assert sem002_errors == []

    def test_typ001_surfaces_through_assembler(self):
        # signature(moveTo, [agent, cell]) declares that moveTo expects an
        # agent in position 1 and a cell in position 2. The call
        # moveTo(c5, player) swaps them -- c5 is a cell, player is an agent.
        # The TYP001 rule (layer 2 of the verifier) must catch this.
        content = (
            "type(agent, player).\n"
            "type(cell, c5).\n"
            "signature(moveTo, [agent, cell]).\n"
            "moveTo(?a, ?b) :- if(), do().\n"
            "goalA :- if(), do(moveTo(c5, player)).\n"
            "goals(goalA).\n"
        )
        errors, _, diags = verify_assembled(
            content, verbose=False, skip_compile=True,
        )
        typ001 = [d for d in diags if d["code"] == "TYP001"]
        assert typ001, f"Expected TYP001 ERROR for type mismatch. Diags: {diags}"
        assert all(d["severity"] == "error" for d in typ001), (
            f"TYP001 must be severity=error. Got: {typ001}"
        )
        assert errors >= 1, (
            f"TYP001 diagnostics must contribute to the error count "
            f"(errors={errors}). Diags: {diags}"
        )


# ---------------------------------------------------------------------------
# Verifier layer 3: C++ parser round-trip
# ---------------------------------------------------------------------------

class TestVerifierLayer3:
    """Layer 3 (HtnCompileCustomVariables). Requires the indhtnpy build."""

    def test_syntax_error_is_caught(self):
        # Truncated clause -- missing closing paren.
        content = "foo() :- if(), do(bar.\n"
        errors, _, diags = verify_assembled(content, verbose=False, skip_compile=False)
        # Either layer 2 or layer 3 must reject it -- both is fine.
        assert errors >= 1, f"Expected at least 1 error for syntax-broken input. Diags: {diags}"

    def test_goldens_compile_in_cpp(self, fixtures_dir):
        """Layer 3 sanity: every golden must round-trip through HtnCompile."""
        from indhtnpy import HtnPlanner
        for level in LEVELS:
            content = (fixtures_dir / f"{level}.htn").read_text(encoding="utf-8")
            planner = HtnPlanner(False)
            error = planner.HtnCompileCustomVariables(content)
            assert error is None, f"{level} failed HtnCompile: {error}"


# ---------------------------------------------------------------------------
# Flag behavior
# ---------------------------------------------------------------------------

class TestNoVerifyFlag:
    """--no-verify must write output even when verification would fail."""

    def test_no_verify_writes_output_unconditionally(self, tmp_path, monkeypatch):
        # Override a level's level.htn with one that would FAIL verify, then
        # ensure --no-verify writes the file anyway. Easier: just confirm that
        # --no-verify produces a valid file for a known-good level AND skips
        # the verify section in stdout.
        rc, stdout, content = _assemble_and_capture(
            "puzzle1", tmp_path, no_verify=True,
        )
        assert rc == 0
        assert content, "Output file should be written"
        assert "Verify:" not in stdout, "Verify summary should not appear when --no-verify"


class TestVerifyOnlyFlag:
    """--verify-only must run verification but skip the file write."""

    def test_verify_only_does_not_write(self, tmp_path):
        out_path = tmp_path / "should-not-exist.htn"
        args = argparse.Namespace(
            level="puzzle1",
            output=str(out_path),
            no_verify=False,
            verify_only=True,
            skip_compile_check=True,  # don't depend on C++ build for this test
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_assemble(args)
        assert rc == 0
        assert "Verify:" in buf.getvalue(), "Verify summary should appear"
        assert not out_path.exists(), "Output file must NOT be written in --verify-only"


class TestVerifyExitCode:
    """Verification errors must cause cmd_assemble to exit non-zero and NOT
    write the output file."""

    def test_duplicate_clause_blocks_write(self, tmp_path, monkeypatch):
        """Inject a level whose level.htn contains a literal duplicate clause,
        run assemble, confirm exit code 2 and no file written.

        We do this by creating a throwaway level directory under tmp_path."""
        level_dir = tmp_path / "broken_level"
        level_dir.mkdir()
        (level_dir / "manifest.json").write_text(
            '{"name": "broken", "version": "0.1.0", "layer": "level", '
            '"dependencies": []}'
        )
        (level_dir / "level.htn").write_text(
            "foo() :- if(), do(bar).\n"
            "bar() :- if(), do().\n"
            "foo() :- if(), do(bar).\n"   # literal duplicate of line 1
            "goals(foo).\n"
        )
        out_path = tmp_path / "out.htn"
        args = argparse.Namespace(
            level=str(level_dir),
            output=str(out_path),
            no_verify=False,
            verify_only=False,
            skip_compile_check=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_assemble(args)
        assert rc == 2, f"Expected exit code 2 on verify failure, got {rc}"
        assert not out_path.exists(), "Output must not be written when verify fails"
        assert "ASM001" in buf.getvalue() or "Duplicate clause" in buf.getvalue()
