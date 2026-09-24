# One Bolt

## Purpose

A **resource scarcity** level: a mana budget buys exactly one jolt, and two machines have to die by
it. A sentry drone stands in the hall of a flooded chapel; beyond the flooded nave, in the apse, a
heavy pump engine squats in its own sump, already soaked. The player and the mage pick one skill each
from six. Both have 2 mana, and the one jolt in the pool, `lightningFlash`, costs 2. Whoever holds it
gets one cast.

A lightning flash strikes its target and everything on its way. The engine is wet, so the flash
kills it. The drone is dry, and a jolt only stuns it. So the one bolt has to meet a *wet* drone on
its way, or the drone has to go some other way first.

| Method | First (the partner) | Then (the one bolt) |
|--------|---------------------|---------------------|
| **Line up**: the flash runs through the hall | soak the drone where it stands: `tidalWave` | `lightningFlash` from the porch at the engine: the drone is on its path |
| **The flood**: the drone in the flooded nave, on the bolt's way | wash it in from the porch (`tidalWave`), drag it in from the nave (`hook`, `taunt`), or draw it in (`vortex` on the nave): it arrives soaked | the same flash, through the nave |
| **The pit**: the drone goes another way | knock it into the pit from the gallery: `fireball`, `tidalWave` | the flash at the engine |

Why no single skill works:
- The flash alone kills the engine and only stuns the dry drone. Both companions holding it doesn't
  help: a stunned drone is still dry.
- A soaker or a mover alone kills nothing: only a jolt stops the engine, and the heavy engine cannot
  be moved into the pit.

The order is the puzzle. Soak the drone, jolt it, then turn to the engine: that is the obvious
order, and it never works, because the bolt spent on the drone cannot reach the engine. The
drone has to be wet, on the line (or gone) before the only bolt is cast. Some skills play two roles:
- `tidalWave` soaks where it stands, washes the drone into the flood from the porch, and into the pit
  from the gallery.
- `fireball` is a push, but its fire and the flood cancel: thrown into the nave burning, the drone
  arrives dry. Its only road is the pit.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
porch (player, mage) --- hall (drone) --- nave (flooded) --- apse (engine; sump)
  |                       |
gallery ------------------+          pit (chasm): a push on the hall from the gallery
```

- **Lines:** from the porch, a push on the hall lands in the nave, and the hall and the nave lie on
  the way to the apse (a flash from the porch at the engine strikes both). From the gallery, a push
  on the hall lands in the pit.
- **Zones:** the nave and the apse are puddles (wet); the pit is a chasm.
- **Line of sight:** porch to hall, nave and apse; gallery to hall; hall and nave to each other;
  nave to apse.
- **Drone:** `machine`, dry. **Engine:** `machine`, `heavy`, `wet`. Both companions have 2 mana.
- **Goal:** `win`. Either neutralize each machine in turn (the pit route), or `douse(drone)` first
  (a soak, a wash or a vortex into the flood, or a drag into the flood), then neutralize the engine:
  the one bolt takes both.

## Hypothesis

Measured by `htn_components combos scarce_one_bolt` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 10 of 36 assignments win, i.e. 5 of the 15 pairs, whichever companion holds which half: the flash,
  plus `tidalWave`, `fireball`, `hook`, `taunt` or `vortex`.
- 5 methods (distinct skill sets), of three kinds: a line, a gathering into the flood, a hazard. No
  dead skills, and no plan carried by one companion. The flash is in every winning pair: it is the
  bolt.
- Every winning plan casts exactly one jolt.
- The losing pairs each lose for a reason you can name:
  - two flashes: the drone is dry, and a stunned drone is still dry;
  - two non-jolts: nothing kills the engine.

## Examples

### Example 1: Line them up

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player's wave soaks the drone in the hall. The mage's flash from the porch at the
engine runs through the hall, and both machines short-circuit (`dead`). It is one bolt.

### Example 2: Into the flood

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player wades into the nave and hooks the drone in from the hall. It arrives soaked.
One flash from the porch runs through the nave and kills both.

### Example 3: The pit

**Given:** the player knows `fireball`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player goes round to the gallery, and the fireball knocks the drone off into the pit
(`opForcedMove(player, drone, hall, pit)`, `fell`). The mage's flash kills the soaked engine.

### Example 4: The default kit

**Given:** the default kit: the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player's wave (from the gallery, the porch or the hall) drops, washes or soaks the
drone; the mage's one flash at the engine finishes it.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Five pairs win | Exactly the five measured pairs have a plan. |
| P3 | One bolt | Every winning plan casts exactly one jolt. |
| P4 | Wrong order loses | With a hook and the flash: the drone first has no plan; the engine first, before the drone is in the flood, has none either. |
| P5 | Each hand matters | A pair wins whichever companion holds which half. |
| P6 | Fire does not soak | With a fireball, every winning plan drops the drone in the pit: thrown into the flood burning, it arrives dry. |
