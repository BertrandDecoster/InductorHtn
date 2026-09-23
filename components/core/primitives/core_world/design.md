# Core World

## Purpose

The unified vocabulary for regions, movement and roles. The HTN reasons over
a small navigation graph of named regions (never tiles); the engine handles
pathing inside a region. Everything above this layer reads `at/2`,
`regionHas/2`, `status/2` and `role/2` and never invents its own.

## Layer

primitive

## Dependencies

None (foundational component)

## Operators

| Operator | Description |
|----------|-------------|
| `opNavigate(?a, ?from, ?to)` | Actor `?a` moves one edge. RL-delegated. |

## Methods

| Method | Description |
|--------|-------------|
| `navigate(?a, ?to)` | No-op if there; else one hop; else two hops via the first region that works. Fails when `?a` is anchored or snared. |
| `takeVantage(?a, ?r)` | Stay if `?r` can be targeted from here, else move to the first region with line of sight to `?r`. |

## Rules

| Rule | Description |
|------|-------------|
| `canAct(?a)` | `?a` is the player or a companion. |
| `canTarget(?from, ?to)` | Same region, or a declared `lineOfSight(?from, ?to)`. |
| `canMove(?a)` | Not anchored, not snared. |

## Required Facts

| Fact | Description |
|------|-------------|
| `region(?r)` | A region of the graph |
| `connected(?a, ?b)` | Traversable edge, declared per direction |
| `lineOfSight(?from, ?to)` | Ranged reach between regions |
| `at(?e, ?r)` | Where an entity is |
| `status(?e, ?s)` | `anchored`, `snared`, ... |
| `role(?e, ?kind)` | `player`, `companion`, `enemy`. `player` and `companion` are both companions and differ only by who controls them; no rule may gate an ability on `role(?a, player)`. |

## Examples

### Example 1: One hop

**Given:** `at(player, a)`, `connected(a, b)`, `role(player, player)`

**When:** `navigate(player, b)`

**Then:** plan contains `opNavigate(player, a, b)`; final state has `at(player, b)`.

### Example 2: Two hops

**Given:** `at(player, a)`, `connected(a, b)`, `connected(b, c)`

**When:** `navigate(player, c)`

**Then:** plan contains `opNavigate(player, a, b)` then `opNavigate(player, b, c)`.

### Example 3: Already there

**Given:** `at(player, a)`

**When:** `navigate(player, a)`

**Then:** a plan exists with no operators.

### Example 4: Take a vantage

**Given:** `at(player, a)`, `connected(a, b)`, `lineOfSight(b, c)`, `region(b)`

**When:** `takeVantage(player, c)`

**Then:** plan contains `opNavigate(player, a, b)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Anchored agents hold | An agent with `status(?a, anchored)` has no `navigate` plan to another region. |
| P2 | Snared agents are stuck | An agent with `status(?a, snared)` has no `navigate` plan to another region. |
