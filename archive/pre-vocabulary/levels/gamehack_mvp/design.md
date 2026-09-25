# GameHack MVP Level

## Purpose

Smallest meaningful world that exercises the decomposed GameHack stack end to end:
`planToDamage` -> `wetAndElectrocute` -> `applyTag` -> dispatcher path 1 (ally-with-skill) -> `opApplyTag`.

One ally (`player`) co-located with one enemy (`gob`). The ally has both `waterSkill` and `lightningSkill` directly. Co-location makes `goToSameLocation` a no-op (`opStayInLocation`). Aggro / luring / skill-acquisition paths are deliberately not exercised.

## Layer

level

## Dependencies

- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_tags`
- `gamehack/primitives/gh_skills`
- `gamehack/actions/gh_tag_application`
- `gamehack/strategies/wet_and_electrocute`
- `gamehack/goals/plan_to_damage`

`stun_and_slow_skill` is pulled in transitively via `plan_to_damage`; its preconditions fail on this world so the planner backtracks to `wetAndElectrocute`. `gh_aggro` is not needed.

## Examples

### Example 1: planToDamage(gob) succeeds

**Given:** MVP world state
**When:** `planToDamage(gob)`
**Then:** A plan exists and contains `opApplyTag(wet, gob)` and `opApplyTag(electrocute, gob)`.

### Example 2: wet applied via player's waterSkill

**Given:** `player` has `waterSkill`, co-located with `gob`
**When:** `applyTag(wet, gob)`
**Then:** Plan contains `opApplyTag(wet, gob)` (no aggro/movement operators).

### Example 3: electrocute applied via player's lightningSkill

**Given:** `player` has `lightningSkill`, co-located with `gob`
**When:** `applyTag(electrocute, gob)`
**Then:** Plan contains `opApplyTag(electrocute, gob)` (no aggro/movement operators).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Fallback to wetAndElectrocute | `planToDamage` plan contains no `opSynchronize` (stunAndSlowSkill precondition fails and is skipped). |
| P2 | Both tags applied | After running `planToDamage(gob)`, state contains `hasTag(gob, wet)` and `hasTag(gob, electrocute)`. |
| P3 | No movement required | Plan contains no `opMoveTo` or `opAggroMoveTo` (ally and target already co-located). |
