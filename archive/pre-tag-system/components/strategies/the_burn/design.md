# The Burn

## Purpose

An enemy weak to burning stands on a floor that catches fire (`tagCombines(?floor, burning,
burning)`: oil), and a companion with a skill that applies `burning` ignites the location from
where it stands (the engine handles range). The floor becomes a burning location, and every
agent standing there burns: the enemy, and the lurer if one brought it there. If the enemy
isn't on that floor yet, a second companion lures it there first.

## Layer

strategy

## Dependencies

- `primitives/locomotion`, `primitives/tags`, `primitives/aggro`

## Methods

| Method | Description |
|--------|-------------|
| `theBurn(?e)` | two cases: the enemy is already on the floor (the igniter ignites it), or a lurer brings it there first (lurer and igniter are different companions) |

## What makes it possible (`if()`)

`enemy(?e)`, `vulnerableTo(?e, burning)`, not `immune(?e, burning)`, no held tag that burning
would combine with, a location with `locationCanApplyTag(?l, ?floor)` and
`tagCombines(?floor, burning, burning)`, a companion with `hasSkill(?igniter, ?s)` and
`skillAppliesTag(?s, burning)`, and when luring is needed a second companion.

## Examples

### Example 1: Lure, then ignite

**Given:** `at(pyro, camp)`, `at(warden, camp)`, `at(gob, hut)`, oil in `storage`; `pyro` holds
`igniteSkill` (burning); `gob` is weak to burning
**When:** `theBurn(gob)`
**Then:** the only plan: warden lures gob to storage; pyro ignites it from the camp; the storage
burns (burning is added, then oily + burning combine into burning); warden and gob, both
standing there, get `burning`

### Example 2: The enemy already stands on the oil

**Given:** Example 1 with `at(gob, storage)`
**Then:** the only plan: pyro ignites the storage from the camp; only gob burns

### Example 3: No oil, no plan

### Example 4: Not weak to burning, no plan

### Example 5: Immune to burning, no plan

### Example 6: Nobody else to lure

**Given:** Example 1 without warden
**Then:** no plan (the igniter doesn't lure)

### Example 7: A tag it holds would turn burning into something else

**Given:** `hasTag(gob, frozen)` (frozen + burning = wet)
**Then:** no plan

## Properties

### P1: The enemy ends burning, on a burning location; the igniter hasn't moved
