# The Drowned Knight

## Purpose

A hazard-terrain level where **the enemy's own weight is the puzzle**. A knight in full plate holds a
keep on a spit of rock: the moat (a pit) runs at the keep's foot, and a short drop separates the keep
from the old tower. Between the gate and the causeway lies a dry lock basin; behind the gatehouse
wall, the sluice that floods it. Nobody can hurt the knight; the water and the drop can. The knight
is `heavy`, which cuts both ways - no knockback moves it and no hook drags it, and in deep water the
heavy sink. The player and the mage pick one skill each from a pool of eight catalogue skills.

| Method | First | Then |
|--------|-------|------|
| **Drown it** (keep it heavy, make it walk) | taunt it from the lock (`taunt`): the only thing that moves it is its own feet, after its taunter | open the sluice: knock the counterweight onto the plate (`fireball` from the gate, `shieldBash` across the gap from the lock, `vortex` on the plate), or leap in and step on it (`blink` through the wall, `lightningFlash` over the gap). The lock floods with deep water and the knight sinks |
| **Drop it** (take the weight off for a moment) | turn it to mist (`turnToMist`): through the next cast it is not heavy | that next cast knocks it into the moat or the drop by the tower (`fireball`, `shieldBash`, `vortex` on the moat), or hooks it across the drop from the tower (`hook`: it falls in) |

Why no single skill works:
- Heavy wards off forced movement; a taunt only walks it about, and the flood only drowns what
  stands in the lock.
- Nobody walks to the sluice (a wall and a gap): opening it takes a knock from outside or a leap.
- The mist lasts one cast, and a misted knight no longer drowns.
- Hooked while heavy, the knight is an anchor: the hook drags the hooker onto the keep instead.

Its heavy move: taunted, the knight walks up to its taunter and slams (`groundSlam`, physical,
telegraphed): everyone in the lock but the knight is stunned and knocked back (into the gap to the
sluice, possibly). The team may answer in the wind-up with one cast: open the sluice then and the
knight sinks before the blow lands. A friend waiting in the lock is caught by the slam too.

`fireball`, `shieldBash` and `vortex` each serve two roles: they open the sluice (the counterweight
onto the plate) in the drowning, and knock the misted knight down in the drop.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
            sluice (plate, counterweight)
           #wall      :gap
  tower --- gate --- lock --- causeway --- keep (knight; the moat)
    :                                        :
    :................... gap ................:
```

- **Areas (6):** gate, lock, causeway, keep, tower, sluice.
- **Links:** walkable gate-lock-causeway-keep and gate-tower; a `gap` tower-keep (the drop) and
  lock-sluice; a `wall` gate-sluice (only a blink goes through).
- **Features:** `feature(keep, moat, chasm)`; `feature(sluice, sluiceGate, flood)` with
  `plate(sluiceGate)` and `effect(flood, target, spill(deepWater, lock))`: pressed, the lock fills
  with deep water and everyone in it takes it.
- **Line of sight:** gate to lock and sluice; lock to sluice and keep; causeway and tower to keep.
- **Knight:** `heavy`, `living`; `behavior(knight, taunted, groundSlam, source)`.
- **Counterweight:** an object in the sluice area.
- Both companions have 4 mana.
- **Goal** `win`: `drown(knight)` (bring it into the lock with `bringTo`, then open the sluice unless
  it was opened in the wind-up) or `dropIt(knight)` (mist, then `sendDown` by someone else).
  Sacrifice is allowed: a companion knocked into the gap by the slam is lost, and the plan still wins.

## Hypothesis

Measured by `htn_components combos hazard_drowned_knight` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 18 of 64 assignments win: 9 pairs, whichever companion holds which half:
  - `taunt` plus `fireball`, `shieldBash`, `vortex`, `blink` or `lightningFlash`: 5 pairs;
  - `turnToMist` plus `fireball`, `shieldBash`, `vortex` or `hook`: 4 pairs.
- 9 methods (distinct skill sets) of two opposite kinds. No solo plans; no dead skills.
- Every loss has a nameable reason: a mover without mist (heavy holds), a taunt with nothing that
  opens the sluice, the sluice opened with nobody luring the knight, `hook` with anything but mist
  (an anchor pulls the hooker in), mist with a leaper (nothing knocks it).

## Examples

### Example 1: Lure, then knock the counterweight

**Given:** the player knows `taunt`, the mage knows `fireball`.

**When:** `win`

**Then:** the player taunts the knight from the lock; it walks in by the causeway. The mage's
fireball knocks the counterweight onto the sluice; the lock floods and the knight sinks.

### Example 2: A blink through the wall

**Given:** the player knows `taunt`, the mage knows `blink`.

**When:** `win`

**Then:** with the knight in the lock, the mage blinks through the gatehouse wall and steps on the
sluice.

### Example 3: Mist, then hook across the drop

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the player mists the knight from the lock; the mage hooks it from the tower, across the
drop, and it falls in.

### Example 4: Open the sluice in the wind-up

**Given:** the player knows `taunt`, the mage knows `fireball`.

**When:** `win`

**Then:** in one plan, the knight reaches the lock and winds up its slam on the player; in that
window the mage fireballs the counterweight onto the sluice, the knight sinks, and the blow misses.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Nine pairs win | Exactly the nine measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | Misted, it does not drown | turnToMist + fireball: no winning plan uses deep water. |
| P5 | Heavy, it cannot be moved | hook + fireball and hook + taunt: no plan. |
| P6 | The flood needs the knight in the lock | In every drowning the lock floods after the knight walked in. |
