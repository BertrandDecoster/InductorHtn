# Oil and Burn

## Purpose

An enemy has oil (a lurer's doing: `applyTag(?lurer, oil, ?t)` lures it onto an oil
location), then is burning (a second companion's: `applyTag(?caster, burning, ?t)`). The
oil + burning combo: the oil becomes a burning location,
everyone standing there burns (the lurer and the caster too), and the enemies vulnerable to
oil + burning are defeated. Copied from `Examples/Combos.htn`. It replaces the old theBurn.

## Layer

strategy

## Dependencies

- `primitives/locomotion`, `primitives/tags`, `primitives/aggro`, `primitives/skills`

## Methods

| Method | Description |
|--------|-------------|
| `oilAndBurn(?t)` | two methods: `applyTag(?lurer, oil, ?t), applyTag(?caster, burning, ?t)`, or, when `?t` already has oil, `applyTag(?caster, burning, ?t)` alone |

## What makes it possible (`if()`)

`enemy(?t)`, `vulnerableToLocationCombo(?t, oil, burning)`, and two distinct companions (a
lurer and a caster) when the enemy has no oil yet. The oil location and the burning skill are
`applyTag`'s ways.

## Examples

pyro (fireballSkill: burning) and frost (frostSkill: chilled) at the camp; gob at the hut,
vulnerable to oil + burning; oil in the storage.

### Example 1: Lure, then burn
**Then:** the only plan: frost lures gob to the storage, pyro walks there and uses
fireballSkill; the oil becomes burning; pyro, frost and gob burn; gob is dead

### Example 2: Not vulnerable, no plan
### Example 3: One companion is not enough, no plan
### Example 4: No oil, no plan
### Example 5: Every vulnerable enemy on the oil is defeated
**Given:** imp, also vulnerable, already in the storage **Then:** both are dead

### Example 6: Already has oil
**Given:** gob in the storage, with oil **Then:** one plan: pyro walks there and sets it burning

## Properties

### P1: The enemy ends dead on a burning location; the oil is gone
