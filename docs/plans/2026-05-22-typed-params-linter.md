# Typed Parameters Linter (T0.2) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a linter rule (code `TYP001`) that catches type mismatches at call sites when a ruleset declares predicate signatures and instance types as facts. No engine changes — purely a `gui/backend/htn_linter.py` extension.

**Architecture:** The ruleset declares two new conventional fact predicates: `signature(predName, [type1, type2, ...]).` and `type(typeName, instance).`. The linter (pre-pass) collects these into a registry, then walks every call site in the assembled source. For each call to a predicate with a declared signature, it checks each *constant* argument against the expected type. Variables and compound terms are skipped in the MVP (deferred to TYP002+). The rule is fully backward-compatible: rulesets without `signature/2` declarations get zero new diagnostics. The runtime engine sees `signature/2` and `type/2` as ordinary facts and never queries them, so they're inert at planning time.

**Tech Stack:** Python 3, existing `htn_linter.py` + `htn_parser.py` AST infrastructure, custom `LinterTestSuite` in `src/Python/tests/test_linter.py`, error fixtures in `Examples/ErrorTests/`.

---

## Design Reference

### Declaration convention

```prolog
% Type declarations (component or level facts)
type(agent, player).
type(agent, gob1).
type(cell, c5).
type(cell, c6).
type(tag, fire).

% Signature declarations (component facts)
signature(moveTo, [agent, cell]).
signature(applyTag, [agent, tag]).
```

### What TYP001 catches

```prolog
% OK — types match
goal :- if(), do(moveTo(player, c5)).

% TYP001 — args swapped: c5 (cell) where agent expected, player (agent) where cell expected
goal :- if(), do(moveTo(c5, player)).

% TYP001 — gob1 declared as agent but used where cell expected
goal :- if(), do(moveTo(player, gob1)).

% TYP001 — wat is an undeclared constant (no type/2 fact for it) but moveTo expects an agent
goal :- if(), do(moveTo(wat, c5)).
```

### What TYP001 explicitly does NOT catch (MVP scope cuts)

- Variables: `moveTo(?a, ?c)` is never flagged, even if `?a` is later bound to a cell. (Future TYP002.)
- Compound terms: `moveTo(pair(a, b), c5)` is skipped.
- Arity mismatch with signature: defer to a future TYP003 (existing SEM003 catches some cases).
- Calls where no `signature/N` is declared for the predicate: not flagged.

### Diagnostic format

Reuse the existing `Diagnostic` dataclass from `htn_parser.py`:

```python
Diagnostic(
    line=<call site line>,
    col=<call site col>,
    length=len(arg_token),
    severity='error',
    code='TYP001',
    message=f"Argument {i+1} of '{pred_name}/{arity}' expects type '{expected_type}', got constant '{arg_name}' (declared as type '{actual_type}')" 
    # or "...got constant '{arg_name}' (no type/2 declaration found)" if untyped
)
```

---

### Task 1: TypeRegistry data structure

**Files:**
- Modify: `gui/backend/htn_linter.py` (add new class near the top, ~line 80)
- Create: `src/Python/tests/test_typed_params_linter.py`

**Step 1: Write the failing test**

Create `src/Python/tests/test_typed_params_linter.py`:

```python
"""Tests for TYP001 typed-parameters linter rule."""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.dirname(script_dir)
backend_dir = os.path.abspath(os.path.join(python_dir, '../../gui/backend'))
sys.path.insert(0, backend_dir)
sys.path.insert(0, python_dir)

from htn_linter import HtnLinter, TypeRegistry


def test_empty_source_yields_empty_registry():
    reg = TypeRegistry.from_source("")
    assert reg.signatures == {}
    assert reg.types == {}


def test_extracts_type_facts():
    src = """
    type(agent, player).
    type(agent, gob1).
    type(cell, c5).
    """
    reg = TypeRegistry.from_source(src)
    assert reg.types == {
        'agent': {'player', 'gob1'},
        'cell': {'c5'},
    }


def test_extracts_signature_facts():
    src = """
    signature(moveTo, [agent, cell]).
    signature(applyTag, [agent, tag]).
    """
    reg = TypeRegistry.from_source(src)
    assert reg.signatures == {
        'moveTo/2': ['agent', 'cell'],
        'applyTag/2': ['agent', 'tag'],
    }


def test_type_lookup():
    src = "type(agent, player). type(cell, c5)."
    reg = TypeRegistry.from_source(src)
    assert reg.type_of('player') == {'agent'}
    assert reg.type_of('c5') == {'cell'}
    assert reg.type_of('unknown') == set()


if __name__ == '__main__':
    test_empty_source_yields_empty_registry()
    test_extracts_type_facts()
    test_extracts_signature_facts()
    test_type_lookup()
    print("All TypeRegistry tests passed.")
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/polycea/Projects/InductorHtn/src/Python/tests
source /Users/polycea/Projects/InductorHtn/.venv/bin/activate
python test_typed_params_linter.py
```

