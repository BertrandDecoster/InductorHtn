# Locomotion

## Purpose

Agents move between locations in one step: the game engine finds the path. Enemies that have
aggro on an agent follow it. An agent can be pushed into a location (`forceMove`).

## Layer

primitive

## Dependencies

None.

## Methods

| Method | Description |
|--------|-------------|
| `goToLocation(?a, ?l)` | `?a` is at `?l`; enemies after `?a` follow. `opStayInLocation` if already there. |
| `goToSameLocation(?a, ?t)` | `?a` stands where `?t` is. |
| `enemiesFollow(?a, ?from, ?to)` | The non-static enemies after `?a` at `?from` move to `?to`. |
| `forceMove(?x, ?l)` | A non-static `?x` is pushed into `?l`. |

## Operators

| Operator | Effect |
|----------|--------|
| `opMoveTo(?who, ?from, ?to)` | an agent walks |
| `opAggroMoveTo(?e, ?from, ?to)` | an enemy follows its target |
| `opForceMove(?x, ?from, ?to)` | an agent is pushed |
| `opStayInLocation(?a)` | already there (no state change) |

## Required Facts

`location(?l)`, `at(?x, ?l)`, and optionally `hasAggro(?e, ?a)`, `static(?x)`.

## Examples

### Example 1: One step, wherever the location is

**Given:** `location(a)`, `location(d)`, `at(hero, a)`
**When:** `goToLocation(hero, d)`
**Then:** the only plan is `opMoveTo(hero, a, d)`

### Example 2: Already there

**Given:** `at(hero, a)`
**When:** `goToLocation(hero, a)`
**Then:** the only plan is `opStayInLocation(hero)`

### Example 3: An enemy after the agent follows it

**Given:** `at(hero, a)`, `at(orc, a)`, `hasAggro(orc, hero)`
**When:** `goToLocation(hero, d)`
**Then:** `opMoveTo(hero, a, d), opAggroMoveTo(orc, a, d)`

### Example 4: A static enemy doesn't follow

**Given:** Example 3 with `static(orc)`
**When:** `goToLocation(hero, d)`
**Then:** `opMoveTo(hero, a, d)`

### Example 5: Stand with another agent

**Given:** `at(hero, a)`, `at(orc, d)`
**When:** `goToSameLocation(hero, orc)`
**Then:** `opMoveTo(hero, a, d)`

### Example 6: Pushed into a location

**Given:** `at(orc, a)`
**When:** `forceMove(orc, d)`
**Then:** `opForceMove(orc, a, d)`; a static agent can't be pushed

## Properties

### P1: One position

After any move, the agent is at exactly one location.

### P2: Unknown locations are refused

`goToLocation` to something that isn't a `location` has no plan.
