"""
CLI for HTN component management.

Commands:
    new <component_path>     Create new component from template
    test <component_path>    Run tests for a component
    certify <component_path> Certify component (runs all checks)
    status                   List all components with status
    assemble <level_path>    Assemble level into single HTN file
    coverage <component_path> Check design-to-test coverage
"""

import argparse
import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Optional, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .manifest import (
    Manifest, CertificationStatus, Parameter,
    find_component_root, resolve_component_path,
    get_component_manifest, list_all_components
)


def find_project_root() -> str:
    """Find the project root (contains components/ and src/)."""
    current = os.path.dirname(os.path.abspath(__file__))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "components")):
            return current
        current = os.path.dirname(current)
    # Fallback
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


PROJECT_ROOT = find_project_root()
COMPONENTS_ROOT = os.path.join(PROJECT_ROOT, "components")


# =============================================================================
# Template Content
# =============================================================================

def get_src_template(layer: str, name: str) -> str:
    """Get template for src.htn based on layer."""
    if layer == "primitive":
        return f"""% {name} - Primitive component
% Core operators and methods for {name}

% === Operators ===

% Example operator
op{name.title()}(?entity) :-
    del(),
    add({name}Applied(?entity)).

% === Methods ===

% Example method
{name}(?entity) :-
    if(canApply{name.title()}(?entity)),
    do(op{name.title()}(?entity)).

{name}(?entity) :-
    else, if(),
    do().  % No-op fallback
"""
    elif layer == "strategy":
        return f"""% {name} - Strategy component
% Tactical pattern composing primitives

% === Strategy Methods ===

{name}(?target) :-
    if(canExecute{name.title()}(?target)),
    do(
        % Add primitive calls here
    ).
"""
    elif layer == "goal":
        return f"""% {name} - Goal component
% High-level objective with multiple strategy options

% === Goal Methods ===

{name}(?target) :-
    if(preferredStrategyAvailable(?target)),
    do(primaryStrategy(?target)).

{name}(?target) :-
    else, if(),
    do(fallbackStrategy(?target)).
"""
    else:
        return f"""% {name} component
"""


def get_design_template(name: str, layer: str) -> str:
    """Get template for design.md."""
    return f"""# {name.replace('_', ' ').title()}

## Purpose

[Describe what this component does and why it exists]

## Layer

{layer}

## Dependencies

[List component dependencies, e.g., "primitives/locomotion"]

## Operators

| Operator | Description |
|----------|-------------|
| `op{name.title()}(?entity)` | [Description] |

## Methods

| Method | Description |
|--------|-------------|
| `{name}(?entity)` | [Description] |

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| [paramName] | fact | [value] | [Description] |

## Examples

### Example 1: [Scenario Name]

**Given:**
- [Initial state facts]

**When:**
- `{name}(entity1)`

**Then:**
- Plan contains: `[expected operators]`
- Final state has: `[expected facts]`

### Example 2: [Another Scenario]

**Given:**
- [Initial state facts]

**When:**
- `{name}(entity1)`

**Then:**
- [Expected outcome]

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | [Name] | [Invariant that must always hold] |
| P2 | [Name] | [Another invariant] |
"""


def get_test_template(name: str, layer: str) -> str:
    """Get template for test.py."""
    class_name = ''.join(word.title() for word in name.split('_'))
    return f'''"""Tests for {name} component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class {class_name}Test(HtnTestSuite):
    """Test suite for {name} component."""

    def setup(self):
        """Load the component before tests."""
        # Load component using the component loader
        self.load_component("{layer}s/{name}")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1(self):
        """Example 1: [Scenario Name]

        Given: [Initial state]
        When: {name}(entity1)
        Then: [Expected outcome]
        """
        self.set_state([
            # Add initial facts here
        ])
        self.assert_plan("{name}(entity1).",
            contains=["op{name.title()}"])
        self.assert_state_after("{name}(entity1).",
            has=["{name}Applied(entity1)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1(self):
        """P1: [Property description]"""
        # Property-based test implementation
        pass


def run_tests():
    """Run all tests in this file."""
    suite = {class_name}Test()
    suite.setup()

    # Run all test methods
    for method_name in dir(suite):
        if method_name.startswith("test_"):
            method = getattr(suite, method_name)
            try:
                method()
            except Exception as e:
                suite._record(False, method_name, str(e))

    print(suite.summary())
    return suite.all_passed()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
'''


def get_manifest_template(name: str, layer: str) -> dict:
    """Get template for manifest.json."""
    return {
        "name": name,
        "version": "0.1.0",
        "layer": layer,
        "description": f"{name.replace('_', ' ').title()} component",
        "dependencies": [],
        "certified": False,
        "certification": {
            "linter": False,
            "tests_pass": False,
            "design_match": False,
            "last_checked": None
        },
        "parameters": []
    }


# =============================================================================
# Commands
# =============================================================================

