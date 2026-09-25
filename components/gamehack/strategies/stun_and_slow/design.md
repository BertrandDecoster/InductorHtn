# Stun and Slow

## Purpose

Two companions: one stuns the target while the other's slow skill lands at the same moment. Each prepares independently (getting its skill from an object if needed), they synchronize, then both use their skills. The skills are chosen by property: one applies `stunned`, the other has `slow` (two different skills).

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

Same world as wet_and_freeze: player (iceBlastSkill: stunned), frost (frostSkill: chilled), pyro (fireballSkill: burning, slow) at camp; gob at the hut.

### Example 1: Both companions have their skills

**Given:** the world above
**When:** `stunAndSlow(gob)`
**Then:** the only plan is `opMoveTo(player, camp, hut), opMoveTo(pyro, camp, hut), opSynchronize(player, pyro), opUseSkill(player, iceBlastSkill, gob), opApplyTag(stunned, gob), opUseSkill(pyro, fireballSkill, gob), opApplyTag(burning, gob)`

### Example 2: Only one companion

**Given:** the player alone
**When:** `stunAndSlow(gob)`
**Then:** no plan (`\==(?a1, ?a2)`)

### Example 3: Target immune to stunned

**Given:** `immune(gob, stunned)`
**When:** `stunAndSlow(gob)`
**Then:** no plan

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Two companions | Two different companions take part, synchronized before either skill is used |
| P2 | Both effects | The target ends stunned and burning; the `defeat` goal adds `dead` |
