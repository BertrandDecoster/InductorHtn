# Clear Location

## Purpose

Goal: every enemy at a location is out of the fight. Each living enemy there is defeated
(`defeat`), in the order the level lists them (`allOf`: one plan that does all of them).

## Layer

goal

## Dependencies

- `goals/defeat` (and its strategies and primitives)

## Methods

| Method | Description |
|--------|-------------|
| `clearLocation(?l)` | `defeat(?e)` for every enemy at `?l` that isn't dead; nothing to do if there is none |

## Examples

The world of `goals/defeat`, plus `imp` in `storage`, weak to burning.

### Example 1: One fire takes out both

**Given:** `guard1` and `imp` in the oily `storage`, both weak to burning
**When:** `clearLocation(storage)`
**Then:** one plan: pyro ignites the storage from the camp; the storage burns and everyone
standing there burns; `guard1` is defeated by theBurn and `imp` because it already holds its
weakness

### Example 2: Nobody to clear

**When:** `clearLocation(camp)` **Then:** the empty plan

### Example 3: The order matters

**Given:** `guard2` and `ogre` in the wet `corridor`
**When:** `clearLocation(corridor)`
**Then:** no plan: freezing the corridor for `guard2` also freezes `ogre`, and a frozen `ogre`
can neither burn nor slide on the frozen floor. (Taking `ogre` first would work; `allOf`
keeps the level's order.)

## Properties

### P1: Every enemy that was at the location ends dead
