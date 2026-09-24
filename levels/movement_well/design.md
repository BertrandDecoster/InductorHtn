# The Well

## Purpose

A pure-movement Lost Vikings puzzle: one companion is the weight, one goes down, one hauls out.

- **The lock:** a lock gate opens for good only at the moment two plates are weighed down at once
  (`openWhenHeld`): a step by the quay, and the floor of a well.
- **The Golem:** heavy, so he cannot leap or be moved. He is the counterweight on the step, and he
  walks out once the lock is open.
- **The well:** barred. Nobody walks down or up. It is seen into from the quay, the brink and the
  exit above, but from the bottom nobody can see out, so whoever goes down cannot leap back up.
- **The seats:** the player and the mage pick **one skill each** from six; the Golem knows nothing.
- **Victory:** all three reach the exit.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Go down, be hauled out** | flashes down (`lightningFlash`) | walks to the exit and pulls the first one up (`hook`, `taunt`) |
| **Fetch the crate, send it down** | draws the crate out of the niche onto the brink (`hook`, `taunt`: nothing but a pull reaches it), and steps back | throws it into the well from the quay (`fireball`, `tidalWave`), or sucks the brink into the well (`vortex`) |

Why no single skill wins, even held by both seats:
- a flasher at the bottom cannot get out alone;
- a puller cannot get down, and alone it only brings the crate to the brink;
- a pusher or a vortex cannot reach the crate in the niche. It can send a friend down, but then the
  only one left to haul them out is the one who sent them.

Both pullers play two roles: fetch the crate, haul a friend out.

Traps:
- A wave or a vortex takes whoever still stands on the brink down the well with the crate.
- The wisp in the well floats, so it does not weigh the plate.
- `blink` is left out of the pool on purpose. A friend who blinks down is disjoint for a moment,
  and the pull right after it misses (P5).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
  nook (crate; a niche up the wall)
    :
  quay (player, mage, golem) --- step (plate)
    |
  brink ...> well (plate; wisp; barred)
    |
  lock (door: step + well held at once) --- exit
```

- **Walking:**
  - quay–step, quay–brink, brink–lock, lock–exit.
  - The brink gives onto the well one way only, so a vortex on the well draws the brink in. The
    well is a door that never opens: nobody walks in, and nothing leads out.
  - The nook is connected to nothing.
- **Lines:** from the quay, what stands on the brink is thrown into the well.
- **Line of sight:** the quay and the brink see the nook and the well; the exit sees the well; the
  well sees nothing.
- **Golem:** heavy, no skills. **Crate:** light. **Wisp:** flying, in the well (does not weigh the
  plate).
- **Mana:** 4 each. **Default kit:** player `lightningFlash`, mage `hook`.

## Hypothesis

Measured by `htn_components combos movement_well` (36 replans in about 3 s; each plan is under
1 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 16 of 36 assignments win, 8 pairs each way round:
  - {`hook`, `taunt`} + {`fireball`, `tidalWave`, `vortex`} (the crate);
  - `lightningFlash` + {`hook`, `taunt`} (go down, be hauled out).
- 8 methods (sets of skills cast), of two kinds.
- Skill usage: hook 8, taunt 8, vortex 4, fireball 4, tidalWave 4, lightningFlash 4. No dead skill;
  no plan carried by one companion.

## Examples

### Example 1: Go down and be pulled out

**Given:** the default kit (player `lightningFlash`, mage `hook`).

**When:** `win`

**Then:**
1. The player flashes down the well.
2. The Golem steps onto the step, and the lock opens.
3. The mage walks to the exit and hooks the player up.
4. Everyone walks out.

### Example 2: Fetch the crate and throw it

**Given:** player `taunt`, mage `tidalWave`.

**When:** `win`

**Then:** the player taunts the crate onto the brink and steps back; the mage's wave from the quay
throws it into the well.

### Example 3: Hook the crate and suck it down

**Given:** player `hook`, mage `vortex`.

**When:** `win`

**Then:** the player hooks the crate onto the brink and steps back; the mage's vortex on the well
sucks it down.

### Example 4: Flash down and be taunted out

**Given:** player `lightningFlash`, mage `taunt`.

**When:** `win`

**Then:** the player flashes down; from the exit, the mage's taunt drags her up.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions acting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured assignments win | Exactly the 8 measured pairs win, both ways round; `combos` passes; no dead skill. |
| P4 | The wisp does not weigh the plate | The Golem on the step alone does not open the lock. |
| P5 | A blinker is disjoint for a moment | `blink` + `hook` loses: the hook right after the blink cannot aim at the player. |
| P6 | A thrown friend is stranded | The fireball throws the mage down and the lock opens, but nobody hauls her out. |
