# Wet and Freeze

## Purpose

A lurer brings an enemy into water or onto ice; a second companion, holding a skill that
applies `chilled`, walks to it and uses the skill. The wet-or-ice + chilled combo: the target
alone is stunned, and defeated if it is vulnerable to that combo. Copied from
`Examples/Combos.htn`. It replaces the old theSlipstream (ice no longer slides).

## Layer

strategy

## Dependencies

- `primitives/locomotion`, `primitives/tags`, `primitives/aggro`, `primitives/skills`

## Methods

| Method | Description |
|--------|-------------|
| `wetAndFreeze(?t)` | two methods: the enemy isn't there (`bringEnemyTo(?lurer, ?t, ?l)`, then a second companion, the caster, prepares and uses its chilling skill on `?t`), or it already stands there (the caster alone) |

## What makes it possible (`if()`)

`enemy(?t)`, a location with a tag `?base` such that `vulnerableToLocationCombo(?t, ?base,
chilled)`, a skill that applies `chilled`, and two distinct companions (a lurer and a caster)
when the enemy isn't already there.

## Examples

pyro (fireballSkill) and frost (frostSkill: chilled) at the camp; gob at the hut, vulnerable to
wet + chilled; a wet corridor and an ice rink.

### Example 1: Lure into the water, then chill
**Then:** the only plan: pyro lures gob into the corridor, frost walks there and chills it; gob
is stunned and dead

### Example 2: Water or ice
**Given:** gob also vulnerable to ice + chilled **Then:** two plans, the corridor or the rink

### Example 3: Not vulnerable, no plan
### Example 4: One companion is not enough, no plan

### Example 5: Already in the water
**Given:** gob in the corridor **Then:** one plan: frost walks there and chills it

## Properties

### P1: Only the target is stunned
