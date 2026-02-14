# GH Skills

## Purpose

Skill acquisition and preparation system for GameHack domains. Handles the `prepareToUseSkill` abstraction which transparently decides whether an ally already has a skill or needs to travel to a location to learn it first. This unifies "has skill" and "can learn skill" into a single interface for callers.

## Layer

primitive

## Dependencies

- `gamehack/primitives/gh_movement` (goToLocation, goToSameLocation)

## Operators

| Operator | Description |
|----------|-------------|
| `opSwapSkill(?a, ?old, ?new)` | Replace ally's current skill with a new one |
| `opGetSkill(?a, ?s)` | Give ally a skill (when they have none) |

## Methods

| Method | Description |
|--------|-------------|
| `prepareToUseSkill(?a, ?s, ?t)` | Prepare ally to use skill on target. If ally has skill, just move to target. Otherwise, travel to learn location, learn skill, then move to target. |
| `getSkillFromLocation(?a, ?l, ?s)` | Learn skill at location. Swaps existing skill or just learns if none. |

## Required Facts

| Fact | Description |
|------|-------------|
| `hasSkill(?entity, ?skill)` | Entity currently has this skill |
| `ally(?entity)` | Entity is an ally (can learn skills) |
| `canGetSkillAtLocation(?location, ?skill)` | Skill can be learned at this location |
| `at(?entity, ?location)` | Current location of an entity |

## Examples

### Example 1: Ally already has skill

**Given:**
- `at(companionI, inn)`, `at(gob, hut)`
- `hasSkill(companionI, iceBlastSkill)`

**When:**
- `prepareToUseSkill(companionI, iceBlastSkill, gob)`

**Then:**
- Plan contains: `opMoveTo(companionI, inn, hut)` (goes to target)
- No `opSwapSkill` or `opGetSkill` in plan

### Example 2: Ally needs to learn skill

**Given:**
- `at(companionI, inn)`, `at(gob, hut)`
- `hasSkill(companionI, iceBlastSkill)`
- `ally(companionI)`
- `canGetSkillAtLocation(sea, waterSkill)`

**When:**
- `prepareToUseSkill(companionI, waterSkill, gob)`

**Then:**
- Plan contains: `opMoveTo` (to sea), `opSwapSkill(companionI, iceBlastSkill, waterSkill)`, `opMoveTo` (to hut)
- Final state has: `hasSkill(companionI, waterSkill)`
- Final state does not have: `hasSkill(companionI, iceBlastSkill)`

### Example 3: Ally with no skill learns one

**Given:**
- `at(player, room)`, `at(gob, hut)`
- `ally(player)`
- `canGetSkillAtLocation(mountain, iceBlastSkill)`
- No `hasSkill(player, ?)` facts

**When:**
- `prepareToUseSkill(player, iceBlastSkill, gob)`

**Then:**
- Plan contains: `opGetSkill(player, iceBlastSkill)`
- Final state has: `hasSkill(player, iceBlastSkill)`

### Example 4: Non-ally cannot learn skill

**Given:**
- `at(gob, hut)`, `at(target, room)`
- `canGetSkillAtLocation(sea, waterSkill)`
- No `ally(gob)` fact

**When:**
- `prepareToUseSkill(gob, waterSkill, target)`

**Then:**
- Planning fails (gob has no skill and is not an ally)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Skill swap clean | After swap, old skill gone and new skill present |
| P2 | Non-ally blocked | Only allies can learn new skills |
