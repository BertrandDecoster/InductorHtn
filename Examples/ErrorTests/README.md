# Error Test Rulesets

This directory contains intentionally broken HTN rulesets for testing the linter and analyzer tools.

## File Naming Convention

Files are named: `{category}_{specific_error}.htn`

## Categories

### Syntax Errors (`syntax_*`)
- `syntax_unbalanced_parens_in_if.htn` - Missing closing paren in if()
- `syntax_unbalanced_parens_in_do.htn` - Extra closing paren in do()
- `syntax_missing_period.htn` - Rule without terminating period
- `syntax_missing_arrow.htn` - Rule without :- separator
- `syntax_unclosed_string.htn` - String literal not closed
- `syntax_invalid_variable_name.htn` - Variable name starts with number
- `syntax_mismatched_brackets.htn` - Square brackets instead of parens

### Variable Errors (`var_*`)
- `var_unbound_in_do.htn` - Variable in do() not bound in if()
- `var_unbound_in_add.htn` - Variable in add() not bound elsewhere
- `var_unused_in_head.htn` - Variable in head never used in body
- `var_singleton_warning.htn` - Variable appears only once

### Semantic Errors (`semantic_*`)
- `semantic_dead_operator.htn` - Operator never called
- `semantic_dead_method.htn` - Method never called
- `semantic_cycle_direct.htn` - Method calls itself directly
- `semantic_cycle_indirect.htn` - A calls B, B calls A
- `semantic_undefined_method.htn` - Calls non-existent method/operator
- `semantic_undefined_predicate.htn` - Condition uses undefined predicate
- `semantic_arity_mismatch_call.htn` - Wrong number of arguments
- `semantic_arity_mismatch_predicate.htn` - Same predicate, different arities
- `semantic_duplicate_operator.htn` - Same operator defined twice
- `semantic_unsatisfiable_condition.htn` - Condition is always false
- `semantic_no_base_case.htn` - Recursion without termination
- `semantic_unreachable_else.htn` - else branch never reached

### HTN-Specific Errors (`htn_*`)
- `htn_operator_with_if_do.htn` - Operator using method syntax
- `htn_method_with_del_add.htn` - Method using operator syntax
- `htn_else_without_prior_method.htn` - else on first method
- `htn_allof_on_operator.htn` - allOf modifier on operator
- `htn_empty_do_clause.htn` - Method does nothing
- `htn_empty_if_risky.htn` - Multiple always-true methods
- `htn_try_always_fail.htn` - try() around always-failing task

### State Invariant Errors (`invariant_*`)
- `invariant_duplicate_position.htn` - Can place two units on same tile
- `invariant_orphan_unit.htn` - Unit left without position

### Logic Errors (`logic_*`)
- `logic_del_nonexistent.htn` - Deleting fact that doesn't exist
- `logic_add_duplicate.htn` - Adding same fact multiple times

## Usage

These files are used by Phase 1 (Syntax Linter) and Phase 2 (Semantic Analyzer) to verify error detection works correctly.

Each file contains a comment header explaining:
1. What error it contains
2. What the tool should detect/report
