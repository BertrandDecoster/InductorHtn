# Stun and Slow Skill

## Purpose

Simultaneous two-ally damage strategy. Two distinct allies prepare independently (one with a stun skill, one with a slow skill), synchronize, then both use their skills on the target. This is the most advanced strategy in GameHack, requiring two allies and demonstrating the `opSynchronize` pattern for coordinated execution.

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_tags` (useSkillOnTarget)
- `gamehack/primitives/gh_skills` (prepareToUseSkill)
- `gamehack/primitives/gh_movement` (movement for positioning)

## Operators

| Operator | Description |
|----------|-------------|
| `opSynchronize(?a1, ?a2)` | Sync point between prepare and use phases |

## Methods

| Method | Description |
|--------|-------------|
| `stunAndSlowSkill(?t)` | Two-ally coordinated stun + slow attack on enemy target |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |
| `skillAppliesTag(?skill, stun)` | A skill that produces stun effect |
| `skillHasTag(?skill, slow)` | A skill that IS slow (property of the skill itself) |
| `ally(?a1)`, `ally(?a2)` | Two distinct allies needed |
| `immune(?t, ?effect)` | Target immunity (optional, blocks strategy if immune to stun) |

## Examples

### Example 1: Both allies have skills (GH7 world)

**Given:**
- companionI has iceBlastSkill (stun), companionF has fireballSkill (slow)
- `skillAppliesTag(iceBlastSkill, stun)`, `skillHasTag(fireballSkill, slow)`

**When:**
- `stunAndSlowSkill(gob)`

**Then:**
- Plan contains: `opSynchronize`, stun and fire tags applied
- Two different allies in plan

### Example 2: Only one ally available

**Given:**
- Only one ally exists

**When:**
- `stunAndSlowSkill(gob)`

**Then:**
- Planning fails (needs `\==(?a1, ?a2)`)

### Example 3: Target immune to stun

**Given:**
- `immune(gob, stun)`

**When:**
- `stunAndSlowSkill(gob)`

**Then:**
- Planning fails

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Two allies | Two different allies participate in the plan |
| P2 | Sync point | `opSynchronize` appears between prepare and use phases |
| P3 | Both effects | Both stun and fire tags applied to target |
