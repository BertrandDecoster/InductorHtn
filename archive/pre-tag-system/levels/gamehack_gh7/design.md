# GameHack GH7 Level

## Purpose

GH7-style world where all three strategies work. CompanionI holds iceBlastSkill (applies `stunned`), companionF holds fireballSkill (applies `burning`, is `slow`); the player holds none. Shrines at the sea, the mountain and the volcano grant waterSkill, iceBlastSkill and fireballSkill. `wetAndElectrify` needs waterSkill from the sea shrine (or the lake) and the static tesla tower's lightning.

## Layer

level

## Dependencies

All GameHack components through the `defeat` goal.

## Examples

### Example 1: defeat(gob)

**Given:** GH7 world state
**When:** `defeat(gob)`
**Then:** 27 plans: 6 stunAndSlow, 12 wetAndElectrify, 9 stunAndBurn; each ends with `opApplyTag(dead, gob)`

### Example 2: stunAndSlow

**Given:** GH7 world state
**When:** `stunAndSlow(gob)`
**Then:** 6 plans, among them companionI and companionF walking to the hut, `opSynchronize(companionI, companionF)`, then stunned and burning; in the others the player or a companion gets a skill from a shrine first

### Example 3: wetAndElectrify through the sea shrine

**Given:** no companion holds waterSkill; the sea shrine grants it
**When:** `wetAndElectrify(gob)`
**Then:** 12 plans; in some, the player gets waterSkill at the sea (`opGetSkill(player, waterSkill)`); gob is then lured to the tesla tower, which electrifies it

### Example 4: stunAndBurn

**Given:** GH7 world state
**When:** `stunAndBurn(gob)`
**Then:** 9 plans, among them companionI stunning and companionF burning

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Every strategy | stunAndSlow, wetAndElectrify and stunAndBurn all produce plans |
| P2 | Correct tags | stunAndSlow leaves gob stunned and burning; wetAndElectrify leaves it wet and electrified |
