# GH Tags

## Purpose

Tags on agents for GameHack domains. `applyTag` gets a tag onto a target (already there, or through `applyTagNotPresent`, whose ways are in the `gh_tag_application` action). A tag lands when a skill is used (`useSkillOnTarget`: every tag of the skill that the target lacks and isn't immune to), when the target stands at a location that applies it (`useLocationToApplyTag`), or when a non-companion standing with it uses its skill (`useAgentSkillToApplyTag`).

## Layer

primitive

## Dependencies

None. Requires `applyTagNotPresent/2` from `gamehack/actions/gh_tag_application`.

## Operators

| Operator | Description |
|----------|-------------|
| `opApplyTag(?tag, ?t)` | Adds `hasTag(?t, ?tag)` |
| `opUseSkill(?a, ?s, ?t)` | No state change; the engine plays the skill |
| `opTagAlreadyOnTarget(?tag, ?t)` | Already true: no state change |

## Methods

| Method | Description |
|--------|-------------|
| `applyTag(?tag, ?t)` | `?t` has the tag: already, or by any way that works (never if immune) |
| `useSkillOnTarget(?a, ?s, ?t)` | `?a`, holding `?s` and standing with `?t`, uses it; its tags land |
| `applySkillTags(?s, ?t)` | Every tag of the skill that `?t` lacks and isn't immune to lands |
| `useLocationToApplyTag(?l, ?tag, ?t)` | The location's tag lands on `?t`, who stands there |
| `useAgentSkillToApplyTag(?ag, ?s, ?t)` | A non-companion standing with `?t` uses its skill on it |

## Required Facts

| Fact | Description |
|------|-------------|
| `hasTag(?t, ?tag)` | Current tags (optional) |
| `skillAppliesTag(?s, ?tag)` | What a skill applies |
| `immune(?t, ?tag)` | Tags that never land (optional) |
| `at(?x, ?l)` | Where agents are (for the location and agent ways) |

## Examples

### Example 1: Tag already present

**Given:** `hasTag(gob, wet)`
**When:** `applyTag(wet, gob)`
**Then:** the only plan is `opTagAlreadyOnTarget(wet, gob)`

### Example 2: A skill with one tag

**Given:** `at(gob, lake)`, `at(companionE, lake)`, `hasSkill(companionE, lightningSkill)`, `skillAppliesTag(lightningSkill, electrified)`
**When:** `useSkillOnTarget(companionE, lightningSkill, gob)`
**Then:** the only plan is `opUseSkill(companionE, lightningSkill, gob), opApplyTag(electrified, gob)`

### Example 2b: The caster must hold the skill and stand with the target

**Given:** `at(gob, lake)`, `at(companionE, inn)`, `hasSkill(companionE, lightningSkill)`
**When:** `useSkillOnTarget(companionE, lightningSkill, gob)`, or the same for `companionW`, who lacks the skill
**Then:** no plan

### Example 3: A skill with two tags

**Given:** `companionW` holds `waterSkill` and stands with `gob`, `skillAppliesTag(waterSkill, wet)`, `skillAppliesTag(waterSkill, clean)`
**When:** `useSkillOnTarget(companionW, waterSkill, gob)`
**Then:** the only plan is `opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob), opApplyTag(clean, gob)`

### Example 4: A skill with no tags

**Given:** `player` holds `emptySkill` and stands with `gob`; no `skillAppliesTag` for `emptySkill`
**When:** `useSkillOnTarget(player, emptySkill, gob)`
**Then:** the only plan is `opUseSkill(player, emptySkill, gob)`

### Example 5: Immune and present tags don't land

**Given:** Example 3's skill, `immune(gob, wet)`, `hasTag(gob, clean)`
**When:** `useSkillOnTarget(companionW, waterSkill, gob)`
**Then:** the only plan is `opUseSkill(companionW, waterSkill, gob)`

### Example 6: A location applies a tag

**Given:** `at(gob, lake)`
**When:** `useLocationToApplyTag(lake, wet, gob)`
**Then:** the only plan is `opApplyTag(wet, gob)`; at `sea`, where gob isn't, no plan

### Example 7: A non-companion's skill applies a tag

**Given:** `at(gob, lake)`, `at(teslaTower, lake)`, `skillAppliesTag(lightningSkill, electrified)`
**When:** `useAgentSkillToApplyTag(teslaTower, lightningSkill, gob)`
**Then:** the only plan is `opUseSkill(teslaTower, lightningSkill, gob), opApplyTag(electrified, gob)`

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No duplicate tags | Applying a tag already present is idempotent |
| P2 | Multi-tag complete | Every tag of a multi-tag skill lands |
