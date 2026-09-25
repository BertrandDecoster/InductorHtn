# Defeat

## Purpose

Goal: take an enemy out of the fight. A menu of strategies, one plain method each, so `FindAllPlans` returns one plan per strategy (and per binding) that works: `stunAndSlow`, `wetAndElectrify`, `stunAndBurn`. Each plan ends with `opApplyTag(dead, ?t)`. An enemy that already has `dead` has no plan.

## Layer

goal

## Dependencies

- `gamehack/strategies/stun_and_slow` (stunAndSlow)
- `gamehack/strategies/wet_and_electrify` (wetAndElectrify)
- `gamehack/strategies/stun_and_burn` (stunAndBurn)

## Methods

| Method | Description |
|--------|-------------|
| `defeat(?t)` | Enemy `?t`, not yet dead, is taken out by one of the strategies |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |
| `hasTag(?t, dead)` | Already out of the fight (optional) |

## Examples

### Example 1: GH7 world

**Given:** companionI (iceBlastSkill), companionF (fireballSkill, slow), the player with no skill, shrines that grant waterSkill and iceBlastSkill, a lake that applies `wet`; nothing electrifies
**When:** `defeat(gob)`
**Then:** stunAndSlow and stunAndBurn plans; no wetAndElectrify plan

### Example 2: GH4 world

**Given:** companionE (lightningSkill), companionW (waterSkill), no stun or slow skill
**When:** `defeat(gob)`
**Then:** only wetAndElectrify plans

### Example 3: Non-enemy fails

**Given:** no `enemy(player)`
**When:** `defeat(player)`
**Then:** no plan

### Example 4: Already dead

**Given:** `hasTag(gob, dead)`
**When:** `defeat(gob)`
**Then:** no plan

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Ends dead | Every plan ends with `opApplyTag(dead, ?t)` |
| P2 | No duplicates | No two plans are the same |
