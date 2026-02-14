# Plan to Damage

## Purpose

Top-level goal for damaging an enemy target. Selects between available strategies: `stunAndSlowSkill` (simultaneous two-ally attack) is tried first, then `wetAndElectrocute` (sequential tag application) as fallback. Strategy availability depends on world state (allies, skills, locations).

## Layer

goal

## Dependencies

- `gamehack/strategies/stun_and_slow_skill` (stunAndSlowSkill)
- `gamehack/strategies/wet_and_electrocute` (wetAndElectrocute)

## Methods

| Method | Description |
|--------|-------------|
| `planToDamage(?t)` | Select and execute best damage strategy for enemy target |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |

## Examples

### Example 1: GH7 world - both strategies available

**Given:**
- GH7 world with companionI (iceBlastSkill), companionF (fireballSkill)
- Skills for both stunAndSlowSkill and wetAndElectrocute

**When:**
- `planToDamage(gob)`

**Then:**
- Multiple plans found (both strategies produce plans)
- stunAndSlowSkill plans appear first (method order)

### Example 2: GH4 world - only wetAndElectrocute

**Given:**
- GH4 world: companionE (lightningSkill), companionW (waterSkill)
- No stun/slow skills available

**When:**
- `planToDamage(gob)`

**Then:**
- Only wetAndElectrocute plans found

### Example 3: Non-enemy fails

**Given:**
- No `enemy(player)` fact

**When:**
- `planToDamage(player)`

**Then:**
- Planning fails

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Strategy selection | Correct strategy selected based on world state |
