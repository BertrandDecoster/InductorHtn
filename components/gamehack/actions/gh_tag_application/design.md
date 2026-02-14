# GH Tag Application

## Purpose

Three-path dispatcher for applying tags that are not yet present on a target. This is the central hub that connects the tag system with the skill, movement, and aggro primitives. It determines HOW to apply a tag based on what's available in the world: ally skills, tagged locations, or non-ally mobs with skills.

## Layer

action

## Dependencies

- `gamehack/primitives/gh_movement` (goToLocation, goToSameLocation)
- `gamehack/primitives/gh_tags` (useSkillOnTarget, useLocationToApplyTag, useMobSkillToApplyTag)
- `gamehack/primitives/gh_aggro` (bringMobToLocation, bringMobsTogether)
- `gamehack/primitives/gh_skills` (prepareToUseSkill)

## Methods

| Method | Description |
|--------|-------------|
| `applyTagNotPresent(?tag, ?t)` | Apply a tag to target via one of three paths |

### Path 1: Ally Skill
Find a skill that produces the tag, prepare an ally to use it (learn if needed), then cast.

### Path 2: Location
Lure target to a location that applies the tag via aggro chain.

### Path 3: Non-ally Mob Skill
Bring target to a non-ally mob that has a matching skill.

## Required Facts

| Fact | Description |
|------|-------------|
| `skillAppliesTag(?skill, ?tag)` | Skill produces this tag effect |
| `locationCanApplyTag(?location, ?tag)` | Location applies this tag |
| `hasSkill(?entity, ?skill)` | Entity has this skill |
| `ally(?entity)` | Entity is an ally |

## Examples

### Example 1: Path 1 - Ally has skill

**Given:**
- `at(companionW, inn)`, `at(gob, hut)`
- `hasSkill(companionW, waterSkill)`, `skillAppliesTag(waterSkill, wet)`
- `ally(companionW)`

**When:**
- `applyTagNotPresent(wet, gob)`

**Then:**
- Plan contains: `opMoveTo` (companionW to gob), `opApplyTag(wet, gob)`
- Final state has: `hasTag(gob, wet)`

### Example 2: Path 1 - Ally learns skill

**Given:**
- `at(companionI, inn)`, `at(gob, hut)`
- `hasSkill(companionI, iceBlastSkill)`, `ally(companionI)`
- `skillAppliesTag(waterSkill, wet)`
- `canGetSkillAtLocation(sea, waterSkill)`

**When:**
- `applyTagNotPresent(wet, gob)`

**Then:**
- Plan contains: `opMoveTo` (to sea), `opSwapSkill`, `opMoveTo` (to gob), `opApplyTag(wet, gob)`

### Example 3: Path 2 - Location applies tag

**Given:**
- `at(gob, hut)`, `at(player, room)`
- `locationCanApplyTag(lake, wet)`, `ally(player)`

**When:**
- `applyTagNotPresent(wet, gob)`

**Then:**
- Plan contains: `opAggroMoveTo(gob, hut, lake)`
- Final state has: `at(gob, lake)`

### Example 4: Path 3 - Mob has skill

**Given:**
- `at(gob, hut)`, `at(teslaTower, lake)`
- `hasSkill(teslaTower, lightningSkill)`, `skillAppliesTag(lightningSkill, electrocute)`
- `enemy(teslaTower)`, `at(player, room)`, `ally(player)`

**When:**
- `applyTagNotPresent(electrocute, gob)`

**Then:**
- Plan contains: movement to bring gob and teslaTower together

### Example 5: No path available

**Given:**
- No skills, locations, or mobs for ice tag

**When:**
- `applyTagNotPresent(ice, gob)`

**Then:**
- Planning fails

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Tag applied | After successful plan, target has the requested tag |