def cmd_new(args) -> int:
    """Create a new component from template."""
    component_path = args.component

    # Parse layer from path
    parts = component_path.split('/')
    if len(parts) < 2:
        print(f"Error: Component path should be 'layer/name', e.g., 'primitives/tags'")
        return 1

    layer_dir = parts[0]
    name = parts[-1]

    # Map directory to layer
    layer_map = {
        "primitives": "primitive",
        "strategies": "strategy",
        "goals": "goal",
        "levels": "level"
    }

    layer = layer_map.get(layer_dir)
    if not layer:
        print(f"Error: Unknown layer directory '{layer_dir}'")
        print(f"Valid options: {list(layer_map.keys())}")
        return 1

    # Create component directory
    full_path = os.path.join(COMPONENTS_ROOT, component_path)

    if os.path.exists(full_path):
        print(f"Error: Component already exists at {full_path}")
        return 1

    os.makedirs(full_path, exist_ok=True)

    # Create files from templates
    files_created = []

    # src.htn
    src_path = os.path.join(full_path, "src.htn")
    with open(src_path, 'w', encoding='utf-8') as f:
        f.write(get_src_template(layer, name))
    files_created.append("src.htn")

    # design.md
    design_path = os.path.join(full_path, "design.md")
    with open(design_path, 'w', encoding='utf-8') as f:
        f.write(get_design_template(name, layer))
    files_created.append("design.md")

    # test.py
    test_path = os.path.join(full_path, "test.py")
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(get_test_template(name, layer))
    files_created.append("test.py")

    # manifest.json
    manifest_path = os.path.join(full_path, "manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(get_manifest_template(name, layer), f, indent=2)
    files_created.append("manifest.json")

    print(f"Created component: {component_path}")
    print(f"Files: {', '.join(files_created)}")
    print(f"\nNext steps:")
    print(f"  1. Edit design.md to define behavior")
    print(f"  2. Edit test.py to encode examples and properties")
    print(f"  3. Edit src.htn to implement")
    print(f"  4. Run: python -m htn_components test {component_path}")

    return 0


def cmd_test(args) -> int:
    """Run tests for a component."""
    try:
        component_path = resolve_component_path(args.component, COMPONENTS_ROOT)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    manifest = get_component_manifest(component_path)
    print(f"Testing component: {manifest.name} v{manifest.version}")
    print("=" * 50)

    results = {
        "linter": False,
        "tests_pass": False
    }

    # Step 1: Run linter on src.htn or level.htn
    src_path = os.path.join(component_path, "src.htn")
    level_path = os.path.join(component_path, "level.htn")
    htn_path = src_path if os.path.exists(src_path) else (level_path if os.path.exists(level_path) else None)
    if htn_path:
        print("\n[1/2] Running linter...")
        lint_result = run_linter(htn_path, component_path)
        results["linter"] = lint_result
        print(f"  Linter: {'PASS' if lint_result else 'FAIL'}")
    else:
        print(f"\n[1/2] Warning: No src.htn or level.htn found")

    # Step 2: Run tests
    test_path = os.path.join(component_path, "test.py")
    if os.path.exists(test_path):
        print("\n[2/2] Running tests...")
        test_result = run_tests(test_path, args.verbose)
        results["tests_pass"] = test_result
        print(f"  Tests: {'PASS' if test_result else 'FAIL'}")
    else:
        print(f"\n[2/2] Warning: No test.py found")

    # Update manifest
    manifest.update_certification(
        linter=results["linter"],
        tests_pass=results["tests_pass"]
    )
    manifest.save(os.path.join(component_path, "manifest.json"))

    # Summary
    print("\n" + "=" * 50)
    all_passed = all(results.values())
    print(f"Result: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")

    return 0 if all_passed else 1


def cmd_certify(args) -> int:
    """Certify a component (runs all checks and marks as certified)."""
    try:
        component_path = resolve_component_path(args.component, COMPONENTS_ROOT)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    manifest = get_component_manifest(component_path)
    print(f"Certifying component: {manifest.name} v{manifest.version}")
    print("=" * 50)

    # Run all checks
    results = {
        "linter": False,
        "tests_pass": False,
        "design_match": False
    }

    # Step 1: Linter
    src_path = os.path.join(component_path, "src.htn")
    level_path = os.path.join(component_path, "level.htn")
    htn_path = src_path if os.path.exists(src_path) else (level_path if os.path.exists(level_path) else None)
    if htn_path:
        print("\n[1/3] Running linter...")
        results["linter"] = run_linter(htn_path, component_path)
        print(f"  Linter: {'PASS' if results['linter'] else 'FAIL'}")

    # Step 2: Tests
    test_path = os.path.join(component_path, "test.py")
    if os.path.exists(test_path):
        print("\n[2/3] Running tests...")
        results["tests_pass"] = run_tests(test_path, args.verbose)
        print(f"  Tests: {'PASS' if results['tests_pass'] else 'FAIL'}")

    # Step 3: Design match (check that design.md examples have tests)
    design_path = os.path.join(component_path, "design.md")
    if os.path.exists(design_path) and os.path.exists(test_path):
        print("\n[3/3] Checking design coverage...")
        passed, report = verify_design_coverage(design_path, test_path, verbose=args.verbose)
        results["design_match"] = passed
        if args.verbose:
            print(report)
        else:
            print(f"  Design coverage: {'PASS' if passed else 'FAIL'}")

    # Update manifest (unless dry-run)
    dry_run = getattr(args, 'dry_run', False)

    if not dry_run:
        manifest.update_certification(
            linter=results["linter"],
            tests_pass=results["tests_pass"],
            design_match=results["design_match"]
        )
        manifest.save(os.path.join(component_path, "manifest.json"))

    # Summary
    print("\n" + "=" * 50)
    if dry_run:
        print("[DRY RUN] Results not saved to manifest")

    # Check if would be certified
    would_certify = all(results.values())
    if would_certify:
        print(f"CERTIFIED: {manifest.name} v{manifest.version}")
        if not dry_run:
            print(f"Timestamp: {manifest.certification.last_checked}")
    else:
        print("NOT CERTIFIED - some checks failed")
        for check, passed in results.items():
            if not passed:
                print(f"  - {check}: FAILED")

    return 0 if would_certify else 1


def cmd_status(args) -> int:
    """List all components with their certification status."""
    components = list_all_components(COMPONENTS_ROOT)

    if not components:
        print("No components found in components/")
        return 0

    print("HTN Components Status")
    print("=" * 70)
    print(f"{'Path':<30} {'Version':<10} {'Certified':<12} {'Status'}")
    print("-" * 70)

    for comp in components:
        if "error" in comp:
            status = f"Error: {comp['error']}"
            certified = "?"
        else:
            certified = "YES" if comp["certified"] else "NO"
            cert = comp["certification"]
            checks = []
            if cert["linter"]:
                checks.append("L")
            if cert["tests_pass"]:
                checks.append("T")
            if cert["design_match"]:
                checks.append("D")
            status = f"[{'/'.join(checks) or '-'}]"
            if cert["last_checked"]:
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(cert["last_checked"])
                    status += f" checked {dt.strftime('%Y-%m-%d')}"
                except:
                    pass

        version = comp.get("version", "?")
        print(f"{comp['path']:<30} {version:<10} {certified:<12} {status}")

    print("-" * 70)
    print(f"Total: {len(components)} components")
    certified_count = sum(1 for c in components if c.get("certified", False))
    print(f"Certified: {certified_count}/{len(components)}")

    return 0


def cmd_assemble(args) -> int:
    """Assemble a level into a single HTN file."""
    level_path = args.level
    output_path = args.output

    # Find level directory
    if os.path.isabs(level_path):
        full_path = level_path
    else:
        full_path = os.path.join(PROJECT_ROOT, "levels", level_path)

    if not os.path.isdir(full_path):
        print(f"Error: Level not found at {full_path}")
        return 1

    manifest_path = os.path.join(full_path, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Error: No manifest.json in level directory")
        return 1

    with open(manifest_path, 'r') as f:
        level_manifest = json.load(f)

    print(f"Assembling level: {level_manifest.get('name', level_path)}")

    # Resolve dependencies
    dependencies = level_manifest.get("dependencies", [])
    assembled_content = []
    assembled_content.append(f"% Assembled level: {level_manifest.get('name', level_path)}")
    assembled_content.append(f"% Generated: {datetime.now().isoformat()}")
    assembled_content.append("")

    # Load dependencies in order
    loaded = set()

    def load_component(comp_name: str, depth: int = 0):
        if comp_name in loaded:
            return

        try:
            comp_path = resolve_component_path(comp_name, COMPONENTS_ROOT)
        except FileNotFoundError:
            print(f"  Warning: Dependency not found: {comp_name}")
            return

        comp_manifest = get_component_manifest(comp_path)

        # Load this component's dependencies first
        for dep in comp_manifest.dependencies:
            load_component(dep, depth + 1)

        # Load component source
        src_path = os.path.join(comp_path, "src.htn")
        if os.path.exists(src_path):
            with open(src_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assembled_content.append(f"% === Component: {comp_name} ===")
            assembled_content.append(content)
            assembled_content.append("")

            loaded.add(comp_name)
            print(f"  {'  ' * depth}Loaded: {comp_name}")

    for dep in dependencies:
        load_component(dep)

    # Load level-specific HTN
    level_htn = os.path.join(full_path, "level.htn")
    if os.path.exists(level_htn):
        with open(level_htn, 'r', encoding='utf-8') as f:
            content = f.read()
        assembled_content.append("% === Level-specific content ===")
        assembled_content.append(content)

    # Write output
    if not output_path:
        output_path = os.path.join(full_path, f"{os.path.basename(level_path)}_assembled.htn")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(assembled_content))

    print(f"\nAssembled to: {output_path}")
    print(f"Components loaded: {len(loaded)}")

    return 0


def cmd_play(args) -> int:
    """Play through a level with step-by-step narrative output."""
    level_path = args.level

    # Find level directory
    if os.path.isabs(level_path):
        full_path = level_path
    else:
        full_path = os.path.join(PROJECT_ROOT, "levels", level_path)

    if not os.path.isdir(full_path):
        print(f"Error: Level not found at {full_path}")
        return 1

    manifest_path = os.path.join(full_path, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Error: No manifest.json in level directory")
        return 1

    with open(manifest_path, 'r') as f:
        level_manifest = json.load(f)

    level_name = level_manifest.get('name', level_path)
    print(f"\n{level_name}")
    print("=" * len(level_name))

    # Import planner
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "Python"))
    from indhtnpy import HtnPlanner

    planner = HtnPlanner(False)

    # Load dependencies (with cycle detection)
    dependencies = level_manifest.get("dependencies", [])
    loaded_deps = set()

    def load_dep(dep_name: str):
        if dep_name in loaded_deps:
            return
        loaded_deps.add(dep_name)

        try:
            dep_path = resolve_component_path(dep_name, COMPONENTS_ROOT)
        except FileNotFoundError:
            print(f"  Warning: Dependency not found: {dep_name}")
            return

        dep_manifest = get_component_manifest(dep_path)
        for sub_dep in dep_manifest.dependencies:
            load_dep(sub_dep)

        src_path = os.path.join(dep_path, "src.htn")
        if os.path.exists(src_path):
            with open(src_path, 'r', encoding='utf-8') as f:
                planner.HtnCompileCustomVariables(f.read())

    for dep in dependencies:
        load_dep(dep)

    # Load level
    level_htn = os.path.join(full_path, "level.htn")
    if os.path.exists(level_htn):
        with open(level_htn, 'r', encoding='utf-8') as f:
            planner.HtnCompileCustomVariables(f.read())

    # Get initial state
    error, facts_json = planner.GetStateFacts()
    if error:
        print(f"Error getting state: {error}")
        return 1

    facts = json.loads(facts_json)

    # Display initial state (filter for interesting facts)
    print("\nInitial State:")
    for fact in facts:
        if fact.startswith("at(") or fact.startswith("isEnemy(") or \
           fact.startswith("hasTag(") or fact.startswith("roomHasHazard("):
            print(f"  - {format_fact_narrative(fact)}")

    # Find the goal (read from level.htn file)
    goal = None
    import re
    with open(level_htn, 'r', encoding='utf-8') as f:
        level_content = f.read()
    goal_match = re.search(r'goals\(([^)]+)\)', level_content)
    if goal_match:
        goal = goal_match.group(1).strip() + "."

    if not goal:
        print("\nError: No goals() directive found in level.htn")
        return 1

    print(f"\nGoal: {goal[:-1]}")

    # Find plan
    error, result = planner.FindAllPlansCustomVariables(goal)
    if error:
        print(f"\nError finding plan: {error}")
        return 1

    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        print("\nNo solution found!")
        return 1

    # Get operators from first solution
    operators = solutions[0] if isinstance(solutions[0], list) else []
    print(f"\nPlan ({len(operators)} operators):")
    print("-" * 50)

    # Step through each operator
    for i, op in enumerate(operators):
        op_str = format_operator(op) if isinstance(op, dict) else str(op)
        print(f"\nStep {i+1}/{len(operators)}: {op_str}")
        print(f"  -> {format_operator_narrative(op_str)}")

    print("-" * 50)

    # Apply solution and show final state
    planner.ApplySolution(0)
    error, final_json = planner.GetStateFacts()
    final_facts = json.loads(final_json) if not error else []

    print("\nFinal State:")
    for fact in final_facts:
        if fact.startswith("at(") or fact.startswith("hasTag("):
            print(f"  - {format_fact_narrative(fact)}")

    print("\nCOMPLETE!")
    return 0


def format_fact_narrative(fact: str) -> str:
    """Convert a fact to a readable narrative."""
    if fact.startswith("at("):
        # at(entity, location) -> entity at location
        inner = fact[3:-1]
        parts = inner.split(",")
        if len(parts) >= 2:
            entity = parts[0].strip()
            location = parts[1].strip()
            return f"{entity} at {location}"
    elif fact.startswith("isEnemy("):
        inner = fact[8:-1]
        return f"{inner} (enemy)"
    elif fact.startswith("hasTag("):
        inner = fact[7:-1]
        parts = inner.split(",")
        if len(parts) >= 2:
            entity = parts[0].strip()
            tag = parts[1].strip()
            return f"{entity} has {tag}"
    elif fact.startswith("roomHasHazard("):
        inner = fact[14:-1]
        parts = inner.split(",")
        if len(parts) >= 2:
            room = parts[0].strip()
            hazard = parts[1].strip()
            return f"{room} has {hazard} hazard"
    return fact


def format_operator(op: dict) -> str:
    """Format an operator dict as a string."""
    if isinstance(op, dict):
        for name, args in op.items():
            if isinstance(args, list):
                arg_strs = []
                for arg in args:
                    if isinstance(arg, dict):
                        for k, v in arg.items():
                            arg_strs.append(k)
                            break
                    else:
                        arg_strs.append(str(arg))
                return f"{name}({', '.join(arg_strs)})"
            return name
    return str(op)


def format_operator_narrative(op_str: str) -> str:
    """Convert an operator to a readable narrative."""
    op_lower = op_str.lower()

    # Extract arguments
    inner = op_str[op_str.find("(")+1:op_str.rfind(")")]
    parts = [p.strip() for p in inner.split(",")] if inner else []

    if "opmoveto" in op_lower:
        if len(parts) >= 3:
            return f"{parts[0]} moves from {parts[1]} to {parts[2]}"
    elif "opgetaggro" in op_lower:
        if len(parts) >= 2:
            return f"{parts[0]} now targets {parts[1]}"
        elif len(parts) >= 1:
            return f"{parts[0]} is now aggro'd"
    elif "oploseaggro" in op_lower:
        if len(parts) >= 2:
            return f"{parts[0]} loses aggro on {parts[1]}"
    elif "opapplyroomtag" in op_lower:
        if len(parts) >= 2:
            return f"{parts[0]} is now {parts[1]}"
    elif "opapplytag" in op_lower:
        if len(parts) >= 2:
            return f"{parts[0]} is now {parts[1]}!"
    elif "opremovetag" in op_lower:
        if len(parts) >= 2:
            return f"{parts[0]} is no longer {parts[1]}"
    elif "opconsumehazard" in op_lower:
        if len(parts) >= 2:
            return f"{parts[1]} hazard in {parts[0]} consumed"
    elif "opactivatehazard" in op_lower:
        if len(parts) >= 2:
            return f"{parts[1]} hazard in {parts[0]} activated"

    return "action completed"


def cmd_trace(args) -> int:
    """Show decomposition tree for a level's plan."""
    level_path = args.level
    custom_goal = args.goal

    # Find level directory
    if os.path.isabs(level_path):
        full_path = level_path
    else:
        full_path = os.path.join(PROJECT_ROOT, "levels", level_path)

    if not os.path.isdir(full_path):
        print(f"Error: Level not found at {full_path}")
        return 1

    manifest_path = os.path.join(full_path, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Error: No manifest.json in level directory")
        return 1

    with open(manifest_path, 'r') as f:
        level_manifest = json.load(f)

    # Import planner
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "Python"))
    from indhtnpy import HtnPlanner

    planner = HtnPlanner(False)

    # Load dependencies (with cycle detection)
    dependencies = level_manifest.get("dependencies", [])
    loaded_deps = set()

    def load_dep(dep_name: str):
        if dep_name in loaded_deps:
            return
        loaded_deps.add(dep_name)

        try:
            dep_path = resolve_component_path(dep_name, COMPONENTS_ROOT)
        except FileNotFoundError:
            print(f"  Warning: Dependency not found: {dep_name}")
            return

        dep_manifest = get_component_manifest(dep_path)
        for sub_dep in dep_manifest.dependencies:
            load_dep(sub_dep)

        src_path = os.path.join(dep_path, "src.htn")
        if os.path.exists(src_path):
            with open(src_path, 'r', encoding='utf-8') as f:
                planner.HtnCompileCustomVariables(f.read())

    for dep in dependencies:
        load_dep(dep)

    # Load level
    level_htn = os.path.join(full_path, "level.htn")
    if os.path.exists(level_htn):
        with open(level_htn, 'r', encoding='utf-8') as f:
            planner.HtnCompileCustomVariables(f.read())

    # Find the goal
    if custom_goal:
        goal = custom_goal if custom_goal.endswith('.') else custom_goal + "."
    else:
        import re
        with open(level_htn, 'r', encoding='utf-8') as f:
            level_content = f.read()
        goal_match = re.search(r'goals\(([^)]+)\)', level_content)
        if goal_match:
            goal = goal_match.group(1).strip() + "."
        else:
            print("Error: No goals() directive found in level.htn")
            return 1

    print(f"\nDecomposition Tree: {goal[:-1]}")
    print("=" * 50)

    # Find plan
    error, result = planner.FindAllPlansCustomVariables(goal)
    if error:
        print(f"\nError finding plan: {error}")
        return 1

    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        print("\nNo solution found!")
        return 1

    # Get decomposition tree
    error, tree_json = planner.GetDecompositionTree(0)
    if error:
        print(f"\nError getting decomposition tree: {error}")
        return 1

    tree_nodes = json.loads(tree_json)

    # Build tree structure
    nodes_by_id = {node.get('nodeID', node.get('id', i)): node for i, node in enumerate(tree_nodes)}

    # Find root nodes (parentNodeID == -1 or not present)
    roots = [n for n in tree_nodes if n.get('parentNodeID', -1) == -1]

    # Build children map
    children_map = {}
    for node in tree_nodes:
        parent_id = node.get('parentNodeID', -1)
        if parent_id not in children_map:
            children_map[parent_id] = []
        children_map[parent_id].append(node)

    # Known strategies for annotation
    known_strategies = {'theBurn', 'theSlipstream', 'theAmbush', 'theSiege'}

    # Print tree recursively
    def print_tree(node, prefix="", is_last=True):
        task_name = node.get('taskName', 'unknown')
        is_operator = node.get('isOperator', False)
        node_id = node.get('nodeID', node.get('id', '?'))

        # Format the node display
        connector = "└── " if is_last else "├── "

        # Check if this is a known strategy
        strategy_annotation = ""
        task_base = task_name.split('(')[0] if '(' in task_name else task_name
        if task_base in known_strategies:
            strategy_annotation = f"  <- Strategy: {task_base}"

        # Display
        if is_operator:
            print(f"{prefix}{connector}[OP] {task_name}")
        else:
            print(f"{prefix}{connector}{task_name}{strategy_annotation}")

        # Get children
        children = children_map.get(node_id, [])
        child_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(children):
            print_tree(child, child_prefix, i == len(children) - 1)

    # Print from roots
    print()
    for i, root in enumerate(roots):
        print_tree(root, "", i == len(roots) - 1)

    # Summary: what strategies were used
    print("\n" + "-" * 50)
    strategies_used = set()
    for node in tree_nodes:
        task_name = node.get('taskName', '')
        task_base = task_name.split('(')[0] if '(' in task_name else task_name
        if task_base in known_strategies:
            strategies_used.add(task_base)

    if strategies_used:
        print("\nStrategies Used:")
        for s in sorted(strategies_used):
            print(f"  - {s}")

    return 0


