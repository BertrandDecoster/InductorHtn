---
description: Improve an HTN ruleset from a natural-language instruction, grounded in syntax + exemplars and verified by planning.
argument-hint: <target file or keyword> <how to improve it>
allowed-tools: Read, Edit, Glob, Grep, mcp__indhtn__indhtn_create_session, mcp__indhtn__indhtn_load_files, mcp__indhtn__indhtn_introspect, mcp__indhtn__indhtn_lint, mcp__indhtn__indhtn_find_plans, mcp__indhtn__indhtn_get_decomposition_tree, mcp__indhtn__indhtn_method_failures, mcp__indhtn__indhtn_list_goals, mcp__indhtn__indhtn_query, mcp__indhtn__indhtn_add_facts, mcp__indhtn__indhtn_remove_facts, mcp__indhtn__indhtn_snapshot_state, mcp__indhtn__indhtn_restore_state, mcp__indhtn__indhtn_end_session
---

You are improving an InductorHTN ruleset. Work through the phases **in order**.
Do NOT edit the target until you have loaded the context (phases 1-2) and captured
a baseline (phase 4). Loading the syntax + good examples first is the whole point of
this command: it keeps the edit grounded in the project's idioms instead of guesswork.

## 1. Syntax & guidelines (your authority)

These reference docs are included below. Treat them as the source of truth for syntax
and authoring heuristics; follow them over anything you recall:

@docs/reference/ruleset-htn-syntax.md
@docs/reference/ruleset-writing.md
@docs/upgrades/ruleset-keywords.md
@docs/reference/ruleset-iterating.md
@docs/reference/ruleset-policies.md

Key invariants from the project (also in CLAUDE.md): variables are `?prefixed`;
methods are `task() :- if(...), do(...).`; operators are `op() :- del(...), add(...).`;
numeric state uses `increase()`/`decrease()`; sources must be **ASCII only** (the
loader is strict UTF-8 -- no em/en dashes or smart quotes).

## 2. Reference rulesets (good examples, same dialect)

Read `docs/reference/exemplars/README.md` (the index). Then **read the 1-2 exemplars
whose pattern best matches the requested change** -- e.g.:
- connectivity / routing / "an edge that appears under a condition" -> `logistics.htn`
- recursion / "clear or unwind a structure first" -> `blocksworld.htn`
- resource counts / numeric fluents / readiness gates -> `barman.htn`
- multi-goal missions / act-on-each-reachable-target (`anyOf`) -> `rover.htn`

If the target is a game/combat level, also skim
`prototypes/fortress-loadout/level.htn` and `Examples/TrunkThumper.htn` for in-repo
idiom. Note the benign lint codes the README lists so you don't chase them later.

## 3. Parse the request

The request is:

> $ARGUMENTS

The **first phrase** names the target ruleset -- a path, or a keyword like
`fortress`. Everything after it is the improvement instruction. Resolve a keyword to
a file with `Glob` (try `**/*<keyword>*/*.htn`, then `Examples/*<keyword>*.htn`,
preferring `prototypes/`, `levels/`, `Examples/`). If several match, pick the most
specific and **state which file you chose**; if none match, stop and ask.

Restate, in one or two sentences, the change you understand you are making.

## 4. Understand the target (baseline -- the "before")

- `Read` the resolved file in full.
- `indhtn_introspect` on its source: confirm methods/operators/facts parsed as you
  expect.
- `indhtn_lint` on its source: record existing diagnostics (so you can tell what your
  edit introduces vs. what was already there). Accept only what the canonical
  benign-lint list allows (POL-7 in the included `ruleset-policies.md`; note
  `SEM004/005` are benign only for POL-1 declared latents and alternate-entry
  tasks); `VAR003` and `TYP010` are real.
- `indhtn_create_session` + `indhtn_load_files` on the file, then `indhtn_find_plans`
  on each goal from its `goals(...)` directive (`indhtn_list_goals` if unsure).
  Record the plan **count and shapes** -- this is your before/after anchor.

## 5. Apply the improvement (edit in place)

Edit the target file directly with `Edit` (git is the safety net). Follow the loaded
guidelines and the exemplar idioms:
- model **data + verbs**: prefer new facts + general methods over special-case
  methods; keep one source of truth.
- introduce an indirection by adding the intermediate **state** and gating the
  affected method/connection on it (e.g. a blocking element that a condition clears),
  mirroring how `logistics.htn` routes over conditional connectivity.
- prefer plain alternative methods (enumerated as separate plans) over `else`, unless
  a genuine priority ladder is intended.
- ASCII only.

Make the smallest coherent change that satisfies the instruction; comment new
vocabulary briefly.

## 6. Verify (iterate until green)

- `indhtn_lint` the edited source: it must introduce **no new errors** and no new
  non-benign warnings (compare against the phase-4 baseline).
- `indhtn_load_files` + `indhtn_find_plans`:
  - (a) the **prior goals still solve** (plan count/shape sane vs. baseline -- explain
    any intended change), and
  - (b) the **new mechanic is reachable**: construct a focused goal or flip the
    relevant facts with `indhtn_snapshot_state` / `indhtn_add_facts` /
    `indhtn_remove_facts` / `indhtn_restore_state` to prove the new path fires when it
    should AND is blocked when it should not (e.g. connected only once frozen).
- If you get fewer plans than expected, run `indhtn_method_failures` to localize which
  gate or subtask blocked, fix, and re-run. Do not hand-wave -- let the tools say
  what's wrong.
- If the change alters **how a challenge is solved** (new mechanic, new/removed
  method or operator chain -- not a pure fact tweak), run the DAG tool before and
  after and report the causal depth delta:
  `source .venv/bin/activate && PYTHONPATH=mcp-server python -m indhtn_quality.dag
  <level> --goal "<challenge>()." --facts <loadout facts> --format summary`.
  Depth should stay in (or move toward) the 3-5 band; a drop toward 1 means the
  new path is a shortcut montage (see `ruleset-creating.md`).
- `indhtn_end_session` when done.

## 7. Report

Summarize: the file changed and the one-line intent; what you added (facts, methods,
operators); baseline vs. new plan counts with the evidence (the `find_plans` output
for the new-mechanic scenario, both the firing and the blocked case); lint status; and
any follow-ups. If the target has a `quality.json` (the fortress level does), suggest
running the harness to confirm the loadout matrix and property gates still hold:
`PYTHONPATH=mcp-server python -m indhtn_quality.harness <dir>/quality.json`.
**Never claim success without showing the lint + find_plans output.**
