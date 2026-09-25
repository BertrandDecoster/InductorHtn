# Oil and Burn

## Purpose

A lurer brings an enemy onto oil; a second companion, holding a skill that applies `burning`,
walks to it and uses the skill. The oil + burning combo: the oil becomes a burning location,
everyone standing there burns (the lurer and the caster too), and the enemies vulnerable to
oil + burning are defeated. Copied from `Examples/Combos.htn`. It replaces the old theBurn.

## Layer

strategy

## Dependencies

- `primitives/locomotion`, `primitives/tags`, `primitives/aggro`, `primitives/skills`

## Methods

| Method | Description |
|--------|-------------|
| `oilAndBurn(?t)` | two methods: the enemy isn't on the oil (`bringEnemyTo(?lurer, ?t, ?l)`, then a second companion, the caster, prepares and uses its burning skill on `?t`), or it already stands there (the caster alone) |

## What makes it possible (`if()`)

`enemy(?t)`, an oil location (`locationCanApplyTag(?l, oil)`),
`vulnerableToLocationCombo(?t, oil, burning)`, a skill that applies `burning`, and two
distinct companions (a lurer and a caster) when the enemy isn't already on the oil.

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

### Example 6: Already on the oil
**Given:** gob in the storage **Then:** one plan: pyro walks there and sets it burning

## Properties

### P1: The enemy ends dead on a burning location; the oil is gone
