# Oil and Burn

## Purpose

Two companions: a lurer brings the target onto oil, and a second companion sets it burning there. Burning on oil turns the oil into a burning location and sets everyone there burning (the lurer and the caster included), and defeats the enemies vulnerable to oil + burning. The strategy's `if()` requires that vulnerability.

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_tags` (useSkillOnTarget and the location combos)
- `gamehack/primitives/gh_aggro` (bringEnemyTo)
- `gamehack/primitives/gh_skills` (prepareToUseSkill)

## Methods

| Method | Description |
|--------|-------------|
| `oilAndBurn(?t)` | A lurer brings `?t` onto oil; a second companion sets it burning there. If `?t` already stands on oil, the caster alone sets it burning |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |
| `locationCanApplyTag(?l, oil)` | The oil |
| `vulnerableToLocationCombo(?t, oil, burning)` | The combo defeats it |
| `skillAppliesTag(?s, burning)` | A fire skill |
| `companion(?lurer)`, `companion(?caster)` | Two distinct companions |

## Examples

Same world as wet_and_freeze: player, frost and pyro at camp; gob at the hut; the kitchen holds oil.

### Example 1: Lured onto oil and burned

**Given:** `vulnerableToLocationCombo(gob, oil, burning)`
**When:** `oilAndBurn(gob)`
**Then:** two plans, one per lurer (player or frost); pyro walks to the kitchen and casts; `opRemoveLocationTag(oil, kitchen), opAddLocationTag(burning, kitchen)`, the lurer, pyro and gob burning, then `opApplyTag(dead, gob)`

### Example 2: Not vulnerable

**Given:** gob only vulnerable to wet + chilled
**When:** `oilAndBurn(gob)`
**Then:** no plan

### Example 3: No oil

**Given:** no oil location
**When:** `oilAndBurn(gob)`
**Then:** no plan

### Example 4: Already standing on oil

**Given:** gob already stands in the kitchen
**When:** `oilAndBurn(gob)`
**Then:** no lurer: the only plan is pyro walking to the kitchen and setting gob burning (the oil becomes burning, pyro and gob burn, gob is dead)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Oil becomes burning | Afterwards the location is burning, no longer oil, and the target is dead |