Expected: `ImportError: cannot import name 'TypeRegistry' from 'htn_linter'`

**Step 3: Implement TypeRegistry**

In `gui/backend/htn_linter.py`, add immediately after the `SymbolInfo` dataclass (around line 80):

```python
from collections import defaultdict


@dataclass
class TypeRegistry:
    """Collects type/2 and signature/2 declarations from a parsed ruleset.

    Conventions (recognized only by the linter; engine treats as ordinary facts):
      - type(typeName, instance).
      - signature(predName, [argType1, argType2, ...]).
    """
    types: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    signatures: Dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def from_source(cls, source: str) -> 'TypeRegistry':
        from htn_parser import parse_htn
        rules, _ = parse_htn(source)
        return cls.from_rules(rules)

    @classmethod
    def from_rules(cls, rules) -> 'TypeRegistry':
        reg = cls()
        for rule in rules:
            head = rule.head
            # Only facts (no body)
            if rule.body:
                continue
            if head.name == 'type' and len(head.args) == 2:
                type_name = head.args[0].name
                instance = head.args[1].name
                if not head.args[0].is_variable and not head.args[1].is_variable:
                    reg.types[type_name].add(instance)
            elif head.name == 'signature' and len(head.args) == 2:
                pred_name = head.args[0].name
                arg_list = head.args[1]
                if arg_list.is_list:
                    types = [t.name for t in arg_list.args if not t.is_variable]
                    if len(types) == len(arg_list.args):  # all concrete
                        reg.signatures[f"{pred_name}/{len(types)}"] = types
        return reg

    def type_of(self, instance: str) -> Set[str]:
        return {t for t, members in self.types.items() if instance in members}
```

Make sure `Dict, Set, List` are already imported from `typing` at top of file (they are, per `from typing import List, Dict, Set, Optional, Tuple` on line 6).

**Step 4: Run test to verify it passes**

```bash
python test_typed_params_linter.py
```

Expected: `All TypeRegistry tests passed.`

**Step 5: Commit**

```bash
cd /Users/polycea/Projects/InductorHtn
git add gui/backend/htn_linter.py src/Python/tests/test_typed_params_linter.py
git commit -m "feat(linter): add TypeRegistry for type/2 and signature/2 facts"
```

---

### Task 2: TYP001 rule — constant arg violates expected type

**Files:**
- Modify: `gui/backend/htn_linter.py` (add `_check_typed_parameters` method, call from `lint()`)
- Modify: `src/Python/tests/test_typed_params_linter.py` (add rule tests)

**Step 1: Write the failing test**

Append to `src/Python/tests/test_typed_params_linter.py`:

```python
def _diag_codes(diags):
    return [d.get('code') if isinstance(d, dict) else d.code for d in diags]


def test_typ001_clean_call_no_diagnostic():
    src = """
    type(agent, player).
    type(cell, c5).
    signature(moveTo, [agent, cell]).
    goalA :- if(), do(moveTo(player, c5)).
    """
    diags = HtnLinter(src).lint()
    assert 'TYP001' not in _diag_codes(diags)


def test_typ001_swapped_args_flagged():
    src = """
    type(agent, player).
    type(cell, c5).
    signature(moveTo, [agent, cell]).
    goalA :- if(), do(moveTo(c5, player)).
    """
    diags = HtnLinter(src).lint()
    typ_diags = [d for d in diags if (d.get('code') if isinstance(d, dict) else d.code) == 'TYP001']
    assert len(typ_diags) == 2  # both args wrong


def test_typ001_untyped_constant_flagged():
    src = """
    type(agent, player).
    type(cell, c5).
    signature(moveTo, [agent, cell]).
    goalA :- if(), do(moveTo(wat, c5)).
    """
    diags = HtnLinter(src).lint()
    assert 'TYP001' in _diag_codes(diags)


def test_typ001_variable_arg_skipped():
    src = """
    type(agent, player).
    type(cell, c5).
    signature(moveTo, [agent, cell]).
    move(?x, ?y) :- if(), do(moveTo(?x, ?y)).
    """
    diags = HtnLinter(src).lint()
    typ_diags = [d for d in diags if (d.get('code') if isinstance(d, dict) else d.code) == 'TYP001']
    assert typ_diags == []


def test_typ001_no_signature_no_diagnostic():
    src = """
    type(agent, player).
    type(cell, c5).
    goalA :- if(), do(moveTo(c5, player)).
    """
    # No signature(moveTo, ...) declared → rule does not engage
    diags = HtnLinter(src).lint()
    assert 'TYP001' not in _diag_codes(diags)


if __name__ == '__main__':
    test_empty_source_yields_empty_registry()
    test_extracts_type_facts()
    test_extracts_signature_facts()
    test_type_lookup()
    test_typ001_clean_call_no_diagnostic()
    test_typ001_swapped_args_flagged()
    test_typ001_untyped_constant_flagged()
    test_typ001_variable_arg_skipped()
    test_typ001_no_signature_no_diagnostic()
    print("All TypeRegistry + TYP001 tests passed.")
```

