# One Bolt

## Purpose

A **resource scarcity** level: a mana budget buys exactly one jolt, and two machines have to die by
it. A sentry drone stands in the hall of a flooded chapel; behind it, in the flooded nave, a heavy
pump engine that is already soaked. The player and the mage pick one skill each from eight. Both have
2 mana, and both jolts in the pool (`lightningFlash`, `chainLightning`) cost 2. Whoever holds the jolt
gets one cast.

The engine is wet, so any jolt kills it. The drone is dry, and a jolt only stuns it. So the one bolt
has to meet a *wet* drone as well, or the drone has to go some other way first.

| Method | First (the partner) | Then (the one bolt) |
|--------|---------------------|---------------------|
| **Line up**: the flash runs through the hall to the nave | soak the drone where it stands: `rainCall`, `frostBolt` | `lightningFlash` from the porch at the engine: the drone is on its path |
| **The flood**: both machines in one region | push the drone into the nave from the porch (`gust`, `tidalWave`) or drag it in from the nave (`taunt`, `magnetize`): it arrives soaked | `chainLightning` over the nave |
| **The pit**: the drone goes another way | push it into the pit from the gallery: `gust`, `tidalWave` | either jolt at the engine |

Why no single skill works:
- A jolt alone kills the engine and only stuns the dry drone. Both companions holding it doesn't help.
  Each flash or chain takes one region or one line, and the drone is still dry.
- A soaker or a mover alone kills nothing: only a jolt or the pit stops a machine, and the heavy
  engine cannot be moved into the pit.

The order is the puzzle. Soak the drone, jolt it, then turn to the engine: that is the obvious
order, and it never works, because the bolt spent on the drone cannot reach the engine. The
drone has to be wet (or gone) before the only bolt is cast. Some skills play two roles:
- `tidalWave` soaks and pushes. From the porch it washes the drone into the flood. From the
  gallery it washes it into the pit.
- `gust` is a push into the flood or into the pit.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
porch (player, mage) --- hall (drone) --- nave (engine; flooded: puddle zone)
  |                       |
gallery ------------------+          pit (chasm): a push on the hall from the gallery
```

- **Lines:** from the porch, the hall lies between it and the nave. A push on the hall lands in the
  nave, and a flash at the nave runs through the hall. From the gallery, a push on the hall lands in
  the pit.
- **Line of sight:** porch to hall and nave; gallery to hall; hall and nave to each other.
- **Drone:** machine, dry. **Engine:** machine, heavy, wet. Both companions have 2 mana.
- **Goal:** `win`. Either neutralize each machine in turn (the pit route), or `douse(drone)` first
  (a soak, a push into the flood, or a drag into the flood), then neutralize the engine: the one bolt
  takes both.

## Hypothesis

Measured by `htn_components combos scarce_one_bolt` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 16 of 64 assignments win, i.e. 8 of the 28 pairs, whichever companion holds which half:
  - `lightningFlash` + `rainCall`, `frostBolt` (line up), + `gust`, `tidalWave` (the pit);
  - `chainLightning` + `gust`, `tidalWave`, `taunt`, `magnetize` (the flood; and the pit for the
    pushers).
- 8 methods (distinct skill sets), of three kinds: a line, a gathering, a hazard. No dead skills,
  and no plan carried by one companion.
- Every winning plan casts exactly one jolt.
- The 20 losing pairs each lose for a reason you can name:
  - two jolts: the drone is dry;
  - rain or frost with the chain: the chain on the hall takes the drone and not the engine;
  - a puller with the flash: the drone is dragged off the flash's line;
  - two non-jolts: nothing kills the engine.

## Examples

### Example 1: Line them up

**Given:** the player knows `rainCall`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** rain soaks the hall. The mage's flash from the porch at the engine runs through the hall,
and both machines short-circuit (`dead`). It is one bolt.

### Example 2: Into the flood

**Given:** the player knows `magnetize`, the mage knows `chainLightning`.

**When:** `win`

**Then:** the player wades into the nave and hooks the drone in from the hall. It arrives soaked.
One chain over the nave kills both.

### Example 3: The pit

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player goes round to the gallery, and the wave washes the drone off into the pit
(`fell`). The mage's flash kills the soaked engine.

### Example 4: Push into the flood

**Given:** the default kit: the player knows `gust`, the mage knows `chainLightning`.

**When:** `win`

**Then:** the gust from the porch drives the drone into the nave (`opForcedMove(player, drone, hall,
nave)`). One chain kills the engine and the drone.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Eight pairs win | Exactly the eight measured pairs have a plan. |
| P3 | One bolt | Every winning plan casts exactly one jolt. |
| P4 | Wrong order loses | With rain and a flash: the drone first, then the engine, has no plan. So has the engine first while the drone is dry. Rain and a chain lose. |
| P5 | Each hand matters | A pair wins whichever companion holds which half. |
