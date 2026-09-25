# GH Skills

## Purpose

Skill preparation for GameHack domains. A companion holds a skill and stands with its target (`prepareToUseSkill`); if it lacks the skill, it first goes to an object that grants it (`canGetSkillFrom`) and learns it there (`getSkillFrom`), replacing its current skill. The object stays for the next companion.

## Layer

primitive

## Dependencies

- `gamehack/primitives/gh_movement` (goToSameLocation)

## Operators

| Operator | Description |
|----------|-------------|
| `opGetSkill(?a, ?s)` | A companion with no skill learns one |
| `opSwapSkill(?a, ?old, ?s)` | A companion replaces its skill |

## Methods

| Method | Description |
|--------|-------------|
| `prepareToUseSkill(?a, ?s, ?t)` | `?a` holds `?s` and stands with `?t`: already has it, or gets it from an object first |
| `getSkillFrom(?a, ?o, ?s)` | `?a`, standing at object `?o`, learns `?s` (swap or first skill) |

## Required Facts

| Fact | Description |
|------|-------------|
| `location(?l)`, `at(?x, ?l)` | Where agents and objects are |
| `companion(?a)` | Only companions learn skills |
| `hasSkill(?a, ?s)` | Skills held |
| `object(?o)`, `canGetSkillFrom(?o, ?s)` | Object `?o` grants skill `?s` |

## Examples

### Example 1: Companion already has the skill

**Given:** `at(companionI, inn)`, `at(gob, hut)`, `hasSkill(companionI, iceBlastSkill)`
**When:** `prepareToUseSkill(companionI, iceBlastSkill, gob)`
**Then:** the only plan is `opMoveTo(companionI, inn, hut)`

### Example 2: Companion swaps its skill at an object

**Given:** `at(companionI, inn)`, `at(gob, hut)`, `hasSkill(companionI, iceBlastSkill)`, `at(seaShrine, sea)`, `canGetSkillFrom(seaShrine, waterSkill)`
**When:** `prepareToUseSkill(companionI, waterSkill, gob)`
**Then:** the only plan is `opMoveTo(companionI, inn, sea), opSwapSkill(companionI, iceBlastSkill, waterSkill), opMoveTo(companionI, sea, hut)`

### Example 3: Companion with no skill learns one

**Given:** `at(player, room)`, `at(gob, hut)`, `at(mountainShrine, mountain)`, `canGetSkillFrom(mountainShrine, iceBlastSkill)`
**When:** `prepareToUseSkill(player, iceBlastSkill, gob)`
**Then:** the only plan is `opMoveTo(player, room, mountain), opGetSkill(player, iceBlastSkill), opMoveTo(player, mountain, hut)`

### Example 4: A non-companion can't learn

**Given:** `at(gob, hut)`, `at(target, room)`, no `companion(gob)`
**When:** `prepareToUseSkill(gob, waterSkill, target)`
**Then:** no plan

### Example 5: The object stays

**Given:** as Example 3
**When:** `prepareToUseSkill(player, iceBlastSkill, gob)`
**Then:** `canGetSkillFrom(mountainShrine, iceBlastSkill)` still holds afterwards

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Clean skill swap | After a swap, the old skill is gone and the new one is held |
| P2 | Companions only | Only companions learn new skills |
