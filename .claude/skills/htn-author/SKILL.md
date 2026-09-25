---
name: htn-author
description: Use when writing, extending or fixing an InductorHTN ruleset (.htn): a level, a component, an example, or a domain in a benchmark task. Covers the design workflow, the owner's quality rubric, pattern-based example lookup, and the compile/lint/plan/review checks.
---

# Writing an InductorHTN ruleset

Correctness is rarely the problem. **Design is.** Rulesets fail when they become imperative
scripts of one-off helpers, effect engines, or invented vocabularies. Follow these steps in
order.

## 1. Read the two references (once per session)

- `docs/reference/language.md`: the dialect. Every example in it is tested. Trust it over
  anything you remember from SWI-Prolog, PDDL or other HTN systems.
- `docs/authoring/rubric.md`: the owner's quality rules, R1-R9, with good and bad code.

## 2. State the need and the strategies before any code

Write down in a few lines, in comments or in your head:
- **The need**, as a task: `damage(?e)`, `travel(?who, ?to)`, `clearRoom(?r)`.
- **The strategies**, one line each: what must become true, in order. Example: "wet, then
  electrocuted"; "stunned and slowed together by two allies".
- **What makes each strategy possible**, the facts its `if()` will check. Choose skills by
  property (`skillAppliesTag(?s, stun)`), never by name.
- **The expected plans** on the sample world: which strategies should work, with whom.

If a strategy reads like "go here, do this, then do that", rewrite it as the **states to
achieve** (rubric R4).

## 3. Look up examples by pattern

Open `docs/authoring/patterns.md`. Name the patterns your design uses (P1 strategy menu, P2
feasibility in `if()`, P4 a verb whose methods are the ways, P6 navigation, and so on). Read the
listed lines of 2-3 examples, and imitate their shape. Pick by pattern, not by subject. Don't
imitate anything the rubric calls slop, and don't copy from `bench/` or git history.

## 4. Write it

- Reuse verbs that exist. Search `components/` and the examples for a verb that already
  achieves the state (`applyTag`, `prepareToUseSkill`, `navigateTo`, `bringMobToLocation`)
  before writing a new one.
- Levels are facts plus a goal. Components never name level-specific characters, places or
  skills.
- Operators are game actions, `op...`, with one clear effect. Guard each one: `del` only what
  exists, `add` only what doesn't.
- One short comment line per method or case. No essays.

## 5. Check (the hook also runs step a on every save)

a. `python -m htn_components check <file>`: compile with real line numbers, plus lint. Fix
   every error. Never weaken a check or a test to get past it.
b. `python -m htn_components check <file> --goal "task(args)."`: compare the plan set with
   what you expected in step 2. **Read the plans.** Too many plans usually means a verb has
   alternatives that should exclude each other. Too few means a condition is wrong.
c. No plan? Probe bottom-up: query each subtask alone, or use the MCP tool
   `indhtn_method_failures` to see which method fails and at which condition.
d. Components and levels: `python -m htn_components test <path>`. Tests assert the plan set
   (`assert_plan`, `assert_no_plan`, `assert_operator_sequence` in
   `src/Python/htn_test_framework.py`).

## 6. Review

Ask the `htn-reviewer` agent to review the files (it starts from a fresh context). Fix its
high-severity findings, or explain why a finding is wrong. Report its score to the user. The
owner's own rating is the final word.
