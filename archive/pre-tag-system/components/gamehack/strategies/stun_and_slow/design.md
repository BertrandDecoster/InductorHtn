# Stun and Slow

## Purpose

Two companions: one stuns the target while the other's slow skill lands at the same moment. Each prepares independently (getting its skill from an object if needed), they synchronize, then both use their skills. The skills are chosen by property: one applies `stunned`, the other has `slow`.

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_tags` (useSkillOnTarget)
- `gamehack/primitives/gh_skills` (prepareToUseSkill)
- `gamehack/primitives/gh_movement` (movement for positioning)

## Operators

| Operator | Description |
|----------|-------------|
| `opSynchronize(?a1, ?a2)` | No state change; tells the engine two companions act together |

## Methods

| Method | Description |
|--------|-------------|
| `stunAndSlow(?t)` | Stunned and, at the same moment, hit by a second companion's slow skill |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |
| `skillAppliesTag(?s, stunned)` | A skill that stuns |
| `skillHasTag(?s, slow)` | A skill that is slow (a property of the skill itself) |
| `companion(?a1)`, `companion(?a2)` | Two distinct companions |
| `immune(?t, stunned)` | Rules the strategy out (optional) |

## Examples

### Example 1: Both companions have their skills (GH7 world)

**Given:** companionI holds iceBlastSkill (applies `stunned`), companionF holds fireballSkill (applies `burning`, is `slow`), both at the inn; gob at the hut; the player holds no skill
**When:** `stunAndSlow(gob)`
**Then:** the only plan is `opMoveTo(companionI, inn, hut), opMoveTo(companionF, inn, hut), opSynchronize(companionI, companionF), opUseSkill(companionI, iceBlastSkill, gob), opApplyTag(stunned, gob), opUseSkill(companionF, fireballSkill, gob), opApplyTag(burning, gob)`

### Example 2: Only one companion

**Given:** only companionI exists
**When:** `stunAndSlow(gob)`
**Then:** no plan (`\==(?a1, ?a2)`)

### Example 3: Target immune to stunned

**Given:** `immune(gob, stunned)`
**When:** `stunAndSlow(gob)`
**Then:** no plan

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Two companions | Two different companions take part |
| P2 | Sync point | `opSynchronize` comes after both prepare and before either skill is used |
| P3 | Both effects | Both skills' tags land on the target |
