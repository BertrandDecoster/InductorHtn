---
description: Audit an HTN ruleset against the quality gates - lint vs POL-7, causal-depth DAG, loadout-sweep harness - and report a gate table with evidence.
argument-hint: <target file or keyword>
allowed-tools: Read, Glob, Grep, Bash, mcp__indhtn__indhtn_create_session, mcp__indhtn__indhtn_load_files, mcp__indhtn__indhtn_introspect, mcp__indhtn__indhtn_lint, mcp__indhtn__indhtn_find_plans, mcp__indhtn__indhtn_get_decomposition_tree, mcp__indhtn__indhtn_method_failures, mcp__indhtn__indhtn_list_goals, mcp__indhtn__indhtn_query, mcp__indhtn__indhtn_end_session
---

You are auditing an InductorHTN ruleset for quality — not editing it. Work
through the phases **in order** and end with the gate table. An audit that
skips a gate must say so and why.

## 1. Authority

The gates, targets, and rulings are included below. Follow them over
anything you recall:

@docs/reference/ruleset-creating.md
@docs/reference/ruleset-policies.md

## 2. Resolve the target

The request is:

> $ARGUMENTS

Resolve a keyword to a file with `Glob` (try `**/*<keyword>*/*.htn`, then
`Examples/*<keyword>*.htn`, preferring `prototypes/`, `levels/`, `Examples/`).
If several match, pick the most specific and **state which file you chose**;
if none match, stop and ask. `Read` the file in full — note declared latents
(POL-1 comment blocks), `challengeAtom`/`atomMethod` metadata, and the
`goals(...)` directive.

## 3. Lint, classified against POL-7

`indhtn_lint` the source. Classify EVERY diagnostic into one of:
- **real** — needs fixing (includes any `TYP010`, `VAR003` unless a probe
  variable, undeclared `SEM004/005`);
- **benign per POL-7** — cite the table row;
- **declared latent per POL-1** — cite the declaring comment (file:line).

An `SEM004/005` with no POL-1 declaration is a finding, not noise.

## 4. DAG gate (causal depth + structure)

For each challenge goal (from metadata or `indhtn_list_goals`), pick a
loadout/facts set that solves it (use `indhtn_query` on the pool + a quick
`indhtn_find_plans` if unsure), then run via Bash:

```
source .venv/bin/activate && PYTHONPATH=mcp-server python -m indhtn_quality.dag \
    <level.htn> --goal "<challenge>()." --facts "<fact>" "<fact>" \
    --format summary --assert-depth 3:5 --verify-replay 1
```

Record per challenge: causalDepth (and min over plans), plan-length range,
cluster count, bottleneck facts, and any verify-replay warnings. For the
report's appendix, also render `--format mermaid` for the deepest challenge.

## 5. Harness sweep

If a `quality.json` exists next to the level, run:

```
source .venv/bin/activate && PYTHONPATH=mcp-server python -m indhtn_quality.harness <dir>/quality.json
```

If none exists, **generate a starter one** (say so in the report): copy the
shape of `prototypes/fortress-loadout/quality.json`, filling the pool query,
challenge goals, full/playRoot goals, and metadata queries from what you read
in phase 2; leave thresholds at their defaults (P1 min 6 for a 21-loadout
pool — scale to `ceil(loadouts/3)` for smaller pools). Write it next to the
level so the audit is reproducible.

Read the matrix like a designer: FULL-column spread, who dies where, the
generativity ranking.

## 6. Report — the gate table

End with exactly this table, one row per gate, each row backed by tool output
you actually showed (never a bare verdict):

| Gate | Value | Target | Status | Evidence |
|------|-------|--------|--------|----------|
| lint | ... | 0 unclassified | PASS/FAIL | phase 3 |
| causal depth per challenge | ... | 3-5 | PASS/WARN | phase 4 summary |
| diversity (clusters) | ... | >= 2 | PASS/WARN | harness |
| decision matters (P2) | ... | some-not-all | PASS/FAIL | harness |
| choke points (P1) | ... | >= threshold | PASS/FAIL | harness |
| dead content (P3/P4/P5) | ... | none undeclared | PASS/FAIL | harness |
| gating real (P6) | ... | no leaks | PASS/FAIL | harness |
| dominance | ... | no dominant pair | PASS/WARN | harness |
| generativity | ... | no zero-score skill | PASS/WARN | harness |
| cross-check | ... | playRoot = sum(FULL) | PASS/FAIL | harness |

Then: the top 3 concrete improvements ranked by leverage (facts-first fix
moves per `ruleset-creating.md` step 6), and every accepted WARN with its
reason. **Never claim a verdict without showing the tool output.**
