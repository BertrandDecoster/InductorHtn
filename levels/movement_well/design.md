# The Well

## Purpose

A pure-movement level on the ability layer, after The Lost Vikings: one companion is the weight,
one goes down, one hauls out. A lock gate opens only while two plates are weighed down at once: a
step on the quay, and the floor of a well. The Golem (heavy, no skills) is the counterweight on the
step, and walks out once the lock has opened. The player and the mage pick **one skill each** from
six, with mana for one costly cast each.

The well is the problem. It lies at the bottom of a shaft (a gap from the brink), its floor is
sucking mud under a hand of water (`puddle`, then `mud`: rooted), and the lock gate opens both on
the brink and, through a grate, on the well floor. Whoever lands in the well holds the plate and is
stuck there: a friend at the exit hauls them out through the open grate, or they swing out on the
Golem.

| Step | Answers |
|------|---------|
| **Down** | Leap the shaft (`lightningFlash`: one flash, no mana for the way back); or fill the shaft with the crate on the brink (`fireball`, `shieldBash`, a `tidalWave` on the brink) and walk down. |
| **Out** | A friend at the exit hooks the rooted one through the grate (`hook`); or the one below knows `hook`, and swings out on the Golem once he stands at the exit (a heavy companion is an anchor). |

Why no single skill wins, even held by both seats: nothing but a hook gets anyone out of the mud,
and a hook gets nobody down (there is no anchor in the well).

Traps:
- Whoever goes down stays there without a hook - even over a filled shaft (P4).
- The bash's shield would take the mud; the water in the well breaks it first (P5).
- The vortex has nothing to draw onto the floor: the well is empty (P6). It is the level's dead
  skill, on purpose: the obvious "suck something onto the plate" does not exist here.
- `blink` is left out of the pool: a blinker is disjoint for a moment when it lands, the mud never
  takes, and it walks out alone.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
quay (player, mage, golem; step) --- brink (crate) ~~ well (floor; puddle, mud)
                                        |              |
                                        +--- exit -----+   (both through the lock gate)
```

- **Areas:** quay, brink, well, exit (four).
- **Links:** quay–brink walkable; brink ~ well a `gap` (the shaft); brink–exit and well–exit
  `doorway`s of the same door, `lock`.
- **Plates:** `step` on the quay and `floor` in the well, both `plateFor(_, lock)` with
  `openWhenHeld(lock)`: they must be held at once; the lock then stays open.
- **Zones:** the well is `puddle` (wet) then `mud` (level-local: rooted).
- **Things:** the crate (filler) on the brink.
- **Kit:** the Golem is heavy and knows nothing; the player and the mage have mana 2 each. Default:
  player `lightningFlash`, mage `hook`.
- **Goal:** `escape` = the Golem steps on, `weighFloor` (leap down, or fill the shaft and walk
  down), the lock is open, then everyone leaves (walks, is hauled out, or swings out on the Golem).

## Hypothesis

Measured by `htn_components combos movement_well` (36 assignments in about 3 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 8 of 36 assignments win: `hook` with `lightningFlash`, `fireball`, `shieldBash` or `tidalWave`,
  each way round.
- 4 methods, and two ways out in the fill-the-shaft methods (hauled, or swinging on the Golem).
- Skill usage: hook 8, lightningFlash 2, fireball 2, shieldBash 2, tidalWave 2, vortex 0. One dead
  skill (vortex, the trap); no plan carried by one companion.

## Examples

### Example 1: Flash down and be hauled out

**Given:** the default kit (player `lightningFlash`, mage `hook`).

**When:** `win`

**Then:**
1. The Golem steps on the step.
2. The player flashes down the shaft (the mud roots him) and steps on the floor: the lock opens.
3. The Golem and the mage walk out; the mage hooks the player out through the grate.

### Example 2: Fill the shaft, and climb out on the Golem

**Given:** player `fireball`, mage `hook`.

**When:** `win`

**Then:** the fireball knocks the crate into the shaft and bridges it. Either the player walks down
and the mage hauls him out, or the mage walks down, and once the Golem stands at the exit, hooks
him and swings out.

### Example 3: Bash the crate in

**Given:** player `shieldBash`, mage `hook`.

**When:** `win`

**Then:** the bash knocks the crate into the shaft; the rest as in Example 2.

### Example 4: A wave on the brink

**Given:** player `tidalWave`, mage `hook`.

**When:** `win`

**Then:** the wave on the brink washes the crate into the shaft; the rest as in Example 2.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions casting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured pairs win | Exactly the 4 measured pairs win, both ways round; `combos` passes; the only dead skill is `vortex`. |
| P4 | Whoever goes down is stuck | `lightningFlash` + `fireball` and `fireball` + `shieldBash` lose. |
| P5 | The puddle takes the shield | A basher who walks down loses the shield to the water and is rooted by the mud. |
| P6 | The well is empty | `vortex` + `hook` loses; a vortex on the floor knocks nothing. |
