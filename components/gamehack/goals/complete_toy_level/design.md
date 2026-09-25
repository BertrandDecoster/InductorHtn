# Complete Toy Level

## Purpose

Top-level goal for the M0 `toy_two_step` level. Sequences two mission beats: unlock a locked door, then defeat an enemy that was behind the door. This is the smallest goal that exercises both the `gh_doors` primitive and the `defeat` goal in one plan.

Hardcodes the entities `door1` and `gob1`: this goal is level-specific by design (rubric R8 would put it in the level). Other levels define their own goals naming their own entities.

## Layer

goal

## Dependencies

- `gamehack/primitives/gh_doors` (unlockDoor)
- `gamehack/goals/defeat` (defeat)

## Methods

| Method | Description |
|--------|-------------|
| `completeToyLevel()` | Unlock door1 if locked, then defeat gob1. Empty plan if the enemy is already gone. |

## Required Facts

| Fact | Description |
|------|-------------|
| `locked(door1)` | Door1 is locked (optional: the method also handles the unlocked case) |
| `enemy(gob1)` | Gob1 is an enemy |
| (plus facts required by `unlockDoor` and `defeat`) | |

## Examples

### Example 1: Full sequence (door locked, enemy alive)

**Given:**
- `locked(door1)`, `plateOpens(plate1, door1)`, `plateOpens(plate2, door1)`
- `companion(companion1)`, `companion(companion2)` in room1, `enemy(gob1)` in room2
- a location `puddle1` (`locationCanApplyTag(puddle1, wet)`); companion1 holds frostSkill (applies `chilled`); `vulnerableToLocationCombo(gob1, wet, chilled)`

**When:**
- `completeToyLevel()`

**Then:**
- 4 plans, one per assignment of the companions to the plates; then wetAndFreeze: companion2 lures gob1 into the puddle, companion1 chills it there (`opApplyTag(stunned, gob1), opApplyTag(dead, gob1)`)
- In every plan `opUnlock(door1)` comes before any tag lands

### Example 2: Door already unlocked

**Given:**
- (Same as Example 1 but no `locked(door1)` fact)

**When:**
- `completeToyLevel()`

**Then:**
- No unlock step (not even `opDoorAlreadyUnlocked`: the goal checks the door itself); the plans start with the lure

### Example 3: Enemy already gone

**Given:**
- (No `enemy(gob1)` fact)

**When:**
- `completeToyLevel()`

**Then:**
- The empty plan (level already complete)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Ordering | `unlockDoor` always precedes `defeat` when both are needed. |
| P2 | Graceful completion | Missing preconditions on one beat skip it rather than failing the whole plan. |