def cmd_test_all(args) -> int:
    """Run tests for all components."""
    layer_filter = args.layer

    components = list_all_components(COMPONENTS_ROOT)

    if not components:
        print("No components found")
        return 0

    # Filter by layer if specified
    if layer_filter:
        # Map layer argument to directory name
        layer_map = {
            "primitives": "primitives",
            "primitive": "primitives",
            "strategies": "strategies",
            "strategy": "strategies",
            "goals": "goals",
            "goal": "goals",
            "levels": "levels",
            "level": "levels"
        }
        target_dir = layer_map.get(layer_filter.lower())
        if target_dir:
            components = [c for c in components if c['path'].startswith(target_dir)]

    print(f"Running tests for {len(components)} components...")
    print("=" * 60)

    results = []
    for comp in components:
        comp_path = comp['path']
        print(f"\n{comp_path}:", end=" ")

        try:
            full_path = resolve_component_path(comp_path, COMPONENTS_ROOT)
            test_path = os.path.join(full_path, "test.py")

            if os.path.exists(test_path):
                passed = run_tests(test_path, verbose=False)
                status = "PASS" if passed else "FAIL"
                results.append((comp_path, passed))
                print(status)
            else:
                print("SKIP (no test.py)")
                results.append((comp_path, None))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((comp_path, False))

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)

    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        print("\nFailed components:")
        for path, result in results:
            if result is False:
                print(f"  - {path}")

    return 0 if failed == 0 else 1


