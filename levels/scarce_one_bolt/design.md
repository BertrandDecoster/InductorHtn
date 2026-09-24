# One Bolt

## Purpose

A resource-scarcity level: **a mana budget**. A flooded chapel. In the hall stands a sentry drone,
by an open shaft; past it, in the flooded nave, squats the pump engine - a heavy machine, soaked.
Both must go. Everyone has 2 mana and a lightning flash costs 2: whoever holds it gets **one bolt**,
and a bolt strikes everyone in one area.

The engine is wet, so the bolt kills it. The drone is dry, so a bolt only stuns it. The one bolt has
to meet the drone soaked in the engine's area - or the drone has to go some other way first.

| Method | Skills | How |
|--------|--------|-----|
| **The flood** | `hook` or `taunt`, + `lightningFlash` | from the nave, hook the drone in, or taunt it (it wades in after the taunter); it arrives soaked, and one bolt on the nave takes both machines |
| **The drop** | `fireball`, `shieldBash`, `tidalWave`, `vortex` or `hook`, + `lightningFlash` | knock the drone into the shaft (a fireball or a bash from the porch, a wave in the hall, a vortex on the shaft - or the gap under the balcony), or hook it off the hall from the gallery across the gap; then the bolt on the engine |

Why no single skill works:
- Only a bolt stops the engine: it is heavy (nothing knocks it) and nothing else in the pool lands a
  tag it cares about.
- A bolt on the dry drone only stuns it; two bolts (both companions holding the flash) spend one on
  the drone and still leave it standing.
- Nothing else moves or knocks the engine; the knockers and movers only deal with the drone.

The scarce thing is the bolt: the flash is a mandatory pick, and the partner decides the method.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
porch (player, mage) --- hall (drone; the shaft) --- nave (engine; flooded)
  |                       ~gap~
gallery -----------------'           (a balcony over the hall)
```

- **Areas and links:** four areas. The porch is walkable to the hall and to the gallery; the hall is
  walkable to the nave; the gallery overlooks the hall across a gap (the chokepoint).
- **Features:** the shaft (`chasm`) inside the hall. The nave is a `puddle` zone.
- **Line of sight:** the porch and the gallery see the hall; the hall and the nave see each other.
- **Drone:** `machine`. **Engine:** `machine`, `heavy`, `wet`.
- Both companions have 2 mana.

The goal `win` has two stages: bring the drone into the nave (`bringTo`), then take the engine
(and the drone with it); or each machine on its own (`neutralize`).

## Hypothesis

Measured by `htn_components combos scarce_one_bolt` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 12 of the 49 assignments win: `lightningFlash` with each of the six others, either way round, by 6
  methods; no solo plans; no dead skills.
- Every winning plan casts exactly one bolt.
- `hook` plays two roles: it drags the drone into the flood (from the nave) or drops it into the
  gap (from the gallery).
- A wave in the hall soaks the drone where it stands - wet but in the wrong area - so with a wave the
  drone only ever falls.

## Examples

### Example 1: Into the flood

**Given:** the player knows `hook`, the mage knows `lightningFlash` (the default kit).

**When:** `win`

**Then:** the player wades into the nave and hooks the drone in from the hall; it arrives soaked. The
mage flashes the nave from the hall: both machines short-circuit (`dead`).

### Example 2: Lured into the flood

**Given:** the player knows `taunt`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player taunts the drone from the nave; it wades in after the player, soaked. One bolt.

### Example 3: The shaft

**Given:** the player knows `fireball`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the fireball knocks the drone into the shaft (`fell`); the mage's bolt on the nave takes the
engine alone.

### Example 4: Off the balcony

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player walks to the gallery and hooks the drone across the gap: it falls in. The bolt
takes the engine.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Six pairs win | Exactly `lightningFlash` with each other skill. |
| P3 | One bolt | Every winning plan casts exactly one `lightningFlash`. |
| P4 | A bolt on the dry drone is wasted | Jolting it first loses; two bolts still lose. |
| P5 | Soaked in the wrong area | With a wave, the drone only ever falls. |
| P6 | Each hand matters | The pairs win whichever companion holds which half. |
