# GH Tags

## Purpose

Tag (status effect) application system for GameHack domains. Provides the mechanics for applying tags to targets via skills, with support for multi-tag skills (one skill applying multiple effects). The `applyTag` method dispatches to `applyTagNotPresent` (defined by gh_tag_application action layer) when a tag is not yet present.

## Layer

primitive

## Dependencies

None (foundational component)

## Operators

| Operator | Description |
|----------|-------------|
| `opApplyTag(?tag, ?t)` | Add a tag to a target. `del(), add(hasTag(?t, ?tag))` |
| `opTagAlreadyOnTarget(?tag, ?t)` | No-op when tag already present |

## Methods

| Method | Description |
|--------|-------------|
| `applyTag(?tag, ?t)` | Dispatch: if tag present → no-op, else → `applyTagNotPresent` |
| `useSkillOnTarget(?a, ?s, ?t)` | Apply all tags from skill `?s` to target `?t` |
| `applySkillTags_L_ApplyTag(?s, ?t)` | `anyOf` applies each tag from `skillAppliesTag(?s, ?tag)` |
| `useLocationToApplyTag(?l, ?tag, ?t)` | Stub - game engine handles location-based tag application |
| `useMobSkillToApplyTag(?m, ?s, ?t)` | Stub - game engine handles mob skill application |

## Required Facts

| Fact | Description |
|------|-------------|
| `hasTag(?t, ?tag)` | Target currently has this tag |
| `skillAppliesTag(?skill, ?tag)` | Skill produces this tag effect |

## Examples

### Example 1: Tag already present (no-op)

**Given:**
- `hasTag(gob, wet)`

**When:**
- `applyTag(wet, gob)`

**Then:**
- Plan contains: `opTagAlreadyOnTarget(wet, gob)`
- No `opApplyTag` in plan

### Example 2: Use skill to apply single tag

**Given:**
- `skillAppliesTag(lightningSkill, electrocute)`

**When:**
- `useSkillOnTarget(companionE, lightningSkill, gob)`

**Then:**
- Plan contains: `opApplyTag(electrocute, gob)`
- Final state has: `hasTag(gob, electrocute)`

### Example 3: Use skill to apply multiple tags

**Given:**
- `skillAppliesTag(waterSkill, wet)`
- `skillAppliesTag(waterSkill, clean)`

**When:**
- `useSkillOnTarget(companionW, waterSkill, gob)`

**Then:**
- Plan contains: `opApplyTag(wet, gob)`, `opApplyTag(clean, gob)`
- Final state has: `hasTag(gob, wet)`, `hasTag(gob, clean)`

### Example 4: Skill with no tags (no-op)

**Given:**
- No `skillAppliesTag` facts for `emptySkill`

**When:**
- `useSkillOnTarget(player, emptySkill, gob)`

**Then:**
- Plan is empty (no operators)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No duplicate tags | Applying a tag already present is idempotent |
| P2 | Multi-tag complete | All tags from a multi-tag skill are applied |
