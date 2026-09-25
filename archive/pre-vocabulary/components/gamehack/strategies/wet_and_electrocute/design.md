# Wet and Electrocute

## Purpose

Sequential damage strategy: apply wet tag to target, then electrocute. The wet+electrocute combo is the most reliable damage path in GameHack, available whenever water and lightning skills/locations exist in the world.

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_tags` (applyTag)
- `gamehack/actions/gh_tag_application` (applyTagNotPresent - needed for applyTag dispatch)
- `gamehack/primitives/gh_movement` (movement for positioning)
- `gamehack/primitives/gh_aggro` (aggro for location-based paths)
- `gamehack/primitives/gh_skills` (skill preparation)

## Methods

| Method | Description |
|--------|-------------|
| `wetAndElectrocute(?t)` | Apply wet then electrocute to enemy target |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |
| Skills/locations/mobs for wet and electrocute tags | Via applyTagNotPresent paths |

## Examples

### Example 1: Both tags via ally skills

**Given:**
- GH4-style world: companionW has waterSkill, companionE has lightningSkill

**When:**
- `wetAndElectrocute(gob)`

**Then:**
- Plan succeeds, both wet and electrocute tags applied

### Example 2: Wet via location, electrocute via ally

**Given:**
- `locationCanApplyTag(lake, wet)`, companionE has lightningSkill

**When:**
- `wetAndElectrocute(gob)`

**Then:**
- Plan includes luring gob to lake, then electrocuting

### Example 3: Non-enemy fails

**Given:**
- No `enemy(player)` fact

**When:**
- `wetAndElectrocute(player)`

**Then:**
- Planning fails

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Both tags | Target has both wet and electrocute after plan |
| P2 | Sequential | Wet applied before electrocute |