**Step 2: Run to verify failure**

```bash
python test_typed_params_linter.py
```

Expected: `AssertionError` in `test_typ001_swapped_args_flagged` (rule not implemented yet).

**Step 3: Implement `_check_typed_parameters`**

In `gui/backend/htn_linter.py`, locate the `lint()` method (line 113). After parsing rules and building symbol tables, add a new check. First, add the helper method on `HtnLinter`:

```python
    def _check_typed_parameters(self) -> None:
        """TYP001: constant argument violates declared signature type.

        Activates only when signature/2 facts are declared. Variables and
        compound terms are skipped. Untyped constants (no type/2 fact) at
        a typed position are flagged.
        """
        registry = TypeRegistry.from_rules(self.rules)
        if not registry.signatures:
            return

        # Walk every call site in every rule's body clauses.
        for rule in self.rules:
            for clause_terms in self._all_call_clauses(rule):
                for call_term in clause_terms:
                    self._check_call_against_signature(call_term, registry)

    def _all_call_clauses(self, rule):
        """Yield iterables of call terms from a rule's if/do/del/add/body."""
        if rule.is_method:
            yield rule.if_clause or []
            yield rule.do_clause or []
        elif rule.is_operator:
            yield rule.del_clause or []
            yield rule.add_clause or []
        else:
            yield rule.body or []

    def _check_call_against_signature(self, call, registry: 'TypeRegistry'):
        if call.is_variable:
            return
        sig_key = f"{call.name}/{len(call.args)}"
        expected_types = registry.signatures.get(sig_key)
        if expected_types is None:
            return
        for i, (arg, expected) in enumerate(zip(call.args, expected_types)):
            if arg.is_variable:
                continue
            if arg.args:  # compound term, skip in MVP
                continue
            actual_types = registry.type_of(arg.name)
            if expected in actual_types:
                continue
            if not actual_types:
                msg = (f"Argument {i+1} of '{call.name}/{len(call.args)}' expects "
                       f"type '{expected}', got constant '{arg.name}' "
                       f"(no type/2 declaration found)")
            else:
                msg = (f"Argument {i+1} of '{call.name}/{len(call.args)}' expects "
                       f"type '{expected}', got constant '{arg.name}' "
                       f"(declared as type '{', '.join(sorted(actual_types))}')")
            self.diagnostics.append(Diagnostic(
                line=arg.line,
                col=arg.col,
                length=len(arg.name),
                severity='error',
                code='TYP001',
                message=msg,
            ))
```

Then wire it into `lint()`. Find the existing sequence of checks (after `_build_symbol_tables()`) and add:

```python
        self._check_typed_parameters()
```

at the end of the check sequence (after the last existing `self._check_*` call but before `return self.diagnostics`).

**Step 4: Run tests**

```bash
python test_typed_params_linter.py
```

Expected: `All TypeRegistry + TYP001 tests passed.`

**Step 5: Commit**

```bash
git add gui/backend/htn_linter.py src/Python/tests/test_typed_params_linter.py
git commit -m "feat(linter): add TYP001 rule for typed parameter mismatches"
```

---

### Task 3: Suppress SEM001/SEM002 noise from `type/2` and `signature/2` facts

**Files:**
- Modify: `gui/backend/htn_linter.py` (existing `BUILTIN_PREDICATES` or symbol-table init)

**Why:** `type/2` and `signature/2` are now conventional facts. Existing rules may flag them as unused, undefined, or as causing arity confusion. Run existing tests after Task 2 to find out.

**Step 1: Write the regression test**

Append to `test_typed_params_linter.py`:

