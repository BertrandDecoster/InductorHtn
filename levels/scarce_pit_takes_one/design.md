# The Pit Takes One

## Purpose

A **resource scarcity** level where the resource is **a hole in the floor**. A narrow pit runs under
a bridge and a flooded walk. A giant beetle squats on the bridge. On the walk stands a drone, a
machine that is already soaked. Both are bulky (`tag(?, filler)`). The first body that falls into
the pit fills it, and after that the pit takes nobody. The player and the mage pick one skill each
from seven.

| Enemy | What stops it |
|-------|---------------|
| beetle (`insect`) | the cold kills it (`chilled` → `dead`); the pit |
| drone (`machine`, `wet`) | any jolt (`electrocuted` on `wet` → `dead`); the pit |

| Method | The beetle | The drone |
|--------|------------|-----------|
| **Beetle in the pit** | knocked off the bridge from the ledge (`fireball`), washed in (`tidalWave`), drawn in (`vortex` on the pit), or dragged across the pit from the far side (`hook`, `taunt`) | jolted: `lightningFlash` |
| **Ice, then drop** | iced: `blizzard` on the bridge | knocked, washed or drawn off the walk into the pit: `fireball`, `tidalWave`, `vortex` |
| **No pit at all** | iced: `blizzard` | jolted: `lightningFlash` |

Why no single skill works:
- A mover can drop one body, and the pit is then full.
- The cold does nothing lasting to the drone: wet and chilled only freeze it (a stun). A jolt does
  nothing to the beetle.

The order is the puzzle whenever a kit holds a mover and a jolt. The drone is nearest the ledge,
and a push drops it at once. That is the tempting move, and it fills the pit: the beetle can then no
longer be taken. The pit belongs to the beetle. With the cold in the kit, it belongs to the drone.
The area movers are double-edged: a wave from the ledge washes *both* bodies toward the pit and a
vortex on the pit draws both, and whichever lands first fills it. The movers serve both bodies:
`fireball`, `tidalWave` and `vortex` drop the beetle in one kit and the drone in another.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
ledge (player, mage) --- bridge (beetle) --- far
  |                         |
walk (drone; flooded) ---- pit (chasm): under the bridge and the walk
```

- **Lines:** from the ledge, a push on the bridge or on the walk lands in the pit. From the far side,
  the pit lies between it and the bridge, so a pull from there drops what it drags. The pit is next
  to the bridge and the walk, so a vortex on it draws from both (nobody walks into it while it is
  live).
- **Line of sight:** ledge to bridge, walk and pit; far to bridge and pit.
- **Beetle:** `insect`, `filler`. **Drone:** `machine`, `filler`, `wet`. Both companions have 2 mana.
- **Goal:** `win`, neutralize both, in either order. The physics fills the pit: a filler that has
  fallen makes the hazard dead.

## Hypothesis

Measured by `htn_components combos scarce_pit_takes_one` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 18 of 49 assignments win, i.e. 9 of the 21 pairs, whichever companion holds which half:
  - a mover (`fireball`, `tidalWave`, `vortex`, `hook`, `taunt`) and the jolt: the beetle takes the
    pit (5 pairs);
  - the cold and a pusher (`fireball`, `tidalWave`, `vortex`): the drone takes the pit (3 pairs);
  - the cold and the jolt: nobody takes it (1 pair).
- 9 methods (distinct skill sets), of three kinds. No dead skills, and no plan carried by one
  companion.
- No plan drops two bodies into the pit.
- The 12 losing pairs:
  - two movers: the pit takes one body;
  - a puller and the cold: a puller can only drop the beetle, which the cold already killed.

## Examples

### Example 1: Beetle first

**Given:** the default kit: the player knows `fireball`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the fireball knocks the beetle off the bridge into the pit (`fell`), which fills it, and the
flash kills the soaked drone. No plan pushes the drone.

### Example 2: Pull across

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player crosses the bridge to the far side and hooks the beetle across the pit, and it
falls in. The flash kills the drone.

### Example 3: Ice, and draw the drone in

**Given:** the player knows `blizzard`, the mage knows `vortex`.

**When:** `win`

**Then:** the blizzard ices the bridge and the cold kills the beetle. The mage's vortex on the pit
draws the drone off the walk into it.

### Example 4: No pit

**Given:** the player knows `blizzard`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the ice kills the beetle, the flash kills the drone, and nothing falls.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Nine pairs win | Exactly the nine measured pairs have a plan. |
| P3 | The pit takes one | No winning plan has two falls. Two movers lose. |
| P4 | Wrong order loses | With `fireball` and `lightningFlash`: the drone into the pit first has no plan, and the beetle first has one. |
| P5 | Each hand matters | A pair wins whichever companion holds which half. |
