# The Pit Takes One

## Purpose

A **resource scarcity** level where the resource is **a hole in the floor**. A narrow pit runs under
a bridge and a flooded walk. A giant beetle squats on the bridge. On the walk stands a drone, a
machine that is already soaked. Both are bulky (`trait(?, filler)`). The first body that falls into
the pit fills it, and after that the pit takes nobody. The player and the mage pick one skill each
from eight.

| Enemy | What stops it |
|-------|---------------|
| beetle (insect) | the cold freezes it (`chilled` → `frozen`); the pit |
| drone (machine, wet) | any jolt (`electrocuted` on `wet` → `dead`); the pit |

| Method | The beetle | The drone |
|--------|------------|-----------|
| **Beetle in the pit** | pushed off the bridge from the ledge (`gust`, `tidalWave`), or dragged across the pit from the far side (`taunt`, `magnetize`) | jolted: `zap`, `chainLightning` |
| **Freeze, then drop** | frozen: `frostBolt`, `glaciate` | pushed off the walk into the pit: `gust`, `tidalWave` |
| **No pit at all** | frozen: `frostBolt`, `glaciate` | jolted: `zap`, `chainLightning` |

Why no single skill works:
- A mover can drop one body, and the pit is then full.
- The cold does nothing lasting to the drone. A jolt does nothing lasting to the beetle.

The order is the puzzle whenever a kit holds a mover and a jolt. The drone is nearest the ledge,
and a push drops it at once. That is the tempting move, and it fills the pit: the beetle can then no
longer be taken. The pit belongs to the beetle. With the cold in the kit, it belongs to the drone.
The pushers serve both bodies: `gust` and `tidalWave` drop the beetle in one kit and the drone in
another.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
ledge (player, mage) --- bridge (beetle) --- far
  |
walk (drone; flooded: puddle zone)            pit (chasm): under the bridge and the walk
```

- **Lines:** from the ledge, a push on the bridge or on the walk lands in the pit. From the far side,
  the pit lies between it and the bridge, so a pull from there drops what it drags.
- **Line of sight:** ledge to bridge and walk; far to bridge.
- **Beetle:** insect, filler. **Drone:** machine, filler, wet. Both companions have 2 mana.
- **Goal:** `win`, neutralize both, in either order. The physics fills the pit: a filler that has
  fallen makes the hazard dead.

## Hypothesis

Measured by `htn_components combos scarce_pit_takes_one` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 32 of 64 assignments win, i.e. 16 of the 28 pairs, whichever companion holds which half:
  - a mover (`gust`, `tidalWave`, `taunt`, `magnetize`) and a jolt (`zap`, `chainLightning`): the
    beetle takes the pit (8 pairs);
  - the cold (`frostBolt`, `glaciate`) and a pusher (`gust`, `tidalWave`): the drone takes the pit
    (4 pairs);
  - the cold and a jolt: nobody takes it (4 pairs).
- 16 methods (distinct skill sets), of three kinds. No dead skills, and no plan carried by one
  companion.
- No plan drops two bodies into the pit.
- The 12 losing pairs:
  - two movers: the pit takes one body;
  - two jolts: nothing stops the beetle;
  - two colds: nothing stops the drone;
  - a puller and the cold: a puller can only drop the beetle, which is already frozen.

## Examples

### Example 1: Beetle first

**Given:** the default kit: the player knows `gust`, the mage knows `zap`.

**When:** `win`

**Then:** the gust drops the beetle off the bridge into the pit (`fell`), which fills it, and the zap
kills the soaked drone. No plan pushes the drone.

### Example 2: Pull across

**Given:** the player knows `magnetize`, the mage knows `chainLightning`.

**When:** `win`

**Then:** the player crosses the bridge to the far side and hooks the beetle across the pit, and it
falls in. The chain kills the drone.

### Example 3: Freeze, and drop the drone

**Given:** the player knows `glaciate`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the ice freezes the beetle solid. The mage washes the drone off the walk into the pit.

### Example 4: No pit

**Given:** the player knows `frostBolt`, the mage knows `zap`.

**When:** `win`

**Then:** the frost freezes the beetle, the zap kills the drone, and nothing falls.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Sixteen pairs win | Exactly the sixteen measured pairs have a plan. |
| P3 | The pit takes one | No winning plan has two falls. Two pushers lose. |
| P4 | Wrong order loses | With `gust` and `zap`: the drone into the pit first has no plan, and the beetle first has one. |
| P5 | Each hand matters | A pair wins whichever companion holds which half. |
