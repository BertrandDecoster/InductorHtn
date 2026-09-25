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

The world of `goals/defeat`: guard1 (vulnerable to oil + burning) and guard2 (vulnerable to
wet + chilled) at the hut.

### Example 1: Two guards
**When:** `clearLocation(hut)`
**Then:** one plan: frost lures guard1 onto the oil and pyro sets it burning; then pyro lures
guard2 into the water and frost chills it

### Example 2: Nobody to clear
**When:** `clearLocation(camp)` **Then:** the empty plan

## Properties

### P1: Every enemy that was at the location ends dead
