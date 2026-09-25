# Wet and Electrify

## Purpose

Sequential strategy: the target gets wet, then electrified. Each state comes from `applyTag`, so any way that applies the tag works (a companion skill, a location, a non-companion skill).

## Layer

strategy

## Dependencies

- `gamehack/primitives/gh_tags` (applyTag)
- `gamehack/actions/gh_tag_application` (applyTagNotPresent, needed by applyTag)
- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_aggro`
- `gamehack/primitives/gh_skills`

## Methods

| Method | Description |
|--------|-------------|
| `wetAndElectrify(?t)` | Wet, then electrified; ruled out if the target is immune to either |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |
| Skills, locations or agents for `wet` and `electrified` | Through the ways of applyTagNotPresent |

## Examples

### Example 1: Both tags from companion skills

**Given:** companionW (waterSkill) at the inn, companionE (lightningSkill) at the hut with gob
**When:** `wetAndElectrify(gob)`
**Then:** the only plan is `opMoveTo(companionW, inn, hut), opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob), opStayInLocation(companionE), opUseSkill(companionE, lightningSkill, gob), opApplyTag(electrified, gob)`

### Example 2: Wet from a location, electrified from a companion

**Given:** `locationCanApplyTag(lake, wet)`; the player (no skill) and companionE (lightningSkill) can lure
**When:** `wetAndElectrify(gob)`
**Then:** two plans, one per lurer; each lures gob to the lake, then companionE electrifies it there

### Example 3: Non-enemy fails

**Given:** no `enemy(player)`
**When:** `wetAndElectrify(player)`
**Then:** no plan

### Example 4: Immune target

**Given:** Example 1's world and `immune(gob, electrified)`
**When:** `wetAndElectrify(gob)`
**Then:** no plan

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Both tags | Target has both wet and electrified after the plan |
| P2 | Sequential | Wet lands before electrified |
