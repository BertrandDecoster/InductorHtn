# Authoring rulesets

Superseded. The 940-line authoring guide is replaced by a rubric, a pattern catalogue and a skill.

- The language (syntax, semantics, built-ins, traps), test-backed:
  [`language.md`](language.md)
- What good rulesets look like here: [`../authoring/rubric.md`](../authoring/rubric.md)
- Patterns, with the gold examples to read:
  [`../authoring/patterns.md`](../authoring/patterns.md)
- The workflow: the `htn-author` skill (`.claude/skills/htn-author/SKILL.md`)
- The ruleset guides that replaced this file: writing heuristics and
  validated optimizations in [`ruleset-writing.md`](ruleset-writing.md), creating levels with
  quality gates in [`ruleset-creating.md`](ruleset-creating.md), debugging and improving in
  [`ruleset-iterating.md`](ruleset-iterating.md), design rulings in
  [`ruleset-policies.md`](ruleset-policies.md). Where they disagree with `language.md`,
  `language.md` (test-backed) wins.

The old text is in git history (before commit `6ffa1e9`). It contradicted the engine in
places (`else`, `hidden`, `sortBy`, `try`), so don't use it.