```python
def test_no_false_positives_on_type_signature_facts():
    src = """
    type(agent, player).
    signature(moveTo, [agent, cell]).
    """
    diags = HtnLinter(src).lint()
    # No SEM001 (undefined call), SEM003 (arity), VAR003 (singleton) from these facts
    bad_codes = {'SEM001', 'SEM003', 'VAR003'}
    for d in diags:
        code = d.get('code') if isinstance(d, dict) else d.code
        assert code not in bad_codes, f"unexpected diagnostic: {d}"
```

**Step 2: Run to see what fires**

```bash
python test_typed_params_linter.py
```

If the test passes, skip to Step 5 (commit) — nothing to fix. If it fails, fix as below.

**Step 3: Suppress false positives**

If SEM001 (or another code) fires on `type/2`/`signature/2`, add them to a whitelist near `BUILTIN_PREDICATES` (line 17):

```python
LINTER_RECOGNIZED_FACTS = {'type/2', 'signature/2'}
```

Then, in whichever `_check_*` method emits the false positive, add `and sig not in LINTER_RECOGNIZED_FACTS` to the condition. (Locate by reading the failing test's diagnostic output.)

**Step 4: Re-run tests**

```bash
python test_typed_params_linter.py
python test_linter.py  # ensure existing linter tests still pass
```

Expected: All tests pass.

**Step 5: Commit**

```bash
git add gui/backend/htn_linter.py src/Python/tests/test_typed_params_linter.py
git commit -m "feat(linter): exempt type/2 and signature/2 from generic rules"
```

---

### Task 4: ErrorTests fixture + integration with `assert_detects_error`

**Files:**
- Create: `Examples/ErrorTests/typed_arg_swapped.htn`
- Create: `Examples/ErrorTests/typed_arg_untyped_constant.htn`
- Modify: `src/Python/tests/test_linter.py` (add new suite section)
- Modify: `Examples/ErrorTests/README.md` (document new TYP* category)

**Step 1: Write the failing test**

Append to `src/Python/tests/test_linter.py` inside `LinterTestSuite.run_all_tests()` (or wherever the test list lives — read the file to find the exact insertion point):

```python
def test_typed_parameters(self):
    """TYP001: typed parameter mismatches."""
    self.assert_detects_error(
        'typed_arg_swapped.htn',
        expected_code='TYP001',
        expected_severity='error',
        msg="Should detect swapped agent/cell args in moveTo call",
    )
    self.assert_detects_error(
        'typed_arg_untyped_constant.htn',
        expected_code='TYP001',
        msg="Should detect constant with no type/2 declaration in typed position",
    )
```

Add `self.test_typed_parameters()` to the appropriate suite-runner method.

**Step 2: Create the fixtures**

`Examples/ErrorTests/typed_arg_swapped.htn`:

```prolog
% TYP001 — moveTo(?agent, ?cell) called with args reversed
type(agent, player).
type(cell, c5).
signature(moveTo, [agent, cell]).

goalA :- if(), do(moveTo(c5, player)).
```

`Examples/ErrorTests/typed_arg_untyped_constant.htn`:

```prolog
% TYP001 — 'wat' has no type/2 declaration but moveTo expects an agent
type(agent, player).
type(cell, c5).
signature(moveTo, [agent, cell]).

goalA :- if(), do(moveTo(wat, c5)).
```

**Step 3: Run tests to verify they pass**

```bash
cd /Users/polycea/Projects/InductorHtn/src/Python/tests
python test_linter.py --verbose
```

Expected: New `PASS: detects error in typed_arg_swapped.htn` and `PASS: detects error in typed_arg_untyped_constant.htn` lines, and no regressions.

**Step 4: Update ErrorTests/README.md**

In `Examples/ErrorTests/README.md`, add a TYP* section in the existing taxonomy (read the file first to match its format). Suggested entry:

```markdown
## TYP — Type errors

| Code | Fixture | Description |
|------|---------|-------------|
| TYP001 | typed_arg_swapped.htn | Constant argument violates expected type at call site |
| TYP001 | typed_arg_untyped_constant.htn | Constant has no `type/2` declaration but appears in a typed position |
```

**Step 5: Commit**

```bash
git add Examples/ErrorTests/typed_arg_swapped.htn \
        Examples/ErrorTests/typed_arg_untyped_constant.htn \
        Examples/ErrorTests/README.md \
        src/Python/tests/test_linter.py
git commit -m "test(linter): add TYP001 fixtures and integration tests"
```

---

### Task 5: Assembler integration verification

**Files:**
- Modify: `src/Python/tests/test_cli_assemble.py` (add one test) — or create a dedicated test file if the layout fits better.

**Why:** TYP001 must surface through `htn_components assemble`'s verifier (layer 2 = `htn_linter`). Confirm end-to-end.

**Step 1: Write the failing test**

First read `src/Python/tests/test_cli_assemble.py` to understand how existing tests assemble + check verifier output. Then add:

```python
def test_typ001_surfaces_through_assembler(tmp_path):
    """A component declaring a bad call should cause `assemble --verify-only` to fail with TYP001."""
    # Build a minimal level + component with a TYP001 violation, write to tmp_path,
    # run `htn_components assemble <level> --verify-only --skip-compile-check`,
    # assert exit code 2 and 'TYP001' in stderr.
    # Use existing helper patterns from this file (read it to see).
    ...
```

(Plan note: implement using the same scaffolding the file already uses for other ASM/SEM/VAR layer-2 tests. Don't re-invent fixture mechanics — match what's there.)

**Step 2: Run to verify it fails**

```bash
cd /Users/polycea/Projects/InductorHtn/src/Python/tests
python -m pytest test_cli_assemble.py::test_typ001_surfaces_through_assembler -v
```

Expected: FAIL (the assembler should reject the violating fixture once linter integration is correct, but if the failure is "test setup wrong" rather than "TYP001 not detected," fix the test scaffolding).

**Step 3: Confirm integration**

If `verify_assembled()` already runs `HtnLinter(content).lint()` (per the survey), no integration change is needed — TYP001 will flow through automatically. Run the test and confirm.

**Step 4: Run full verifier test suite**

```bash
python -m pytest test_cli_assemble.py -v
```

Expected: All existing tests still pass, plus the new one.

**Step 5: Commit**

```bash
git add src/Python/tests/test_cli_assemble.py
git commit -m "test(assemble): verify TYP001 surfaces through the assemble verifier"
```

---

### Task 6: Documentation

**Files:**
- Modify: `.claude/rules/component-system.md` (Linter section / Assembly verifier table)
- Modify: `CLAUDE.md` (if a linter rules table exists; otherwise skip)

**Step 1: Update the verifier table in component-system.md**

Find the table titled `### Assembly verifier` (around line 95 of `.claude/rules/component-system.md`). Add a row for the new code in Layer 2:

```markdown
| 2. semantic lint | `SEM*`, `VAR*`, `SYN*`, `TYP*` | Undefined tasks, unused vars, syntax shape, **typed-parameter mismatches** — via `gui/backend/htn_linter.py` |
```

**Step 2: Add a new subsection documenting the convention**

After the verifier table, add:

```markdown
### Typed parameters (TYP001)

Components and levels may declare:

```prolog
type(typeName, instance).
signature(predName, [argType1, argType2, ...]).
```

`TYP001` fires when a *constant* argument at a typed call site is declared as a
different type, or has no `type/2` declaration at all. Variables and compound
terms are not yet checked. Rulesets with no `signature/2` declarations get no
TYP* diagnostics — the rule is fully opt-in.
```

**Step 3: Commit**

```bash
git add .claude/rules/component-system.md
git commit -m "docs(linter): document TYP001 and the type/signature convention"
```

---

## Verification (end-to-end)

After all six tasks land, run the full test sweep:

```bash
cd /Users/polycea/Projects/InductorHtn
source .venv/bin/activate

# Linter unit tests (custom suite)
cd src/Python/tests
python test_linter.py --verbose
python test_typed_params_linter.py

# Assembler/integration
python -m pytest test_cli_assemble.py -v

# Existing C++ parity tests should be unaffected — sanity check
cd /Users/polycea/Projects/InductorHtn/tests/cpp_parity
python -m pytest -v
```

Then manually exercise the assembler against an existing level (which has no `signature/2` declarations) and confirm it still verifies cleanly:

```bash
cd /Users/polycea/Projects/InductorHtn
PYTHONPATH=src/Python python -m htn_components assemble puzzle1 --verify-only
```

Expected: exit code 0, no TYP* diagnostics (because no signatures declared).

---

## Out of scope (defer to future plans)

- **TYP002** — variable type-flow analysis (track a variable's type through `if(...)` and check consistency at usage).
- **TYP003** — signature arity mismatch (existing SEM003 partially covers; revisit if needed).
- **Generator emission** of `type/2` and `signature/2` facts for companions-loop. The generator lives in a separate repo and is a separate work item; this plan only delivers the *consumer* (the linter) so that when the generator starts emitting them, validation is already in place.
- **Inline `?x:type` parameter syntax.** Requires `htn_parser.py` changes; not worth the cost for the MVP.
