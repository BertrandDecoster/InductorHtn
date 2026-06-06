# clear_area

## Purpose

Pressure-class challenge: agent must navigate to and eliminate every blocker
(enemy, obstacle, hazard) in a designated zone. All blockers must be cleared
for the challenge to succeed.

Models wave-clear, room-cleanup, and obstacle-removal scenarios. The
`allOf` modifier ensures the agent handles every blocker without the level
designer needing to enumerate them explicitly.

## Layer

challenges

## Dependencies

- `challenges/nav_obstacle` -- provides `navigateTo` and `opMoveTo`

## Operators

| Operator | Description |
|----------|-------------|
| `opEliminate(?entity, ?zone)` | Remove a blocker from its zone. Deletes `blocker(?entity, ?zone)`, adds `cleared(?entity)`. |

## Methods

| Method | Description |
|--------|-------------|
| `removeBlocker(?entity)` | Navigate to the zone entry, then eliminate the specified blocker. |
| `clearZone(?zone)` | Eliminate all blockers in the zone using `allOf`. Succeeds only when every blocker has been cleared. |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(agent, ?location)` | Current agent location |
| `blocker(?entity, ?zone)` | Entity is a blocker in the specified zone |
| `zoneEntry(?zone, ?entryLocation)` | Location agent navigates to in order to interact with blockers in the zone |
| `connected(?from, ?to)` | Traversable link (from nav_obstacle) |
| `blocked(?location)` | Impassable location (from nav_obstacle) |

## Examples

### Example 1: Clear a zone with one blocker

**Given:**
- `at(agent, start)`
- `blocker(enemy1, zone1)`
- `zoneEntry(zone1, zoneEntrance)`
- `connected(start, zoneEntrance)`

**When:**
- `clearZone(zone1)`

**Then:**
- Plan contains: `opEliminate(enemy1, zone1)`
- Final state has: `cleared(enemy1)`
- Final state does not have: `blocker(enemy1, zone1)`

### Example 2: Clear a zone with multiple blockers

**Given:**
- `at(agent, start)`
- `blocker(enemy1, zone1)`, `blocker(enemy2, zone1)`, `blocker(enemy3, zone1)`
- `zoneEntry(zone1, zoneEntrance)`
- `connected(start, zoneEntrance)`

**When:**
- `clearZone(zone1)`

**Then:**
- Plan eliminates all three enemies
- Final state has: `cleared(enemy1)`, `cleared(enemy2)`, `cleared(enemy3)`
- No `blocker` facts remain for zone1

### Example 3: Already empty zone succeeds with empty plan

**Given:**
- `at(agent, start)`
- (no `blocker` facts for zone1)

**When:**
- `clearZone(zone1)`

**Then:**
- Planning succeeds with empty plan (allOf with no bindings is vacuously true)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | All blockers cleared | After plan, no `blocker(?, zone)` facts remain for the cleared zone |
| P2 | Cleared markers added | After plan, every blocker has a corresponding `cleared(entity)` fact |
| P3 | Plan length scales with blockers | Number of `opEliminate` calls equals number of blockers |
