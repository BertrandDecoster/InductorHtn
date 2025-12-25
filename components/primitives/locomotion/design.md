# Locomotion

## Purpose

High-level movement primitive for HTN planning. Handles room-to-room movement at the abstraction level where locations are rooms/areas, not grid tiles.

The game engine handles low-level pathfinding (A*, tile-by-tile movement). This component only tracks which room/area an entity is in.

## Layer

primitive

## Dependencies

None (foundational component)

## Operators

| Operator | Description |
|----------|-------------|
| `opMoveTo(?entity, ?from, ?to)` | Move entity from one location to another. Deletes `at(?entity, ?from)`, adds `at(?entity, ?to)`. |

## Methods

| Method | Description |
|--------|-------------|
| `moveTo(?entity, ?destination)` | Move entity to destination. Handles direct connections and multi-hop paths. No-op if already there. |
| `canReach(?entity, ?destination)` | Query: check if entity can reach destination from current location. |
| `reachable(?from, ?to)` | Query: check if path exists between two locations. |

## Required Facts

The following facts must be provided by the level/game:

| Fact | Description |
|------|-------------|
| `at(?entity, ?location)` | Current location of an entity |
| `connected(?from, ?to)` | Direct connection between locations |
| `pathThrough(?from, ?to, ?via)` | Multi-hop path (optional, for complex layouts) |

## Parameters

No configurable parameters. Movement is instant at HTN level.

## Examples

### Example 1: Direct movement

**Given:**
- `at(player, roomA)`
- `connected(roomA, roomB)`

**When:**
- `moveTo(player, roomB)`

**Then:**
- Plan contains: `opMoveTo(player, roomA, roomB)`
- Final state has: `at(player, roomB)`
- Final state does not have: `at(player, roomA)`

### Example 2: Already at destination

**Given:**
- `at(player, roomA)`

**When:**
- `moveTo(player, roomA)`

**Then:**
- Plan contains: empty (no operators needed)
- Final state has: `at(player, roomA)`

### Example 3: Multi-hop path

**Given:**
- `at(player, roomA)`
- `connected(roomA, corridor)`
- `connected(corridor, roomB)`
- `pathThrough(roomA, roomB, corridor)`

**When:**
- `moveTo(player, roomB)`

**Then:**
- Plan contains: `opMoveTo(player, roomA, corridor)`, `opMoveTo(player, corridor, roomB)`
- Final state has: `at(player, roomB)`

### Example 4: Unreachable destination

**Given:**
- `at(player, roomA)`
- No connection to roomC

**When:**
- `moveTo(player, roomC)`

**Then:**
- Planning fails (no valid plan)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Single location | An entity can only be at one location at a time |
| P2 | Conservation | Moving doesn't create or destroy entities |
| P3 | Idempotent | Moving to current location is a no-op |
