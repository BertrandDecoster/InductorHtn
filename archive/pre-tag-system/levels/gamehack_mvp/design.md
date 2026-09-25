# GameHack MVP Level

## Purpose

Smallest meaningful world that exercises the GameHack stack end to end:
`defeat` -> `wetAndElectrify` -> `applyTag` -> applyTagNotPresent way 1 (a companion skill) -> `opUseSkill`, `opApplyTag`.

One companion (`player`) stands with one enemy (`gob`) and holds both `waterSkill` and `lightningSkill`. Standing together makes `goToSameLocation` a no-op (`opStayInLocation`). Aggro, luring and skill objects are deliberately not exercised.

## Layer

level

## Dependencies

- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_tags`
- `gamehack/primitives/gh_skills`
- `gamehack/actions/gh_tag_application`
- `gamehack/strategies/wet_and_electrify`
- `gamehack/goals/defeat`

`stun_and_slow` and `stun_and_burn` come in through `defeat`; their conditions fail on this world, so `wetAndElectrify` is the only plan.

## Examples

### Example 1: defeat(gob)

**Given:** MVP world state
**When:** `defeat(gob)`
**Then:** the only plan is `opStayInLocation(player), opUseSkill(player, waterSkill, gob), opApplyTag(wet, gob), opStayInLocation(player), opUseSkill(player, lightningSkill, gob), opApplyTag(electrified, gob), opApplyTag(dead, gob)`

### Example 2: wet through the player's waterSkill

**Given:** `player` holds `waterSkill` and stands with `gob`
**When:** `applyTag(wet, gob)`
**Then:** the only plan is `opStayInLocation(player), opUseSkill(player, waterSkill, gob), opApplyTag(wet, gob)`

### Example 3: electrified through the player's lightningSkill

**Given:** `player` holds `lightningSkill` and stands with `gob`
**When:** `applyTag(electrified, gob)`
**Then:** the only plan is `opStayInLocation(player), opUseSkill(player, lightningSkill, gob), opApplyTag(electrified, gob)`

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No stunAndSlow | One companion and no slow skill: `stunAndSlow(gob)` has no plan |
| P2 | Tags | After `defeat(gob)`, gob is wet, electrified and dead |
| P3 | No movement | No `opMoveTo` or `opAggroMoveTo` (companion and target stand together) |
