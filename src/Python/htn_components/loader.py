"""
Central component loader for HTN component assembly.

Replaces the ad-hoc dep-walk-and-concat logic duplicated across
`htn_test_framework.load_component` and multiple sites in
`htn_components.cli`. Adds load-time correctness checks:

  - **Duplicate operator detection.** Two different components defining
    the same `opName/arity` is an error (last-wins silently today).
  - **`provides` / `requires` contract.** After loading the closure,
    every `requires` signature must be satisfied by some component's
    `provides`.

The loader uses `gui/backend/htn_parser.py` — the real HTN AST parser —
to extract operator signatures rather than regex. Method duplicates are
surfaced as warnings because HTN legitimately allows multiple methods
with the same name/arity across alternatives.
"""

import os
import sys
from typing import Callable, Dict, List, Optional, Set, Tuple

from .manifest import (
    Manifest,
    get_component_manifest,
    resolve_component_path,
)


class LoadError(Exception):
    """Raised when a component cannot be loaded cleanly."""


def _import_htn_parser():
    """Lazy-import the AST parser from gui/backend (not on default path)."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    backend_dir = os.path.join(project_root, "gui", "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from htn_parser import parse_htn  # type: ignore
    return parse_htn


def _import_builtins():
    """Lazy-import the authoritative built-in predicate set from the linter."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    backend_dir = os.path.join(project_root, "gui", "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from htn_linter import BUILTIN_PREDICATES  # type: ignore
    return BUILTIN_PREDICATES


_META_WRAPPERS = {
    # These wrap other tasks/goals; their own name is not a contract call.
    "try", "first", "and", "not", "\\+", "call",
    "findall", "bagof", "setof", "forall", "count",
    "distinct", "sortBy", "parallel",
}


def _collect_called_sigs(term, out: Set[str]) -> None:
    """Collect name/arity signatures of tasks dispatched from a do()-clause arg.

    Task arguments (atoms, variables, compound data) are NOT calls — they're
    the operands of the task — so we do not recurse into them. Meta-wrappers
    (try/first/and/not/parallel/...) are transparent: we recurse through
    them to the real task underneath.
    """
    if term is None or getattr(term, "is_variable", False):
        return
    name = term.name
    if name in _META_WRAPPERS:
        for arg in term.args:
            _collect_called_sigs(arg, out)
        return
    # Real task call. Record and stop — its arguments are data.
    out.add(f"{name}/{len(term.args)}")


def infer_contracts(source: str) -> Tuple[List[str], List[str]]:
    """Parse an HTN source and return (provides, requires).

    - **provides**: method + operator + fact signatures (`name/arity`)
      defined in the source.
    - **requires**: signatures called from do()/if() clauses but neither
      defined locally nor a known built-in. These are what the component
      expects some dependency to supply.

    Both lists are sorted for deterministic manifest output.
    """
    parse_htn = _import_htn_parser()
    builtins = _import_builtins()
    rules, _ = parse_htn(source)

    provides: Set[str] = set()
    atoms_as_facts: Set[str] = set()

    # First pass: collect all definitions.
    for rule in rules:
        if rule.head is None:
            continue
        sig = f"{rule.head.name}/{len(rule.head.args)}"
        # goals() directives are not predicates the component "provides"
        if rule.head.name == "goals":
            continue
        if rule.is_method or rule.is_operator or rule.is_fact:
            provides.add(sig)
        else:
            # pure Prolog rule — also a provided predicate
            provides.add(sig)
        # Facts' atomic arguments are implicitly recognizable (e.g. "player"
        # in `at(player, home).` so downstream rules can match them).
        if rule.is_fact:
            for arg in rule.head.args:
                if not arg.is_variable and len(arg.args) == 0:
                    atoms_as_facts.add(f"{arg.name}/0")

    # Second pass: collect calls from do() clauses only. These are direct
    # dispatches to other methods/operators and form real load-time contracts.
    # if()-clause predicates query state (facts, op-produced) and are too
    # fuzzy to flag as contracts; add()/del() shape the state, not calls.
    called: Set[str] = set()
    for rule in rules:
        if rule.do_clause is None:
            continue
        for arg in rule.do_clause.args:
            _collect_called_sigs(arg, called)

    known = provides | atoms_as_facts | set(builtins)
    requires = {sig for sig in called if sig not in known}

    return sorted(provides), sorted(requires)


