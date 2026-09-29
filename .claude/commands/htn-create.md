---
description: Create a new HTN level from a design brief, following the ruleset-creating workflow, ending with the /htn-audit gate table.
argument-hint: <target directory or file> <design brief>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, mcp__indhtn__indhtn_create_session, mcp__indhtn__indhtn_load_files, mcp__indhtn__indhtn_load_source, mcp__indhtn__indhtn_introspect, mcp__indhtn__indhtn_lint, mcp__indhtn__indhtn_find_plans, mcp__indhtn__indhtn_get_decomposition_tree, mcp__indhtn__indhtn_method_failures, mcp__indhtn__indhtn_list_goals, mcp__indhtn__indhtn_query, mcp__indhtn__indhtn_add_facts, mcp__indhtn__indhtn_remove_facts, mcp__indhtn__indhtn_snapshot_state, mcp__indhtn__indhtn_restore_state, mcp__indhtn__indhtn_end_session
---

You are creating a new InductorHTN level from a design brief. The workflow is
`docs/reference/ruleset-creating.md`, included below with its companions —
follow its seven steps in order; this command only adds the mechanics.

@docs/reference/ruleset-creating.md
@docs/reference/ruleset-policies.md
@docs/reference/ruleset-htn-syntax.md
@docs/reference/ruleset-writing.md

## The request

> $ARGUMENTS

The **first phrase** names where the level goes (a directory like
`prototypes/<name>/` or an explicit `.htn` path); everything after it is the
design brief. Restate the brief in 2-3 sentences, then execute the workflow:

1. **Sketch first (in your reply, before any file):** the layered unlock-DAG
   backward from each challenge goal — layers of facts/actions, the choice
   facts that gate edges, the intended bottlenecks. State the expected causal
   depth per challenge (target 3-5) and the intended solution clusters
   (target >= 2). Get this structure right before writing syntax; depth comes
   from operators producing facts that later `if()` preconditions consume.
2. **Write the level** (`Write`, ASCII only): facts and general verbs, then
   methods bottom-up with `opResolveAtom(atom, method)` markers and
   `challengeAtom`/`atomMethod` metadata, exemplar patterns in hand (step 3
   of the workflow). Include a `playLevel()`-style root binding the loadout
   in-plan (`skillIdx` + `<(?i1,?i2)` for unordered pairs) and `goals(...)`.
3. **Lint + plan** until the correctness floor holds (workflow step 4;
   benign codes only per POL-7).
4. **DAG gate** (workflow step 5) via Bash — depth 3:5 asserted, replay
   verified. If a challenge is shallow, thread state, don't pad `do()`.
5. **Write `quality.json`** next to the level (copy the fortress one's shape)
   and run the **harness** (workflow step 6). Iterate with the facts-first
   fix moves until error gates pass and each WARN is fixed or defensible.
6. **Report** with the /htn-audit gate table (its phase 6 format), the DAG
   summary per challenge, and every accepted WARN with a reason. Never claim
   a gate passed without showing the tool output.
