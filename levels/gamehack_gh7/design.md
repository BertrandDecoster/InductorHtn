# GameHack GH7 Level

## Purpose

GH7-style world demonstrating both `stunAndSlowSkill` and `wetAndElectrocute` strategies. CompanionI has iceBlastSkill (stun), companionF has fireballSkill (fire + slow). The `stunAndSlowSkill` strategy uses two allies preparing independently then synchronizing. The `wetAndElectrocute` strategy requires learning waterSkill at sea or using the lake location.

## Layer

level

## Dependencies

All GameHack components through `plan_to_damage` goal.

## Examples

### Example 1: planToDamage(gob) succeeds

**Given:** GH7 world state
**When:** `planToDamage(gob)`
**Then:** Plans found from both strategies

### Example 2: stunAndSlowSkill works

**Given:** GH7 world with companionI + companionF
**When:** `stunAndSlowSkill(gob)`
**Then:** opSynchronize in plan, stun+fire tags applied

### Example 3: wetAndElectrocute via skill acquisition

**Given:** No ally has waterSkill natively, but sea teaches it
**When:** `wetAndElectrocute(gob)`
**Then:** Ally learns waterSkill at sea, then applies wet+electrocute

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Both strategies | Both stunAndSlowSkill and wetAndElectrocute produce plans |
| P2 | Correct tags | Target has appropriate tags after each strategy |
