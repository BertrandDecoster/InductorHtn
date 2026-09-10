# The Burn

## Purpose

Area denial. A companion drags the enemy onto the oil; the player ignites it.
The explosion kills what stands in it and scorches the floor, so the oil is
gone for whatever comes next.

## Layer

strategy

## Dependencies

- `core/primitives/core_aggro`
- `core/primitives/core_attunement`

## Methods

| Method | Description |
|--------|-------------|
| `theBurn(?e)` | Bring `?e` to a region whose feature fire blasts lethally, then the player detonates fire there. |

## Examples

### Example 1: Swarm in the corridor

**Given:** oil in `corridor`, an iron `swarm` at `gallery`, warden with `magnetize`, player with one `ignite` charge and line of sight to `corridor`.

**When:** `theBurn(swarm)`

**Then:** plan contains `opLure(warden, swarm, gallery, corridor)`, `opCastRegion(player, ignite, corridor, oil, scorched)`, `opStatus(player, swarm, dead)`; final state has `regionHas(corridor, scorched)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Shields turn the burn | A `shielded` enemy is not a valid target for `theBurn`. |
| P2 | The oil is consumed | After `theBurn`, no region has `oil`. |
