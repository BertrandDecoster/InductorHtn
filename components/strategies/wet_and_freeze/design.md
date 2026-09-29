# Wet and Freeze

## Purpose

An enemy is wet or iced (a lurer's doing: `applyTag(?lurer, ?base, ?t)` lures it there),
then chilled (a second companion's: `applyTag(?caster, chilled, ?t)`). The wet-or-ice +
chilled combo: the target
alone is stunned, and defeated if it is vulnerable to that combo. Copied from
`Examples/Combos.htn`. It replaces the old theSlipstream (ice no longer slides).

## Layer

strategy

## Dependencies

- `primitives/locomotion`, `primitives/tags`, `primitives/aggro`, `primitives/skills`

## Methods

| Method | Description |
|--------|-------------|
| `wetAndFreeze(?t)` | two methods: `applyTag(?lurer, ?base, ?t), applyTag(?caster, chilled, ?t)`, or, when `?t` already has `?base`, `applyTag(?caster, chilled, ?t)` alone |

## What makes it possible (`if()`)

`enemy(?t)`, a `?base` with `locationCombo(?base, chilled)` and `vulnerableToLocationCombo(?t,
?base, chilled)`, and two distinct companions (a lurer and a caster) when the enemy doesn't have
`?base` yet. The location and the chilling skill are `applyTag`'s ways.

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

### Example 5: Already wet
**Given:** gob in the corridor, wet **Then:** one plan: frost walks there and chills it

## Properties

### P1: Only the target is stunned
