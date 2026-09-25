# GameHack GH4 Level

## Purpose

GH4-style world demonstrating the `wetAndElectrocute` strategy. Two allies have direct skills (companionE: lightningSkill, companionW: waterSkill). The `stunAndSlowSkill` strategy is not viable because no stun/slow skills exist. Multiple paths exist for applying wet (ally skill, lake, sea) and electrocute (ally skill, teslaTower, electricityElemental).

## Layer

level

## Dependencies

All GameHack components through `plan_to_damage` goal.

## Examples

### Example 1: planToDamage(gob) succeeds

**Given:** GH4 world state
**When:** `planToDamage(gob)`
**Then:** Plan found using wetAndElectrocute strategy

### Example 2: Wet via ally skill

**Given:** companionW has waterSkill
**When:** `applyTag(wet, gob)`
**Then:** companionW applies wet to gob

### Example 3: Electrocute via ally skill

**Given:** companionE has lightningSkill
**When:** `applyTag(electrocute, gob)`
**Then:** companionE applies electrocute to gob

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Strategy | Only wetAndElectrocute plans (no stunAndSlowSkill) |
| P2 | Both tags | Target has both wet and electrocute after plan |
