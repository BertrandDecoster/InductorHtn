# GH Tag Application

## Purpose

The ways to get a tag that isn't on the target yet, one method per way (`applyTagNotPresent`). A new way to get a tag is one more method here, and every strategy benefits. A lurer is chosen only when something has to move, so no two plans differ only by an idle lurer.

## Layer

action

## Dependencies

- `gamehack/primitives/gh_movement` (goToLocation, goToSameLocation)
- `gamehack/primitives/gh_tags` (useSkillOnTarget, useLocationToApplyTag, useAgentSkillToApplyTag)
- `gamehack/primitives/gh_aggro` (bringEnemyTo, bringAgentsTogether)
- `gamehack/primitives/gh_skills` (prepareToUseSkill)

## Methods

| Method | Description |
|--------|-------------|
| `applyTagNotPresent(?tag, ?t)` | Apply a tag to the target by one of three ways |

### Way 1: a companion skill
A companion prepares a skill that applies the tag (getting it from an object if needed), then uses it.

### Way 2: a location
The target already stands at a location that applies the tag, or a lurer (any companion) brings it there.

### Way 3: a non-companion skill
The target already stands with a non-companion that holds a skill applying the tag, or a lurer brings them together.

## Required Facts

| Fact | Description |
|------|-------------|
| `companion(?a)` | Companions: skill users and lurers |
| `skillAppliesTag(?s, ?tag)` | What a skill applies |
| `locationCanApplyTag(?l, ?tag)` | Standing at `?l` gives the tag |
| `hasSkill(?ag, ?s)` | Skills held |
| `location(?l)`, `at(?x, ?l)`, `enemy(?e)` | Where agents are; only enemies are lured |

## Examples

### Example 1: Way 1, a companion holds the skill

**Given:** `at(companionW, inn)`, `at(gob, hut)`, `hasSkill(companionW, waterSkill)`, `skillAppliesTag(waterSkill, wet)`
**When:** `applyTagNotPresent(wet, gob)`
**Then:** the only plan is `opMoveTo(companionW, inn, hut), opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob)`

### Example 2: Way 1, the skill comes from an object

**Given:** `at(companionI, inn)`, `hasSkill(companionI, iceBlastSkill)`, `at(seaShrine, sea)`, `canGetSkillFrom(seaShrine, waterSkill)`
**When:** `applyTagNotPresent(wet, gob)`
**Then:** the only plan goes to the sea, swaps the skill, goes to gob and uses it

### Example 3: Way 2, a lurer brings the target to the location

**Given:** `at(gob, hut)`, `at(player, room)`, `locationCanApplyTag(lake, wet)`
**When:** `applyTagNotPresent(wet, gob)`
**Then:** the only plan is `opMoveTo(player, room, hut), opAggro(gob, player), opMoveTo(player, hut, lake), opAggroMoveTo(gob, hut, lake), opApplyTag(wet, gob)`

### Example 4: Way 2, the target already stands there

**Given:** `at(gob, lake)`, two companions, `locationCanApplyTag(lake, wet)`
**When:** `applyTagNotPresent(wet, gob)`
**Then:** the only plan is `opApplyTag(wet, gob)`

### Example 5: Way 3, a lurer brings the target to the agent

**Given:** `at(gob, hut)`, `at(teslaTower, lake)`, `hasSkill(teslaTower, lightningSkill)`, `skillAppliesTag(lightningSkill, electrified)`
**When:** `applyTagNotPresent(electrified, gob)`
**Then:** the only plan lures gob to the lake, then `opUseSkill(teslaTower, lightningSkill, gob), opApplyTag(electrified, gob)`

### Example 6: Way 3, already together

**Given:** gob and teslaTower both at the lake, two companions
**When:** `applyTagNotPresent(electrified, gob)`
**Then:** the only plan is `opUseSkill(teslaTower, lightningSkill, gob), opApplyTag(electrified, gob)`

### Example 7: No way available

**Given:** no skill, location or agent applies `stunned`
**When:** `applyTagNotPresent(stunned, gob)`
**Then:** no plan

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Tag applied | After a successful plan, the target has the requested tag |
