# Stun and Burn

## Purpose

Sequential strategy: the target is stunned, then burning. Each state comes from `applyTag`, so any way that applies the tag works. GameHack 1-6 declared this strategy in worlds that had no way to stun; it works in any world with a skill, a location or an agent that applies `stunned` and `burning` (gamehack_multipath has them).

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_tags` (applyTag)
- `gamehack/actions/gh_tag_application` (applyTagNotPresent, needed by applyTag)
- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_aggro`
- `gamehack/primitives/gh_skills`

## Methods

| Method | Description |
|--------|-------------|
| `stunAndBurn(?t)` | Stunned, then burning; ruled out if the target is immune to either |

## Examples

### Example 1: No way to stun

**Given:** nothing applies `stunned` or `burning`
**When:** `stunAndBurn(gob)`
**Then:** no plan

### Example 2: A world with the skills

**Given:** companionI (iceBlastSkill applies `stunned`) and companionF (fireballSkill applies `burning`) at the inn, gob at the hut
**When:** `stunAndBurn(gob)`
**Then:** the only plan is `opMoveTo(companionI, inn, hut), opUseSkill(companionI, iceBlastSkill, gob), opApplyTag(stunned, gob), opMoveTo(companionF, inn, hut), opUseSkill(companionF, fireballSkill, gob), opApplyTag(burning, gob)`

### Example 3: The building block works alone

**Given:** companionW with waterSkill
**When:** `applyTag(wet, gob)`
**Then:** the only plan is `opMoveTo(companionW, inn, hut), opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob)`

### Example 4: Immune to burning

**Given:** Example 2's world and `immune(gob, burning)`
**When:** `stunAndBurn(gob)`
**Then:** no plan

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Fails without skills | No plan when nothing applies stunned or burning |
| P2 | Works with skills | With the skills, the target ends stunned and burning |
