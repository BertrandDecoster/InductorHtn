# The Pit Takes One

## Purpose

A resource-scarcity level: **an irreversible fill**. A narrow pit in the middle of a stone crossing.
On the crossing squat a giant beetle and a drone, dripping from the sluice. Both are bulky
(`filler`): the first body that falls into the pit fills it, and after that the pit is only floor.
Two companions, one skill each, from six.

The beetle is an insect: the cold kills it, and the pit takes it. The drone is a soaked machine: a
jolt kills it, and the pit takes it too. The pit is the scarce thing - it takes one - so the team
needs one enemy's own weakness plus the pit, or both weaknesses.

| Method | Skills | How |
|--------|--------|-----|
| **Beetle in the pit** | a knocker + `lightningFlash` | jolt the drone first; then knock the beetle in: a fireball or a shield bash from the ledge, a wave on the crossing, a vortex on the pit (it draws both, and the beetle lands first) |
| **Drone in the pit** | `blizzard` + a knocker | ice the crossing: the beetle dies, the soaked drone freezes (a stun); then knock the frozen drone in |
| **No pit** | `blizzard` + `lightningFlash` | jolt the drone, then ice the beetle |

The order is the puzzle:
- **Ice before the jolt** loses: the cold freezes the soaked drone, and the freeze dries it (the
  catalogue's `freeze` removes `wet`); the jolt then only stuns.
- **Fire before the jolt** loses: the fireball's flames fill the crossing and steam the drone dry.
- **A vortex before the ice** loses: it draws both, the beetle fills the pit, and the frozen drone
  is left standing. Ice first, then the vortex takes the drone alone.

Why no single skill works:
- Two knocks: the second body finds the pit full.
- The cold alone kills the beetle and only freezes the drone; the jolt alone kills the drone and does
  nothing to the beetle.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
tower --- ledge (player, mage) --- crossing (beetle, drone; the pit) --- far
```

- **Areas and links:** four areas in a row, all walkable.
- **Features:** the pit (`chasm`) inside the crossing.
- **Line of sight:** the ledge, the tower and the far bank see the crossing.
- **Beetle:** `insect`, `filler`. **Drone:** `machine`, `filler`, `wet`.
- Both companions have 4 mana.

## Hypothesis

Measured by `htn_components combos scarce_pit_takes_one` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 18 of the 36 assignments win (9 pairs, either way round), by 9 methods of three kinds; no solo
  plans; no dead skills:
  - a knocker (fireball, tidalWave, shieldBash, vortex) + lightningFlash: 4 pairs (beetle in the pit);
  - a knocker + blizzard: 4 pairs (drone in the pit);
  - blizzard + lightningFlash: 1 pair (no pit).
- No winning plan drops two bodies; two knockers lose.
- Each knocker plays two roles: the beetle into the pit, or the frozen drone.

## Examples

### Example 1: Beetle first

**Given:** the player knows `fireball`, the mage knows `lightningFlash` (the default kit).

**When:** `win`

**Then:** the mage jolts the soaked drone (`dead`); the player's fireball knocks the beetle into the
pit (`fell`), and it fills it.

### Example 2: Freeze, then draw the drone

**Given:** the player knows `blizzard`, the mage knows `vortex`.

**When:** `win`

**Then:** the ice kills the beetle and freezes the drone; the vortex on the pit knocks the drone in.

### Example 3: No pit

**Given:** the player knows `blizzard`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the mage jolts the drone, then the player ices the crossing: the pit stays empty.

### Example 4: The vortex takes the nearer

**Given:** the player knows `vortex`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the vortex draws both; the beetle lands first and fills the pit (`opSink`); the drone is
knocked onto the full pit and stays - for the jolt.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Nine pairs win | Exactly the nine measured pairs have a plan. |
| P3 | The pit takes one | No winning plan drops two bodies; two knockers lose. |
| P4 | Ice before the jolt loses | The freeze dries the drone. |
| P5 | The vortex before the ice loses | The beetle fills the pit first. |
| P6 | Fire dries the drone | A fireball before the jolt leaves it only stunned. |
| P7 | Each hand matters | The pairs win whichever companion holds which half. |
