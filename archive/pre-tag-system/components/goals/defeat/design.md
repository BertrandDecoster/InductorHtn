# Defeat

## Purpose

Goal: an enemy is out of the fight (`hasTag(?t, dead)`). A menu of strategies: every strategy
that works gives its own plan. Each strategy's `if()` requires a weakness the enemy has
(`vulnerableTo`), so the tag it lands is what takes the enemy out.

## Layer

goal

## Dependencies

- `primitives/locomotion`, `primitives/tags`, `primitives/aggro`
- `strategies/the_burn`, `strategies/the_slipstream`

## Methods

| Method | Description |
|--------|-------------|
| `defeat(?t)` | if it already holds a tag it is weak to (an area effect reached it), `opApplyTag(dead, ?t)`; otherwise `theBurn(?t)` or `theSlipstream(?t)`, then `opApplyTag(dead, ?t)`. No plan for an enemy already dead |

## Examples

The world: `pyro` (igniteSkill: burning), `arcanist` (freezeSkill: frozen) and `warden` at
`camp`; oil in `storage`, a wet `corridor`, an electrified `generator`; `linked` camp-storage,
camp-corridor, corridor-generator. Skills reach any location (the engine handles range).

### Example 1: Weak to burning, standing on oil

**Given:** `guard1` in `storage`, weak to burning
**Then:** one plan: theBurn (pyro ignites the storage from the camp)

### Example 2: Weak to electrified, on a wet floor

**Given:** `guard2` in the `corridor`, weak to electrified
**Then:** one plan: theSlipstream (the arcanist freezes the corridor, guard2 slides into the generator)

### Example 3: Weak to both: the menu

**Given:** `ogre` in the `corridor`, weak to burning and electrified
**Then:** three plans: theBurn with the arcanist or the warden as lurer (the lurer stands on the
oil with the ogre and burns too), and theSlipstream

### Example 4: Already dead

**Given:** `hasTag(guard1, dead)`
**Then:** no plan

### Example 5: No weakness, no plan

### Example 6: It already holds its weakness

**Given:** `hasTag(guard1, burning)`
**Then:** one plan: `opApplyTag(dead, guard1)`

## Properties

### P1: Every plan ends with the enemy dead
