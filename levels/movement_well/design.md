# The Well

## Purpose

A pure-movement Lost Vikings puzzle: one companion is the weight, one goes down, one hauls out. A
lock gate opens (for good) only at the moment two plates are weighed down at once - a step by the
quay, and the floor of a well (`openWhenHeld`). The Golem is heavy: he cannot leap or be moved, so
he is the counterweight on the step, and he walks out once the lock is open. The well is seen into
from the quay and from the exit above, but from the bottom nobody can see out: whoever goes down
cannot leap back up. The player and the mage pick **one skill each** from six; the Golem knows
nothing. Victory: all three reach the exit.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Go down, be hauled out** | goes down: blinks in (`pounce`) or swaps places with the floating wisp (`translocate`) | walks to the exit and pulls the first one up (`magnetize`, `taunt`) |
| **Fetch the crate, throw it** | draws the crate out of the nook onto the brink: pulls it (`magnetize`, `taunt`) or swaps places with it (`translocate`) | throws it into the well from the quay (`gust`, `shieldBash`) |

Why no single skill wins, even held by both seats:
- a dasher or a swapper at the bottom cannot get out alone, and a swap from the exit only trades who
  is stuck;
- a puller cannot get down, and alone it only brings the crate to the brink;
- a pusher cannot reach the crate in the nook; it can throw a friend down, but then the only one
  left to haul them out is the pusher.

Every drawer (`magnetize`, `taunt`, `translocate`) plays two roles. The wisp floats: it does not
weigh the plate. `shadowStep` is left out of the pool on purpose: a friend who shadow-steps down is
stealthed, and nobody can aim a pull at them (P5).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
  nook (crate) --- quay (player, mage, golem) --- step (plate)
                    |    \
                  brink   well (plate; wisp; seen from the quay, the brink and the exit)
                    |
                  lock (door: step + well held at once) --- exit
```

- **Lines:** from the quay, what stands on the brink is thrown into the well. Nothing pushes out of
  the nook.
- **Line of sight:** the quay and the brink see the nook and the well; the exit sees the well; the
  well sees nothing.
- **Golem:** heavy, no skills. **Crate:** light, mindless. **Wisp:** a flier in the well (a swap
  target that does not weigh the plate).

## Hypothesis

Measured by `htn_components combos movement_well` (~5 s for all 42 replans; one plan < 1 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 20 of 36 assignments win: 10 unordered pairs, each in both seat orders - a pusher with a drawer (6
  pairs: the crate), and `pounce` or `translocate` with `magnetize` or `taunt` (4 pairs: down and
  up).
- 10 methods, of two kinds, and one trap (throw a friend). No dead skill; no plan carried by one
  companion.

## Examples

### Example 1: Go down and be pulled out

**Given:** the default kit (player `pounce`, mage `magnetize`).

**When:** `win`

**Then:** the player blinks into the well; the Golem steps onto the step and the lock opens; the mage
walks to the exit and hooks the player up; the Golem walks out.

### Example 2: Fetch the crate and throw it

**Given:** player `gust`, mage `taunt`.

**When:** `win`

**Then:** the mage taunts the crate out of the nook onto the brink; the player gusts it into the well.

### Example 3: Swap with the crate

**Given:** player `translocate`, mage `shieldBash`.

**When:** `win`

**Then:** the player swaps places with the crate from the brink; the mage bashes it into the well.

### Example 4: Swap with the wisp and be taunted out

**Given:** player `translocate`, mage `taunt`.

**When:** `win`

**Then:** the player swaps places with the wisp and is down the well; the mage taunts her up from the
exit.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions acting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured pairs win | Exactly the 10 measured pairs win, in both seat orders, and `combos` passes. |
| P4 | The wisp does not weigh the plate | The Golem on the step alone does not open the lock. |
| P5 | The stealthed cannot be hauled out | `shadowStep` + `magnetize` loses: the stealthed player cannot be aimed at. |
| P6 | A thrown friend is stranded | Thrown down, the mage opens the lock, but nobody can haul her out. |
