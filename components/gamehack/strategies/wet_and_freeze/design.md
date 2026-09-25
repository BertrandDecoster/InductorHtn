# Wet and Freeze

## Purpose

Two companions: a lurer brings the target into water or onto ice, and a second companion chills it there. Chilled on a wet or ice location stuns the target, and defeats it if it is `vulnerableToLocationCombo` to that combo. The strategy's `if()` requires that vulnerability, so every plan ends with the target dead.

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_tags` (useSkillOnTarget and the location combos)
- `gamehack/primitives/gh_aggro` (bringEnemyTo)
- `gamehack/primitives/gh_skills` (prepareToUseSkill)

## Methods

| Method | Description |
|--------|-------------|
| `wetAndFreeze(?t)` | A lurer brings `?t` to a wet or ice location it is vulnerable on; a second companion chills it there. If `?t` already stands there, the caster alone chills it |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |
| `locationCanApplyTag(?l, wet)` or `(?l, ice)` | Where the target is brought |
| `vulnerableToLocationCombo(?t, wet or ice, chilled)` | The combo defeats it |
| `skillAppliesTag(?s, chilled)` | A cold skill |
| `companion(?lurer)`, `companion(?caster)` | Two distinct companions |

## Examples

The examples use three companions at camp: player (iceBlastSkill), frost (frostSkill: chilled), pyro (fireballSkill); gob at the hut; a wet lake, an ice rink, a kitchen with oil.

### Example 1: Lured into water and chilled

**Given:** `vulnerableToLocationCombo(gob, wet, chilled)`
**When:** `wetAndFreeze(gob)`
**Then:** two plans, one per lurer (player or pyro): the lurer walks to gob, takes its aggro, walks to the lake (gob follows); frost walks to the lake, `opUseSkill(frost, frostSkill, gob), opApplyTag(stunned, gob), opApplyTag(dead, gob)`

### Example 2: Water or ice

**Given:** gob also vulnerable to ice + chilled
**When:** `wetAndFreeze(gob)`
**Then:** four plans: the lake and the rink, two lurers each

### Example 3: Not vulnerable

**Given:** no chilled vulnerability
**When:** `wetAndFreeze(gob)`
**Then:** no plan

### Example 4: One companion is not enough

**Given:** frost alone
**When:** `wetAndFreeze(gob)`
**Then:** no plan (the lurer and the caster are distinct)

### Example 5: Already standing in water

**Given:** gob already stands in the lake
**When:** `wetAndFreeze(gob)`
**Then:** no lurer: the only plan is frost walking to the lake and chilling gob

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Defeated | The target ends stunned and dead |
