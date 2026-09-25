# Aggro

## Purpose

An enemy with `hasAggro(?e, ?a)` is after `?a` and follows it (locomotion's
`enemiesFollow`). A lurer takes an enemy's aggro and walks it somewhere. The caller chooses the
lurer: any companion, bound in the caller's `if()`.

## Layer

primitive

## Dependencies

- `primitives/locomotion`

## Methods

| Method | Description |
|--------|-------------|
| `getAggro(?e, ?a)` | `?e` is after `?a`: already (`opTargetAlreadyAggroed`), switched from another target, or for the first time |
| `bringEnemyTo(?lurer, ?e, ?l)` | the lurer walks to `?e`, takes its aggro and walks to `?l`; `?e` follows. `opEnemyAlreadyAtLocation` if it is there |

## Operators

| Operator | Effect |
|----------|--------|
| `opAggro(?e, ?a)` | adds `hasAggro(?e, ?a)` |
| `opRemoveAggro(?e, ?a)` | removes it |
| `opTargetAlreadyAggroed`, `opEnemyAlreadyAtLocation` | already true (no state change) |

## Required Facts

`enemy(?e)`, `location(?l)`, `at(?x, ?l)`, optionally `hasAggro(?e, ?a)`, `static(?x)`.

## Examples

### Example 1: First aggro

**When:** `getAggro(orc, hero)` with no aggro
**Then:** `opAggro(orc, hero)`

### Example 2: Already after that target

**Given:** `hasAggro(orc, hero)`
**Then:** `getAggro(orc, hero)` is `opTargetAlreadyAggroed(orc, hero)`

### Example 3: Switching target

**Given:** `hasAggro(orc, other)`
**Then:** `getAggro(orc, hero)` is `opRemoveAggro(orc, other), opAggro(orc, hero)`

### Example 4: Lure an enemy to a location

**Given:** `at(hero, a)`, `at(orc, b)`
**When:** `bringEnemyTo(hero, orc, c)`
**Then:** `opMoveTo(hero, a, b), opAggro(orc, hero), opMoveTo(hero, b, c), opAggroMoveTo(orc, b, c)`

### Example 5: Already there, or can't move

**Then:** `bringEnemyTo(hero, orc, b)` is `opEnemyAlreadyAtLocation(orc, b)`; a static enemy
elsewhere has no plan.

## Properties

### P1: The lured enemy ends at the destination, with the lurer

### P2: One target at a time

After `getAggro(orc, hero)`, `orc` has aggro on `hero` only.
