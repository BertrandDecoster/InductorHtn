# Stun and Burn (Documented Failure)

## Purpose

Sequential damage strategy: apply ice tag then fire tag. This strategy was declared in GameHack versions 1-6 but never worked because no ally had iceSkill and no location produced ice. The building blocks (applyTag) work correctly - the strategy fails due to missing world state, not broken logic.

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_tags` (applyTag)
- `gamehack/actions/gh_tag_application` (applyTagNotPresent - needed for applyTag dispatch)
- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_aggro`
- `gamehack/primitives/gh_skills`

## Methods

| Method | Description |
|--------|-------------|
| `stunAndBurn(?t)` | Apply ice then fire to enemy target |

## Examples

### Example 1: Standard world - fails (no ice/fire path)

**Given:**
- No `skillAppliesTag(?, ice)`, no `locationCanApplyTag(?, ice)`, no mob with ice skill

**When:**
- `stunAndBurn(gob)`

**Then:**
- Planning fails (no path to apply ice tag)

### Example 2: Hypothetical world with ice+fire skills

**Given:**
- Ally has iceSkill with `skillAppliesTag(iceSkill, ice)`
- Ally has fireballSkill with `skillAppliesTag(fireballSkill, fire)`

**When:**
- `stunAndBurn(gob)`

**Then:**
- Plan succeeds, both ice and fire tags applied

### Example 3: Individual tag works (wet via ally)

**Given:**
- Ally with waterSkill, `skillAppliesTag(waterSkill, wet)`

**When:**
- `applyTag(wet, gob)` (individual building block, not stunAndBurn)

**Then:**
- Plan succeeds, wet tag applied (building blocks work)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Fails without skills | No plan when ice/fire skills absent from world |
| P2 | Works with skills | Plan succeeds when ice/fire skills provided |
