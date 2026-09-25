# door

## Purpose

A locked door opens when a companion stands on the single plate that opens it. Gates, switches
and doors are one concept: a door (`docs/authoring/vocabulary.md`). Two-plate doors, where two
companions must stand on two plates at the same moment, are `components/gamehack`'s `gh_doors`.

## Layer

challenges

## Dependencies

- `primitives/locomotion` (`goToLocation`)

## Methods

| Method | Description |
|--------|-------------|
| `unlockDoor(?d)` | already unlocked (`opDoorAlreadyUnlocked`), or any companion walks to the door's only plate and it unlocks |

## Operators

| Operator | Effect |
|----------|--------|
| `opUnlock(?d)` | removes `locked(?d)` |
| `opDoorAlreadyUnlocked(?d)` | already true (no state change) |

## Required Facts

`locked(?d)`, `plateOpens(?p, ?d)`, `at(?p, ?l)` (where the plate is), `companion(?a)`, `at(?a, ?l)`, `location(?l)`.

What a door guards is a static fact of the map: `blockedLink(?a, ?b, door(?d))` on the link it
closes (both directions). Only `locked(?d)` changes. The engine's pathfinder reads the blocked
links; `unlockDoor` doesn't need them.

## Examples

### Example 1: One companion, one plate

**Given:** `locked(door1)` on the hall-vault link (`blockedLink(hall, vault, door(door1))`),
`plateOpens(plate1, door1)`, `at(plate1, side)`, `companion(hero)`, `at(hero, hall)`
**When:** `unlockDoor(door1)`
**Then:** the only plan: `opMoveTo(hero, hall, side), opUnlock(door1)`

### Example 2: Already unlocked

**Then:** `opDoorAlreadyUnlocked(door1)`

### Example 3: Any companion can stand on the plate

**Given:** Example 1 with a second companion `scout` at `side`
**Then:** two plans: `hero` walks there, or `scout` (already there) stays

### Example 4: A two-plate door isn't opened by one companion

**Given:** Example 1 with `plateOpens(plate2, door1)`
**Then:** no plan

## Properties

### P1: After unlocking, the door is not locked
