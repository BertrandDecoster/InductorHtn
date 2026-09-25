# GameHack GH4 Level

## Purpose

GH4-style world where only `wetAndElectrify` works. Two companions have direct skills (companionE: lightningSkill, companionW: waterSkill); the player holds none. `stunAndSlow` and `stunAndBurn` fail: nothing stuns and nothing is slow. There are several ways to wet gob (companionW's skill, the lake, the sea) and to electrify it (companionE's skill, the tesla tower, the electricity elemental).

## Layer

level

## Dependencies

All GameHack components through the `defeat` goal.

## Examples

### Example 1: defeat(gob)

**Given:** GH4 world state
**When:** `defeat(gob)`
**Then:** 43 plans, all wetAndElectrify, each ending with `opApplyTag(dead, gob)`

### Example 2: Wet

**Given:** GH4 world state
**When:** `applyTag(wet, gob)`
**Then:** 7 plans: companionW's waterSkill, or a lure to the lake or to the sea (any of the three companions lures)

### Example 3: Electrified

**Given:** GH4 world state
**When:** `applyTag(electrified, gob)`
**Then:** 7 plans: companionE's lightningSkill (it already stands with gob), or a lure to the tesla tower or to the electricity elemental

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Strategy | Only wetAndElectrify plans (43); stunAndSlow and stunAndBurn have none |
| P2 | Tags | After the first plan, gob is wet, electrified and dead |