def cmd_verify(args) -> int:
    """Verify a level: check all dependencies are certified and tests pass."""
    level_path = args.level

    # Find level directory
    if os.path.isabs(level_path):
        full_path = level_path
    else:
        full_path = os.path.join(PROJECT_ROOT, "levels", level_path)

    if not os.path.isdir(full_path):
        print(f"Error: Level not found at {full_path}")
        return 1

    manifest_path = os.path.join(full_path, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Error: No manifest.json in level directory")
        return 1

    with open(manifest_path, 'r') as f:
        level_manifest = json.load(f)

    level_name = level_manifest.get('name', level_path)
    print(f"Verifying level: {level_name}")
    print("=" * 60)

    all_passed = True

    # Step 1: Check all dependencies are certified
    print("\n[1/3] Checking dependency certifications...")
    dependencies = level_manifest.get("dependencies", [])

    for dep in dependencies:
        try:
            dep_path = resolve_component_path(dep, COMPONENTS_ROOT)
            dep_manifest = get_component_manifest(dep_path)

            if dep_manifest.certified:
                print(f"  {dep}: CERTIFIED")
            else:
                print(f"  {dep}: NOT CERTIFIED")
                all_passed = False
        except FileNotFoundError:
            print(f"  {dep}: NOT FOUND")
            all_passed = False

    # Step 2: Run level tests
    print("\n[2/3] Running level tests...")
    test_path = os.path.join(full_path, "test.py")

    if os.path.exists(test_path):
        test_passed = run_tests(test_path, verbose=args.verbose)
        print(f"  Tests: {'PASS' if test_passed else 'FAIL'}")
        if not test_passed:
            all_passed = False
    else:
        print("  Tests: SKIP (no test.py)")

    # Step 3: Verify plan can be found
    print("\n[3/3] Verifying plan generation...")

    # Import and run a quick plan check
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "Python"))
    from indhtnpy import HtnPlanner

    planner = HtnPlanner(False)
    loaded_deps = set()

    def load_dep(dep_name: str):
        if dep_name in loaded_deps:
            return
        loaded_deps.add(dep_name)
        try:
            dep_path = resolve_component_path(dep_name, COMPONENTS_ROOT)
            dep_manifest = get_component_manifest(dep_path)
            for sub_dep in dep_manifest.dependencies:
                load_dep(sub_dep)
            src_path = os.path.join(dep_path, "src.htn")
            if os.path.exists(src_path):
                with open(src_path, 'r', encoding='utf-8') as f:
                    planner.HtnCompileCustomVariables(f.read())
        except:
            pass

    for dep in dependencies:
        load_dep(dep)

    level_htn = os.path.join(full_path, "level.htn")
    if os.path.exists(level_htn):
        with open(level_htn, 'r', encoding='utf-8') as f:
            planner.HtnCompileCustomVariables(f.read())

    # Find goal and try to plan
    import re
    with open(level_htn, 'r', encoding='utf-8') as f:
        level_content = f.read()
    goal_match = re.search(r'goals\(([^)]+)\)', level_content)

    if goal_match:
        goal = goal_match.group(1).strip() + "."
        error, result = planner.FindAllPlansCustomVariables(goal)
        solutions = json.loads(result) if result else []

        if solutions and not (isinstance(solutions[0], dict) and "false" in solutions[0]):
            num_ops = len(solutions[0]) if isinstance(solutions[0], list) else 0
            print(f"  Plan found: {num_ops} operators")
        else:
            print("  Plan: FAILED - no solution")
            all_passed = False
    else:
        print("  Plan: SKIP - no goals() found")

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print(f"VERIFIED: {level_name} is ready")
    else:
        print(f"NOT VERIFIED: {level_name} has issues")

    return 0 if all_passed else 1


