# GameHack GH7 Level

## Purpose

GH7-style world where all three strategies work. companionI holds iceBlastSkill (stunned), companionF holds fireballSkill (burning, slow), the player holds none. Shrines at the sea, the mountain and the volcano grant frostSkill (chilled), iceBlastSkill and fireballSkill. The lake is wet and the kitchen holds oil; gob is vulnerable to wet + chilled and to oil + burning.

## Layer

level

## Dependencies

All GameHack components through the `defeat` goal.

## Examples

### Example 1: defeat(gob)

**Given:** GH7 world state
**When:** `defeat(gob)`
**Then:** 18 plans: 6 wetAndFreeze, 6 oilAndBurn, 6 stunAndSlow

### Example 2: wetAndFreeze through the sea shrine

**Given:** nobody holds a chilled skill
**When:** `wetAndFreeze(gob)`
**Then:** 6 plans (3 lurers, and a caster who gets frostSkill at the sea shrine); for example companionI lures gob into the lake while the player gets frostSkill and chills it there

### Example 3: oilAndBurn

**Given:** GH7 world state
**When:** `oilAndBurn(gob)`
**Then:** 6 plans; for example the player lures gob into the kitchen and companionF sets it burning: the oil becomes burning, the player, companionF and gob burn, gob is dead

### Example 4: stunAndSlow

**Given:** GH7 world state
**When:** `stunAndSlow(gob)`
**Then:** 6 plans, among them companionI and companionF walking to the hut, `opSynchronize(companionI, companionF)`, then stunned and burning

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Every strategy | wetAndFreeze, oilAndBurn and stunAndSlow all produce plans |
| P2 | Oil becomes burning | oilAndBurn leaves the kitchen burning and gob dead |
| P3 | Two companions | Every plan ends with gob dead, and two different companions act in it |
