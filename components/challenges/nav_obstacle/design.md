# nav_obstacle

## Purpose

Navigate an agent from their current location to a destination while avoiding
blocked locations. Provides insight-class challenge: the player must identify
which path is unblocked and route accordingly.

Blocked locations model hazards (traps, enemies, fire) that make a location
impassable at the HTN abstraction level. Low-level movement is handled by
the game engine.

## Layer

challenges

## Dependencies

None (self-contained navigation primitive)

## Operators

| Operator | Description |
|----------|-------------|
| `opMoveTo(?agent, ?from, ?to)` | Move agent from one location to another. Deletes `at(?agent, ?from)`, adds `at(?agent, ?to)`. |

## Methods

| Method | Description |
|--------|-------------|
| `navigateTo(?agent, ?dest)` | Navigate agent to destination avoiding blocked locations. Handles already-there, direct, and single-intermediate-hop paths. |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(?agent, ?location)` | Current location of the agent |
| `connected(?from, ?to)` | Direct traversable link between locations |
| `blocked(?location)` | Location is impassable (hazard present) |

## Parameters

No configurable parameters. Challenge difficulty is set by the ratio of
blocked locations to total path options.

## Examples

### Example 1: Direct unblocked path

**Given:**
- `at(agent, locA)`
- `connected(locA, locB)`

**When:**
- `navigateTo(agent, locB)`

**Then:**
- Plan contains: `opMoveTo(agent, locA, locB)`
- Final state has: `at(agent, locB)`
- Final state does not have: `at(agent, locA)`

### Example 2: Direct path blocked, detour available

**Given:**
- `at(agent, locA)`
- `connected(locA, locB)`, `blocked(locB)`
- `connected(locA, locC)`, `connected(locC, locB)` (locC is safe)

**When:**
- `navigateTo(agent, locB)`

**Then:**
- Plan contains: `opMoveTo(agent, locA, locC)`, `opMoveTo(agent, locC, locB)`
- Plan does NOT take the direct A→B route (locB was blocked — but it is unblocked via locC)

### Example 3: All paths blocked — no plan

**Given:**
- `at(agent, locA)`
- `connected(locA, locB)`, `blocked(locB)`

**When:**
- `navigateTo(agent, locB)`

**Then:**
- Planning fails (no valid unblocked route)

### Example 4: Already at destination — no-op

**Given:**
- `at(agent, locA)`

**When:**
- `navigateTo(agent, locA)`

**Then:**
- Plan is empty (no operators needed)
- State unchanged

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Destination reached | After successful plan, agent is at `?dest` |
| P2 | No blocked visits | No operator in the plan moves agent into a `blocked` location |
| P3 | Single location | Agent is at exactly one location at any time |
| P4 | Idempotent when at destination | navigateTo when already there produces no operators |