def cmd_coverage(args) -> int:
    """Check design-to-test coverage for a component."""
    try:
        component_path = resolve_component_path(args.component, COMPONENTS_ROOT)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    design_path = os.path.join(component_path, "design.md")
    test_path = os.path.join(component_path, "test.py")

    if not os.path.exists(design_path):
        print(f"Error: No design.md found")
        return 1

    if not os.path.exists(test_path):
        print(f"Error: No test.py found")
        return 1

    print(f"Design Coverage Report: {args.component}")
    print("=" * 70)

    # Use enhanced semantic coverage check
    passed, report = verify_design_coverage(design_path, test_path, verbose=True)
    print(report)

    print("")
    if passed:
        print("RESULT: All design items have corresponding tests")
    else:
        print("RESULT: Some design items are missing tests")
        print("\nNaming convention required:")
        print("  - Example N → test_example_N_* (e.g., test_example_1_simple_case)")
        print("  - Property PN → test_property_pN_* (e.g., test_property_p1_invariant)")

    return 0 if passed else 1


# =============================================================================
# Helper Functions
# =============================================================================

def run_linter(htn_path: str, component_path: str = None) -> bool:
    """Run the HTN linter on a file.

    Args:
        htn_path: Path to the HTN file to lint
        component_path: Path to component directory (to resolve dependencies)
    """
    try:
        # Import linter from gui backend
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "gui", "backend"))
        from htn_linter import HtnLinter

        with open(htn_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if component has dependencies
        has_deps = False
        if component_path:
            manifest_path = os.path.join(component_path, "manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                has_deps = len(manifest.get("dependencies", [])) > 0

        linter = HtnLinter(content)
        diagnostics = linter.lint()

        # Filter diagnostics
        errors = []
        for d in diagnostics:
            severity = getattr(d, 'severity', '')
            msg = getattr(d, 'message', '')

            # Skip "undefined" errors for components with dependencies
            # (the dependency provides the definition)
            if has_deps and 'Undefined' in msg:
                continue

            if severity == "error":
                errors.append(d)

        if errors:
            for error in errors:
                line = getattr(error, 'line', '?')
                msg = getattr(error, 'message', 'Unknown error')
                print(f"    Line {line}: {msg}")
            return False

        return True
    except ImportError:
        print("    Warning: Linter not available (gui/backend/htn_linter.py not found)")
        return True  # Pass if linter not available
    except Exception as e:
        print(f"    Linter error: {e}")
        return False


def run_tests(test_path: str, verbose: bool = False) -> bool:
    """Run tests in a test.py file."""
    try:
        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=not verbose,
            text=True,
            cwd=os.path.dirname(test_path)
        )

        if verbose or result.returncode != 0:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"    Test error: {e}")
        return False