class ComponentLoader:
    """Walks a component's dep graph, compiles sources into a planner,
    and enforces load-time contracts.

    Usage:
        loader = ComponentLoader(planner, project_root)
        loader.load("gamehack/goals/plan_to_damage")
        loader.load_level_htn("levels/gamehack_mvp")  # optional
        loader.verify_contracts()
    """

    def __init__(
        self,
        planner,
        project_root: str,
        warn: Optional[Callable[[str], None]] = None,
    ):
        self._planner = planner
        self._project_root = project_root
        self._components_root = os.path.join(project_root, "components")
        self._warn = warn or (lambda msg: print(f"[warn] {msg}", file=sys.stderr))

        self._loaded: Set[str] = set()                # component path strings
        self._operator_owner: Dict[str, str] = {}      # "name/arity" -> component
        self._method_owners: Dict[str, List[str]] = {}  # "name/arity" -> [components]
        self._provides: Dict[str, Set[str]] = {}        # component -> sigs
        self._requires: Dict[str, Set[str]] = {}        # component -> sigs

    # --------------------------------------------------------------- loading

    def load(self, component_path: str) -> None:
        """Load a component and its transitive dependencies.

        Two-phase: (1) walk manifests building a dep graph with DFS-based
        cycle detection, (2) compile in topological order. Raises LoadError
        on dependency cycles, duplicate operators, missing files, or
        compile errors.
        """
        if component_path in self._loaded:
            return
        order = self._plan_load_order([component_path])
        self._compile_in_order(order)

    def load_level_htn(self, level_dir: str) -> None:
        """Compile a level's `level.htn` (facts + goals) into the planner.

        `level_dir` is either a component-path form ("levels/puzzle1",
        "puzzle1") or an absolute directory path. Dependencies from the
        level's manifest are walked first, in topological order.
        """
        if os.path.isabs(level_dir) and os.path.isdir(level_dir):
            full_path = level_dir
        else:
            try:
                full_path = resolve_component_path(level_dir, self._components_root)
            except FileNotFoundError as exc:
                raise LoadError(str(exc)) from exc

        manifest_path = os.path.join(full_path, "manifest.json")
        if os.path.exists(manifest_path):
            manifest = Manifest.load(manifest_path)
            # Resolve deps through the same two-phase loader.
            deps = [d for d in manifest.dependencies if d not in self._loaded]
            if deps:
                order = self._plan_load_order(deps)
                self._compile_in_order(order)

        level_htn = os.path.join(full_path, "level.htn")
        if not os.path.exists(level_htn):
            raise LoadError(f"No level.htn in {full_path}")

        with open(level_htn, "r", encoding="utf-8") as f:
            content = f.read()

        error = self._planner.HtnCompileCustomVariables(content)
        if error:
            raise LoadError(f"Compile error in {level_htn}: {error}")

    # ------------------------------------------------- topological planning

    def _plan_load_order(self, roots: List[str]) -> List[str]:
        """Walk manifests from the given roots and return a topological
        load order (dependencies before dependents).

        Uses iterative DFS with explicit 'visiting' / 'visited' sets so we
        can report the full cycle path on a back-edge.
        """
        order: List[str] = []
        visited: Set[str] = set(self._loaded)  # treat already-loaded as sinks
        visiting: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                # Back-edge → cycle. Slice the path from the first occurrence.
                start = path.index(node)
                cycle = " → ".join(path[start:] + [node])
                raise LoadError(f"Dependency cycle: {cycle}")
            visiting.add(node)
            path.append(node)

            deps = self._manifest_deps(node)
            for dep in deps:
                dfs(dep)

            path.pop()
            visiting.remove(node)
            visited.add(node)
            order.append(node)

        for root in roots:
            dfs(root)

        return order

    def _manifest_deps(self, component_path: str) -> List[str]:
        """Read manifest.json for the component and return its dependency
        list. Returns [] if the manifest is missing.
        """
        try:
            full_path = resolve_component_path(component_path, self._components_root)
        except FileNotFoundError as exc:
            raise LoadError(str(exc)) from exc

        manifest_path = os.path.join(full_path, "manifest.json")
        if not os.path.exists(manifest_path):
            return []
        return Manifest.load(manifest_path).dependencies

    def _compile_in_order(self, order: List[str]) -> None:
        """Read src.htn for each component in order, run signature checks,
        compile into the shared planner, and record contract metadata.
        """
        for component_path in order:
            if component_path in self._loaded:
                continue
            try:
                full_path = resolve_component_path(component_path, self._components_root)
            except FileNotFoundError as exc:
                raise LoadError(str(exc)) from exc

            manifest_path = os.path.join(full_path, "manifest.json")
            manifest: Optional[Manifest] = None
            if os.path.exists(manifest_path):
                manifest = Manifest.load(manifest_path)

            src_path = os.path.join(full_path, "src.htn")
            if os.path.exists(src_path):
                with open(src_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._check_signatures(component_path, content)
                error = self._planner.HtnCompileCustomVariables(content)
                if error:
                    raise LoadError(f"Compile error in {component_path}: {error}")

            self._loaded.add(component_path)
            self._record_contract(component_path, manifest)

    # ----------------------------------------------------- contract checking

    def verify_contracts(self) -> None:
        """Ensure every `requires` signature is covered by some `provides`.

        Raises LoadError listing the requesting component(s) and the
        unsatisfied signatures, with a hint about which component typically
        provides them.
        """
        all_provided: Set[str] = set()
        for sigs in self._provides.values():
            all_provided |= sigs

        violations: List[str] = []
        for component, required in self._requires.items():
            missing = required - all_provided
            if missing:
                # Try to locate which component in the wider system provides
                # each missing sig, to give the user a useful suggestion.
                hints = self._find_providers_on_disk(missing)
                pretty = ", ".join(sorted(missing))
                hint_txt = ""
                if hints:
                    hint_lines = "\n    Suggestion:"
                    for sig, providers in hints.items():
                        hint_lines += f"\n      - {sig} is provided by {providers}"
                    hint_txt = hint_lines
                violations.append(
                    f"{component} requires [{pretty}] — not provided by any loaded component.{hint_txt}"
                )

        if violations:
            raise LoadError("Contract violations:\n  " + "\n  ".join(violations))

    # ---------------------------------------------------------------- helpers

    def _check_signatures(self, component: str, source: str) -> None:
        """Parse the component's source and update operator/method registries.

        - Two components declaring the same operator signature → LoadError.
        - Two components declaring the same method signature → warning (HTN
          allows cross-file method alternatives; this is informational).
        """
        parse_htn = _import_htn_parser()
        rules, _diagnostics = parse_htn(source)

        local_ops: Set[str] = set()
        local_methods: Set[str] = set()

        for rule in rules:
            if rule.head is None:
                continue
            sig = f"{rule.head.name}/{len(rule.head.args)}"
            if rule.is_operator:
                local_ops.add(sig)
            elif rule.is_method:
                local_methods.add(sig)

        # Operator conflict → hard error.
        for sig in local_ops:
            prior = self._operator_owner.get(sig)
            if prior is not None and prior != component:
                raise LoadError(
                    f"Duplicate operator {sig}: defined in both "
                    f"'{prior}' and '{component}'. Operators must be unique."
                )
            self._operator_owner[sig] = component

        # Method sharing across components → warn.
        for sig in local_methods:
            owners = self._method_owners.setdefault(sig, [])
            if owners and component not in owners:
                self._warn(
                    f"Method {sig} defined in multiple components: "
                    f"{owners + [component]}. Last-compiled definition applies."
                )
            if component not in owners:
                owners.append(component)

    def _record_contract(self, component: str, manifest: Optional[Manifest]) -> None:
        if manifest is None:
            return
        if manifest.provides:
            self._provides[component] = set(manifest.provides)
        if manifest.requires:
            self._requires[component] = set(manifest.requires)

    def _find_providers_on_disk(self, missing_sigs: Set[str]) -> Dict[str, str]:
        """For each missing signature, scan the components tree for any
        component whose manifest declares it in `provides`. Used purely
        for human-friendly error messages."""
        hints: Dict[str, List[str]] = {sig: [] for sig in missing_sigs}
        try:
            for root, _dirs, files in os.walk(self._components_root):
                if "manifest.json" in files:
                    try:
                        m = Manifest.load(os.path.join(root, "manifest.json"))
                    except Exception:
                        continue
                    rel = os.path.relpath(root, self._components_root)
                    for sig in missing_sigs:
                        if sig in m.provides:
                            hints[sig].append(rel)
        except OSError:
            pass
        return {sig: ", ".join(p) for sig, p in hints.items() if p}

    # -------------------------------------------------------- introspection

    @property
    def loaded(self) -> Set[str]:
        return set(self._loaded)

    @property
    def operator_owner(self) -> Dict[str, str]:
        return dict(self._operator_owner)
