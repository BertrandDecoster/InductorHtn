# Complete Toy Level

## Purpose

Top-level goal for the M0 `toy_two_step` level. Sequences two mission beats: unlock a locked door, then defeat an enemy that was behind the door. This is the smallest goal that exercises both the `gh_doors` primitive and the existing `plan_to_damage` goal in one plan, proving end-to-end HTN sequencing.

Hardcodes the entities `door1` and `gob1` — this goal is level-specific by design. Other levels will define their own goals naming their own entities.

## Layer

goal

## Dependencies

- `gamehack/primitives/gh_doors` (unlockDoor)
- `gamehack/goals/plan_to_damage` (planToDamage)

## Methods

| Method | Description |
|--------|-------------|
| `completeToyLevel()` | Unlock door1 if locked, then damage gob1. No-op if enemy already gone. |

## Required Facts

| Fact | Description |
|------|-------------|
| `locked(door1)` | Door1 is locked (optional — method also handles unlocked case) |
| `enemy(gob1)` | Gob1 is an enemy |
| (plus facts required by `unlockDoor` and `planToDamage`) | |

## Examples

### Example 1: Full sequence (door locked, enemy alive)

**Given:**
- `locked(door1)`, `plateOpens(plate1, door1)`, `plateOpens(plate2, door1)`
- `ally(companion1)`, `ally(companion2)`, `enemy(gob1)`
- facts enabling `wetAndElectrocute(gob1)` (e.g. `locationCanApplyTag(puddle1, wet)`, `locationCanApplyTag(conduit1, electrocute)`)

**When:**
- `goals(completeToyLevel)`

**Then:**
- Plan decomposes to `unlockDoor(door1)` then `planToDamage(gob1)` → `wetAndElectrocute(gob1)` → `applyTag(wet, gob1)`, `applyTag(electrocute, gob1)`
- Final state: `locked(door1)` removed, `hasTag(gob1, wet)` and `hasTag(gob1, electrocute)` present

### Example 2: Door already unlocked

**Given:**
- (Same as Example 1 but no `locked(door1)` fact)

**When:**
- `goals(completeToyLevel)`

**Then:**
- Plan skips unlock; starts with `planToDamage(gob1)` decomposition

### Example 3: Enemy already gone

**Given:**
- (No `enemy(gob1)` fact)

**When:**
- `goals(completeToyLevel)`

**Then:**
- Plan is empty (level already complete)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Ordering | `unlockDoor` beats always precede `planToDamage` when both are needed. |
| P2 | Graceful completion | Missing preconditions on one beat skip it rather than failing the whole plan. |
