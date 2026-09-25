# GameHack MVP Level

## Purpose

Smallest meaningful world that exercises the GameHack stack end to end:
`defeat` -> `wetAndFreeze` -> `bringEnemyTo` (the lurer) and `prepareToUseSkill`, `useSkillOnTarget` (the caster) -> the wet + chilled location combo.

Two companions and gob stand in a room; a wet pool is next door. Frost holds the only skill (frostSkill: chilled); gob is vulnerable to wet + chilled. The player is the only possible lurer, so there is one plan.

## Layer

level

## Dependencies

All GameHack components through the `defeat` goal.

## Examples

### Example 1: defeat(gob)

**Given:** MVP world state
**When:** `defeat(gob)`
**Then:** the only plan is `opStayInLocation(player), opAggro(gob, player), opMoveTo(player, room, pool), opAggroMoveTo(gob, room, pool), opMoveTo(frost, room, pool), opUseSkill(frost, frostSkill, gob), opApplyTag(stunned, gob), opApplyTag(dead, gob)`

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Only wetAndFreeze | No oil and no stun skill: oilAndBurn and stunAndSlow have no plan |
| P2 | Tags | After `defeat(gob)`, gob is stunned and dead |
| P3 | Two companions | Every plan ends with gob dead, and two different companions act in it |
