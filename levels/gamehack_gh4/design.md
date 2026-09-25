# GameHack GH4 Level

## Purpose

GH4-style world where exactly one strategy works: `wetAndFreeze`. companionE holds lightningSkill (electrified), companionW holds frostSkill (chilled), the player holds none. The lake and the sea are wet; gob is vulnerable to wet + chilled. Nothing stuns and there is no oil, so `oilAndBurn` and `stunAndSlow` have no plan.

## Layer

level

## Dependencies

All GameHack components through the `defeat` goal.

## Examples

### Example 1: defeat(gob)

**Given:** GH4 world state
**When:** `defeat(gob)`
**Then:** 4 plans: the player or companionE lures gob into the lake or the sea; companionW walks there and chills it (`opApplyTag(stunned, gob), opApplyTag(dead, gob)`)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | One strategy | 4 wetAndFreeze plans; oilAndBurn and stunAndSlow have none |
| P2 | Tags | After the first plan, gob is stunned and dead |
| P3 | Two companions | Every plan ends with gob dead, and two different companions act in it |
