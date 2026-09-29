# Wet and Freeze

## Purpose

Two companions: the target is wet or iced (a lurer's doing: `applyTag(?lurer, ?base, ?t)` lures it there), then chilled (a second companion's: `applyTag(?caster, chilled, ?t)`). Chilled on a wet or ice location stuns the target, and defeats it if it is `vulnerableToLocationCombo` to that combo. The strategy's `if()` requires that vulnerability, so every plan ends with the target dead.

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_tags` (useSkillOnTarget and the location combos)
- `gamehack/primitives/gh_aggro` (bringEnemyTo)
- `gamehack/primitives/gh_skills` (applyTag)

## Methods

| Method | Description |
|--------|-------------|
| `wetAndFreeze(?t)` | `applyTag(?lurer, ?base, ?t), applyTag(?caster, chilled, ?t)` for a wet or ice `?base` it is vulnerable to; if `?t` already has `?base`, `applyTag(?caster, chilled, ?t)` alone |

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

### Example 5: Already wet

**Given:** gob starts in the lake, so it is wet
**When:** `wetAndFreeze(gob)`
**Then:** no lurer: the only plan is frost walking to the lake and chilling gob

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Defeated | The target ends stunned and dead |
