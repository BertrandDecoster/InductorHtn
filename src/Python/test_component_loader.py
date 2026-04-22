"""Loader-level contract tests.

Covers verification items 5 and 6 from the Component System Hardening plan:
  - duplicate-operator detection across components must raise LoadError
  - unsatisfied `requires` sig in a loaded component must raise LoadError
    from verify_contracts().

Run via pytest from anywhere; the file stands up its own fake project tree
in tmp_path so it doesn't touch the real components/ directory.
"""

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from htn_components.loader import ComponentLoader, LoadError  # noqa: E402
from indhtnpy import HtnPlanner  # noqa: E402


def _write_component(
    project_root,
    rel_path,
    *,
    src_htn,
    layer="primitive",
    dependencies=None,
    provides=None,
    requires=None,
):
    """Create a component directory with manifest.json + src.htn."""
    full = os.path.join(project_root, "components", rel_path)
    os.makedirs(full, exist_ok=True)
    manifest = {
        "name": os.path.basename(rel_path),
        "version": "0.1.0",
        "layer": layer,
        "description": "fixture",
        "dependencies": dependencies or [],
        "certified": False,
        "certification": {
            "linter": False,
            "tests_pass": False,
            "design_match": False,
            "last_checked": "1970-01-01T00:00:00",
        },
        "provides": provides or [],
        "requires": requires or [],
    }
    with open(os.path.join(full, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(full, "src.htn"), "w") as f:
        f.write(src_htn)
    return full


def test_duplicate_operator_across_components_raises(tmp_path):
    """Plan step 5: two components defining `opApplyTag/2` → LoadError
    naming both components and the signature."""
    project_root = str(tmp_path)
    os.makedirs(os.path.join(project_root, "components"), exist_ok=True)

    _write_component(
        project_root,
        "primitives/dup_a",
        src_htn="opApplyTag(?tag, ?target) :- del(), add(hasTag(?target, ?tag)).\n",
        provides=["opApplyTag/2"],
    )
    _write_component(
        project_root,
        "primitives/dup_b",
        src_htn="opApplyTag(?tag, ?target) :- del(hasTag(?target, ?tag)), add().\n",
        provides=["opApplyTag/2"],
    )
    _write_component(
        project_root,
        "goals/dup_root",
        src_htn="rootGoal() :- if(), do().\n",
        layer="goal",
        dependencies=["primitives/dup_a", "primitives/dup_b"],
        provides=["rootGoal/0"],
    )

    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, project_root)

    with pytest.raises(LoadError) as excinfo:
        loader.load("goals/dup_root")

    msg = str(excinfo.value)
    assert "opApplyTag/2" in msg, f"error should name the duplicated sig: {msg}"
    assert "primitives/dup_a" in msg, f"error should name first owner: {msg}"
    assert "primitives/dup_b" in msg, f"error should name second owner: {msg}"


def test_unsatisfied_requires_raises_on_verify(tmp_path):
    """Plan step 6: component declaring requires: [nonexistent/0] with no
    provider in its dep closure → verify_contracts() raises LoadError."""
    project_root = str(tmp_path)
    os.makedirs(os.path.join(project_root, "components"), exist_ok=True)

    _write_component(
        project_root,
        "primitives/needy",
        src_htn=(
            "provided() :- if(), do(nonexistent).\n"
        ),
        provides=["provided/0"],
        requires=["nonexistent/0"],
    )

    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, project_root)

    # load() succeeds — contracts aren't checked until verify_contracts().
    loader.load("primitives/needy")

    with pytest.raises(LoadError) as excinfo:
        loader.verify_contracts()

    msg = str(excinfo.value)
    assert "nonexistent/0" in msg, f"error should name the missing sig: {msg}"
    assert "primitives/needy" in msg, f"error should name the requester: {msg}"


def test_satisfied_requires_verifies_clean(tmp_path):
    """Positive control: when a sibling provides the required sig, the
    closure verifies without error."""
    project_root = str(tmp_path)
    os.makedirs(os.path.join(project_root, "components"), exist_ok=True)

    _write_component(
        project_root,
        "primitives/provider",
        src_htn="helper() :- del(), add(done).\n",
        provides=["helper/0"],
    )
    _write_component(
        project_root,
        "primitives/caller",
        src_htn="entry() :- if(), do(helper).\n",
        dependencies=["primitives/provider"],
        provides=["entry/0"],
        requires=["helper/0"],
    )

    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, project_root)

    loader.load("primitives/caller")
    loader.verify_contracts()  # must not raise
