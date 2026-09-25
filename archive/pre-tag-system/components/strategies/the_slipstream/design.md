# The Slipstream

## Purpose

The floor under an enemy reacts to cold (a wet or oily location freezes). A companion with a
skill that applies `frozen` freezes it from where it stands (the engine handles range): the
location becomes frozen, and every agent there, the enemy included, is frozen. The enemy slides
(`forceMove`) into an adjacent hazard location it is weak to, whose tag then lands on it.

## Layer

strategy

## Dependencies

- `primitives/locomotion`, `primitives/tags`

## Methods

| Method | Description |
|--------|-------------|
| `theSlipstream(?e)` | the freezer freezes the enemy's location; the enemy slides into the hazard and takes its tag |

## What makes it possible (`if()`)

- `enemy(?e)`, not `static(?e)`, `at(?e, ?l)`
- the floor reacts to cold: `locationCanApplyTag(?l, ?floor)`, `tagCombines(?floor, frozen, frozen)`
- a companion with `hasSkill(?freezer, ?s)`, `skillAppliesTag(?s, frozen)`
- a hazard location `?h` next to it: `linked(?l, ?h)` and no `blockedLink(?l, ?h, ?blocker)`
  (wall, hole or door), with `locationCanApplyTag(?h, ?tag)`, `vulnerableTo(?e, ?tag)`, not
  `immune(?e, ?tag)`, and a `?tag` that combines neither with `frozen` (the enemy arrives
  frozen) nor with a tag the enemy holds

## Examples

### Example 1: Freeze, slide, electrified

**Given:** `guard` in the wet `corridor`, weak to `electrified`; `generator` applies
`electrified`; `arcanist` holds `freezeSkill` (frozen) at `camp`
**When:** `theSlipstream(guard)`
**Then:** the only plan: the arcanist freezes the corridor from the camp (frozen is added, then
wet + frozen combine into frozen), guard gets `frozen`, `opForceMove(guard, corridor,
generator)`, `opApplyTag(electrified, guard)`

### Example 2: A dry floor doesn't freeze, no plan

### Example 3: Not weak to the hazard, no plan

### Example 4: A static enemy doesn't slide, no plan

### Example 5: A wall on the link, no plan

**Given:** `blockedLink(corridor, generator, wall)`

### Example 6: Only an adjacent hazard

**Given:** a second electrified location, `vault`, not linked to the corridor
**Then:** guard slides into the generator, never the vault

## Properties

### P1: The enemy ends in the hazard with its tag