def check_design_coverage(design_path: str, test_path: str) -> bool:
    """Check that design examples have corresponding tests."""
    examples = parse_design_examples(design_path)
    properties = parse_design_properties(design_path)
    tests = parse_test_methods(test_path)

    total_needed = len(examples) + len(properties)
    if total_needed == 0:
        return True

    return len(tests) >= total_needed


def parse_design_examples(design_path: str) -> List[str]:
    """Parse example names from design.md."""
    examples = []
    with open(design_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for "### Example N:" patterns
    import re
    for match in re.finditer(r'###\s+Example\s+\d+:\s*(.+)', content):
        examples.append(match.group(1).strip())

    return examples


def parse_design_properties(design_path: str) -> List[str]:
    """Parse property IDs from design.md."""
    properties = []
    with open(design_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for "| P1 |" patterns in property table
    import re
    for match in re.finditer(r'\|\s*(P\d+)\s*\|', content):
        properties.append(match.group(1))

    return properties


def parse_test_methods(test_path: str) -> List[str]:
    """Parse test method names from test.py."""
    tests = []
    with open(test_path, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    for match in re.finditer(r'def\s+(test_\w+)', content):
        tests.append(match.group(1))

    return tests


# =============================================================================
# Enhanced Design Coverage (Semantic Matching)
# =============================================================================

def parse_design_items(design_path: str) -> Tuple[List[Tuple[int, str]], List[Tuple[str, str]]]:
    """Parse design.md for numbered examples and properties.

    Returns:
        Tuple of (examples, properties) where:
        - examples: List of (number, title) tuples
        - properties: List of (id, description) tuples
    """
    import re

    with open(design_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse examples: ### Example N: Title
    examples = []
    for match in re.finditer(r'###\s+Example\s+(\d+):\s*(.+)', content):
        num = int(match.group(1))
        title = match.group(2).strip()
        examples.append((num, title))

    # Parse properties from table: | PN | Name | Description |
    properties = []
    # Match rows like: | P1 | No double tags | An entity cannot have... |
    for match in re.finditer(r'\|\s*(P\d+)\s*\|\s*([^|]+)\s*\|', content):
        prop_id = match.group(1)
        prop_name = match.group(2).strip()
        properties.append((prop_id, prop_name))

    return examples, properties


def parse_test_coverage(test_path: str) -> Tuple[List[Tuple[int, str]], List[Tuple[str, str]]]:
    """Parse test.py for example and property test methods.

    Returns:
        Tuple of (example_tests, property_tests) where:
        - example_tests: List of (number, method_name) tuples
        - property_tests: List of (property_id, method_name) tuples
    """
    import re

    with open(test_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse example tests: def test_example_N_*
    example_tests = []
    for match in re.finditer(r'def\s+(test_example_(\d+)\w*)', content):
        method_name = match.group(1)
        num = int(match.group(2))
        example_tests.append((num, method_name))

    # Parse property tests: def test_property_pN_* (case insensitive for pN)
    property_tests = []
    for match in re.finditer(r'def\s+(test_property_(p\d+)\w*)', content, re.IGNORECASE):
        method_name = match.group(1)
        prop_id = match.group(2).upper()  # Normalize to P1, P2, etc.
        property_tests.append((prop_id, method_name))

    return example_tests, property_tests


def verify_design_coverage(design_path: str, test_path: str, verbose: bool = False) -> Tuple[bool, str]:
    """Verify that design examples and properties have corresponding tests.

    Uses naming convention:
    - test_example_N_* for Example N
    - test_property_pN_* for Property PN

    Args:
        design_path: Path to design.md
        test_path: Path to test.py
        verbose: If True, return detailed report

    Returns:
        Tuple of (passed, report_string)
    """
    examples, properties = parse_design_items(design_path)
    example_tests, property_tests = parse_test_coverage(test_path)

    # Build lookup maps
    example_test_map = {num: name for num, name in example_tests}
    property_test_map = {pid: name for pid, name in property_tests}

    # Check coverage
    example_results = []
    for num, title in examples:
        if num in example_test_map:
            example_results.append((num, title, example_test_map[num], True))
        else:
            example_results.append((num, title, None, False))

    property_results = []
    for prop_id, prop_name in properties:
        if prop_id in property_test_map:
            property_results.append((prop_id, prop_name, property_test_map[prop_id], True))
        else:
            property_results.append((prop_id, prop_name, None, False))

    # Calculate coverage
    total_items = len(examples) + len(properties)
    covered_items = sum(1 for _, _, _, ok in example_results if ok) + \
                   sum(1 for _, _, _, ok in property_results if ok)

    passed = covered_items == total_items

    # Build report
    lines = []
    if verbose:
        lines.append("Examples:")
        for num, title, test_name, ok in example_results:
            status = "OK" if ok else "MISSING"
            test_display = test_name if test_name else f"test_example_{num}_*"
            # Truncate title for alignment
            title_short = title[:30] + "..." if len(title) > 30 else title
            lines.append(f"  [{num}] {title_short:<34} {test_display:<40} {status}")

        lines.append("")
        lines.append("Properties:")
        for prop_id, prop_name, test_name, ok in property_results:
            status = "OK" if ok else "MISSING"
            test_display = test_name if test_name else f"test_property_{prop_id.lower()}_*"
            name_short = prop_name[:30] + "..." if len(prop_name) > 30 else prop_name
            lines.append(f"  [{prop_id}] {name_short:<34} {test_display:<40} {status}")

        lines.append("")

    coverage_pct = (covered_items / total_items * 100) if total_items > 0 else 100
    lines.append(f"Coverage: {covered_items}/{total_items} ({coverage_pct:.0f}%)")

    return passed, "\n".join(lines)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="HTN Component Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  new       Create a new component from template
  test      Run tests for a component
  certify   Certify a component (all checks must pass)
  status    List all components with certification status
  assemble  Assemble a level into a single HTN file
  coverage  Check design-to-test coverage

Examples:
  python -m htn_components new primitives/tags
  python -m htn_components test primitives/tags
  python -m htn_components certify primitives/tags
  python -m htn_components status
  python -m htn_components assemble puzzle1 --output level1.htn
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # new command
    new_parser = subparsers.add_parser("new", help="Create new component")
    new_parser.add_argument("component", help="Component path (e.g., primitives/tags)")
    new_parser.set_defaults(func=cmd_new)

    # test command
    test_parser = subparsers.add_parser("test", help="Test a component")
    test_parser.add_argument("component", help="Component path or name")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    test_parser.set_defaults(func=cmd_test)

    # certify command
    certify_parser = subparsers.add_parser("certify", help="Certify a component")
    certify_parser.add_argument("component", help="Component path or name")
    certify_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    certify_parser.add_argument("--dry-run", action="store_true", help="Show results without updating manifest")
    certify_parser.set_defaults(func=cmd_certify)

    # status command
    status_parser = subparsers.add_parser("status", help="List component status")
    status_parser.set_defaults(func=cmd_status)

    # assemble command
    assemble_parser = subparsers.add_parser("assemble", help="Assemble level")
    assemble_parser.add_argument("level", help="Level path")
    assemble_parser.add_argument("-o", "--output", help="Output file path")
    assemble_parser.set_defaults(func=cmd_assemble)

    # coverage command
    coverage_parser = subparsers.add_parser("coverage", help="Check design coverage")
    coverage_parser.add_argument("component", help="Component path or name")
    coverage_parser.set_defaults(func=cmd_coverage)

    # play command
    play_parser = subparsers.add_parser("play", help="Play level with narrative output")
    play_parser.add_argument("level", help="Level path (e.g., puzzle1)")
    play_parser.set_defaults(func=cmd_play)

    # trace command
    trace_parser = subparsers.add_parser("trace", help="Show decomposition tree")
    trace_parser.add_argument("level", help="Level path (e.g., puzzle1)")
    trace_parser.add_argument("--goal", "-g", help="Custom goal (default: level's goals())")
    trace_parser.set_defaults(func=cmd_trace)

    # test-all command
    test_all_parser = subparsers.add_parser("test-all", help="Run tests for all components")
    test_all_parser.add_argument("--layer", "-l", help="Filter by layer (primitives, strategies, goals, levels)")
    test_all_parser.set_defaults(func=cmd_test_all)

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a level (dependencies + tests + plan)")
    verify_parser.add_argument("level", help="Level path (e.g., puzzle1)")
    verify_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    verify_parser.set_defaults(func=cmd_verify)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
