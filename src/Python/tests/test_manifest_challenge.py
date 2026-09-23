"""Tests for the optional `challenge` block in manifest.json validation.

Covers:
- Manifest with no challenge block loads without error (backward compat).
- Valid challenge blocks round-trip through from_dict / to_dict.
- Invalid `class` values raise ManifestValidationError.
- Missing required fields (`class`, `behavioral_axes`) raise ManifestValidationError.
- Invalid `expected` subfield values raise ManifestValidationError.
- ChallengeBlock.validate() is invoked on Manifest construction and save/load.
"""

import json
import os
import tempfile

import pytest

from htn_components.manifest import (
    ChallengeBlock,
    ChallengeExpected,
    Manifest,
    ManifestValidationError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_manifest_dict(**overrides) -> dict:
    """Minimal valid manifest dict with optional overrides."""
    d = {
        "name": "test_component",
        "version": "0.1.0",
        "layer": "primitive",
        "description": "Test",
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
    d.update(overrides)
    return d


def _valid_challenge_dict(**overrides) -> dict:
    d = {
        "class": "S",
        "behavioral_axes": ["plan_length", "context_switches"],
        "expected": {
            "min_plans": 2,
            "max_plans": 10,
            "min_distinct_methods": 2,
        },
    }
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Backward compatibility: no challenge block
# ---------------------------------------------------------------------------

class TestNoChallengeBlock:
    def test_manifest_without_challenge_loads_ok(self):
        m = Manifest.from_dict(_base_manifest_dict())
        assert m.challenge is None

    def test_manifest_without_challenge_serializes_without_challenge_key(self):
        m = Manifest.from_dict(_base_manifest_dict())
        d = m.to_dict()
        assert "challenge" not in d

    def test_existing_manifests_unaffected(self):
        """Existing component manifests (no challenge key) still load."""
        for layer in ["primitive", "strategy", "goal", "level"]:
            m = Manifest.from_dict(_base_manifest_dict(layer=layer))
            assert m.challenge is None


# ---------------------------------------------------------------------------
# Valid challenge blocks
# ---------------------------------------------------------------------------

class TestValidChallengeBlock:
    def test_all_fields_accepted(self):
        data = _base_manifest_dict(challenge=_valid_challenge_dict())
        m = Manifest.from_dict(data)
        assert m.challenge is not None
        assert m.challenge.cls == "S"
        assert m.challenge.behavioral_axes == ["plan_length", "context_switches"]
        assert m.challenge.expected.min_plans == 2
        assert m.challenge.expected.max_plans == 10
        assert m.challenge.expected.min_distinct_methods == 2

    @pytest.mark.parametrize("cls", ["S", "P", "C", "O"])
    def test_all_valid_classes_accepted(self, cls):
        data = _base_manifest_dict(challenge=_valid_challenge_dict(**{"class": cls}))
        m = Manifest.from_dict(data)
        assert m.challenge.cls == cls

    def test_empty_behavioral_axes_accepted(self):
        """Empty list is a valid (if unusual) behavioral_axes."""
        data = _base_manifest_dict(
            challenge=_valid_challenge_dict(behavioral_axes=[])
        )
        m = Manifest.from_dict(data)
        assert m.challenge.behavioral_axes == []

    def test_challenge_without_expected_accepted(self):
        """The `expected` sub-object is optional."""
        raw = {"class": "P", "behavioral_axes": ["branching_factor"]}
        data = _base_manifest_dict(challenge=raw)
        m = Manifest.from_dict(data)
        assert m.challenge.expected.min_plans is None
        assert m.challenge.expected.max_plans is None
        assert m.challenge.expected.min_distinct_methods is None

    def test_challenge_with_partial_expected_accepted(self):
        raw = {"class": "C", "behavioral_axes": ["depth"], "expected": {"min_plans": 1}}
        data = _base_manifest_dict(challenge=raw)
        m = Manifest.from_dict(data)
        assert m.challenge.expected.min_plans == 1
        assert m.challenge.expected.max_plans is None


# ---------------------------------------------------------------------------
# Round-trip serialization
# ---------------------------------------------------------------------------

class TestChallengeRoundTrip:
    def test_to_dict_includes_challenge(self):
        data = _base_manifest_dict(challenge=_valid_challenge_dict())
        m = Manifest.from_dict(data)
        d = m.to_dict()
        assert "challenge" in d
        assert d["challenge"]["class"] == "S"
        assert d["challenge"]["behavioral_axes"] == ["plan_length", "context_switches"]
        assert d["challenge"]["expected"]["min_plans"] == 2

    def test_round_trip_via_json_file(self, tmp_path):
        data = _base_manifest_dict(challenge=_valid_challenge_dict())
        m = Manifest.from_dict(data)

        path = str(tmp_path / "manifest.json")
        m.save(path)

        m2 = Manifest.load(path)
        assert m2.challenge is not None
        assert m2.challenge.cls == "S"
        assert m2.challenge.behavioral_axes == ["plan_length", "context_switches"]
        assert m2.challenge.expected.max_plans == 10

    def test_expected_empty_omitted_from_dict(self):
        raw = {"class": "O", "behavioral_axes": ["x"]}
        data = _base_manifest_dict(challenge=raw)
        m = Manifest.from_dict(data)
        d = m.to_dict()
        # expected is empty — it should be omitted rather than serialized as {}
        assert "expected" not in d["challenge"]

    def test_no_challenge_survives_save_load(self, tmp_path):
        m = Manifest.from_dict(_base_manifest_dict())
        path = str(tmp_path / "manifest.json")
        m.save(path)
        m2 = Manifest.load(path)
        assert m2.challenge is None


# ---------------------------------------------------------------------------
# Invalid class value
# ---------------------------------------------------------------------------

class TestInvalidChallengeClass:
    @pytest.mark.parametrize("bad_class", ["X", "s", "A", "Z", "", "SS", "1"])
    def test_invalid_class_raises(self, bad_class):
        data = _base_manifest_dict(
            challenge=_valid_challenge_dict(**{"class": bad_class})
        )
        with pytest.raises(ManifestValidationError, match="challenge.class"):
            Manifest.from_dict(data)

    def test_error_message_lists_valid_classes(self):
        data = _base_manifest_dict(challenge=_valid_challenge_dict(**{"class": "X"}))
        with pytest.raises(ManifestValidationError) as exc_info:
            Manifest.from_dict(data)
        msg = str(exc_info.value)
        for cls in ("S", "P", "C", "O"):
            assert cls in msg


# ---------------------------------------------------------------------------
# Missing required fields
# ---------------------------------------------------------------------------

class TestMissingRequiredChallengeFields:
    def test_missing_class_raises(self):
        raw = {"behavioral_axes": ["plan_length"]}
        data = _base_manifest_dict(challenge=raw)
        with pytest.raises(ManifestValidationError, match="class"):
            Manifest.from_dict(data)

    def test_missing_behavioral_axes_raises(self):
        raw = {"class": "S"}
        data = _base_manifest_dict(challenge=raw)
        with pytest.raises(ManifestValidationError, match="behavioral_axes"):
            Manifest.from_dict(data)


# ---------------------------------------------------------------------------
# Invalid expected sub-fields
# ---------------------------------------------------------------------------

class TestInvalidExpectedFields:
    def test_min_plans_negative_raises(self):
        challenge = _valid_challenge_dict(expected={"min_plans": -1})
        data = _base_manifest_dict(challenge=challenge)
        with pytest.raises(ManifestValidationError, match="min_plans"):
            Manifest.from_dict(data)

    def test_min_plans_zero_accepted(self):
        challenge = _valid_challenge_dict(expected={"min_plans": 0})
        data = _base_manifest_dict(challenge=challenge)
        m = Manifest.from_dict(data)
        assert m.challenge.expected.min_plans == 0

    def test_max_plans_zero_raises(self):
        challenge = _valid_challenge_dict(expected={"max_plans": 0})
        data = _base_manifest_dict(challenge=challenge)
        with pytest.raises(ManifestValidationError, match="max_plans"):
            Manifest.from_dict(data)

    def test_max_plans_one_accepted(self):
        challenge = _valid_challenge_dict(expected={"max_plans": 1})
        data = _base_manifest_dict(challenge=challenge)
        m = Manifest.from_dict(data)
        assert m.challenge.expected.max_plans == 1

    def test_min_distinct_methods_zero_raises(self):
        challenge = _valid_challenge_dict(expected={"min_distinct_methods": 0})
        data = _base_manifest_dict(challenge=challenge)
        with pytest.raises(ManifestValidationError, match="min_distinct_methods"):
            Manifest.from_dict(data)

    def test_min_distinct_methods_one_accepted(self):
        challenge = _valid_challenge_dict(expected={"min_distinct_methods": 1})
        data = _base_manifest_dict(challenge=challenge)
        m = Manifest.from_dict(data)
        assert m.challenge.expected.min_distinct_methods == 1

    def test_behavioral_axes_non_list_raises(self):
        raw = {"class": "S", "behavioral_axes": "plan_length"}
        data = _base_manifest_dict(challenge=raw)
        with pytest.raises(ManifestValidationError, match="behavioral_axes"):
            Manifest.from_dict(data)

    def test_behavioral_axes_non_string_entry_raises(self):
        raw = {"class": "S", "behavioral_axes": ["ok", 42]}
        data = _base_manifest_dict(challenge=raw)
        with pytest.raises(ManifestValidationError, match="behavioral_axes"):
            Manifest.from_dict(data)


# ---------------------------------------------------------------------------
# ChallengeBlock standalone API
# ---------------------------------------------------------------------------

class TestChallengeBlockDirectAPI:
    def test_from_dict_to_dict_roundtrip(self):
        raw = {
            "class": "C",
            "behavioral_axes": ["depth"],
            "expected": {"min_plans": 1, "max_plans": 5},
        }
        cb = ChallengeBlock.from_dict(raw)
        assert cb.cls == "C"
        result = cb.to_dict()
        assert result["class"] == "C"
        assert result["expected"]["min_plans"] == 1

    def test_validate_ok_does_not_raise(self):
        cb = ChallengeBlock(cls="S", behavioral_axes=["x"])
        cb.validate()  # should not raise

    def test_validate_bad_class_raises(self):
        cb = ChallengeBlock(cls="Z", behavioral_axes=["x"])
        with pytest.raises(ManifestValidationError):
            cb.validate()


# ---------------------------------------------------------------------------
# ChallengeExpected.check_report (fix 6)
# ---------------------------------------------------------------------------

class TestChallengeExpectedCheckReport:
    """check_report enforces all declared bounds against an evaluate_level
    result dict.  Violations are returned as strings, not raised."""

    def _make_report(self, plan_count=3, operator_variety=None):
        return {
            "plan_count": plan_count,
            "operator_variety": operator_variety if operator_variety is not None else ["opA", "opB"],
        }

    def test_no_bounds_returns_no_violations(self):
        exp = ChallengeExpected()
        assert exp.check_report(self._make_report()) == []

    def test_min_plans_satisfied(self):
        exp = ChallengeExpected(min_plans=2)
        assert exp.check_report(self._make_report(plan_count=2)) == []

    def test_min_plans_violated(self):
        exp = ChallengeExpected(min_plans=5)
        violations = exp.check_report(self._make_report(plan_count=3))
        assert len(violations) == 1
        assert "min_plans" in violations[0]
        assert "3" in violations[0]

    def test_max_plans_satisfied(self):
        exp = ChallengeExpected(max_plans=10)
        assert exp.check_report(self._make_report(plan_count=10)) == []

    def test_max_plans_violated(self):
        exp = ChallengeExpected(max_plans=2)
        violations = exp.check_report(self._make_report(plan_count=5))
        assert len(violations) == 1
        assert "max_plans" in violations[0]

    def test_min_distinct_methods_satisfied(self):
        exp = ChallengeExpected(min_distinct_methods=2)
        assert exp.check_report(self._make_report(operator_variety=["opA", "opB"])) == []

    def test_min_distinct_methods_violated(self):
        exp = ChallengeExpected(min_distinct_methods=3)
        violations = exp.check_report(self._make_report(operator_variety=["opA"]))
        assert len(violations) == 1
        assert "min_distinct_methods" in violations[0]
        assert "1" in violations[0]

    def test_all_three_bounds_can_fail_simultaneously(self):
        exp = ChallengeExpected(min_plans=5, max_plans=2, min_distinct_methods=4)
        violations = exp.check_report(self._make_report(plan_count=3, operator_variety=["opA"]))
        # min_plans: 3 < 5 → violation
        # max_plans: 3 > 2 → violation
        # min_distinct_methods: 1 < 4 → violation
        assert len(violations) == 3

    def test_missing_report_keys_default_gracefully(self):
        """check_report must not crash when optional keys are absent."""
        exp = ChallengeExpected(min_plans=1, min_distinct_methods=1)
        violations = exp.check_report({})
        # plan_count defaults to 0 → min_plans violated
        assert any("min_plans" in v for v in violations)
