# GameHack Multipath Level

## Purpose

Prove the GameHack stack composes broadly, not just end to end. Where `gamehack_mvp` has a single plan, this level arranges a world in which all three strategies succeed, each combo has several locations, and skills are held or granted by shrines, so `defeat(gob)` returns many structurally distinct plans.

## Layer

level

## Dependencies

All GameHack components through the `defeat` goal.

## World Overview

- Companions: `player`, `companionA` (frostSkill: chilled), `companionB` (fireballSkill: burning, slow), `companionC` (no skill).
- Enemies: `gob` (target), `teslaTower` (static, lightningSkill), `iceElemental` (iceBlastSkill).
- Locations: `arena` (where `gob` is), `forge`, `glacier`, `lakeShore`, `sea`, `volcano`, `refinery`.
- `lakeShore` and `sea` are wet, `glacier` is ice, `refinery` holds oil.
- Objects that grant a skill: `volcanoShrine` (fireballSkill), `glacierShrine` (iceBlastSkill: stunned), `shoreShrine` (frostSkill).
- gob is vulnerable to wet + chilled, ice + chilled and oil + burning.

## Examples

### Example 1: wetAndFreeze

**Given:** multipath world state
**When:** `wetAndFreeze(gob)`
**Then:** 36 plans (three locations, a lurer and a chilled caster)

### Example 2: stunAndSlow

**Given:** multipath world state
**When:** `stunAndSlow(gob)`
**Then:** 12 plans, each with `opSynchronize`

### Example 3: oilAndBurn

**Given:** multipath world state
**When:** `oilAndBurn(gob)`
**Then:** 12 plans (gob lured into the refinery)

### Example 4: Plan multiplicity

**Given:** multipath world state
**When:** `defeat(gob)`
**Then:** 60 distinct plans (36 + 12 + 12)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Water and ice | gob is frozen at the lake shore, the sea and the glacier |
| P2 | Held skill | companionA, who holds frostSkill, chills gob while another companion lures it |
| P3 | Skill from a shrine | Some stunAndSlow plan has `opSwapSkill` or `opGetSkill` with `opSynchronize` |
| P4 | Oil becomes burning | oilAndBurn leaves the refinery burning and gob dead |
| P5 | Two companions | Every plan ends with gob dead, and two different companions act in it |
