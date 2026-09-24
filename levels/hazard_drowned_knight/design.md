# The Drowned Knight

## Purpose

A hazard-terrain level where **the enemy's own weight is the puzzle**. A knight in full plate holds a
keep on a spit of rock: on one side the keep drops into a moat (a chasm), and below the quay wall
lies a deep lake. Nobody can hurt the knight; the terrain can. The knight is `heavy`, which cuts both
ways - it wards off every push and pull, and the catalogue sinks the heavy in deep water. The player
and the mage pick one skill each from a pool of six catalogue skills.

| Method | First | Then |
|--------|-------|------|
| **Drown it** (keep it heavy, make it move itself) | a friend puts the baiter in the lake: washed off the quay (`tidalWave`), blasted off it (`fireball`), or sucked down (`vortex` on the lake) | the baiter taunts the knight from the water (`taunt`): it leaps in after them (a dash) and sinks |
| **Drop it** (take the weight off for a moment) | turn it to mist (`turnToMist`): through the next cast it is not heavy | that next cast moves it: blasted or washed off the keep into the moat from the causeway (`fireball`, `tidalWave`), sucked into the moat (`vortex`), or pulled across it from the tower (`hook`, `taunt`) |

Why no single skill works:
- Heavy wards off forced movement, and a misted knight no longer drowns.
- A knight taunted from dry land just leaps over to its taunter: a leap never falls.
- Nobody can walk down to the lake (the quay wall is a door that never opens); the only way in is
  to be put there by a friend.
- Hooked while heavy, the knight is an anchor: the hook drags the hooker onto the keep instead.

`taunt` serves two roles (the bait from the water; a pull across the moat), and so do `tidalWave`,
`fireball` and `vortex` (put a friend in the lake; move the misted knight into the moat).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate --- quay --- causeway --- keep (knight) --- moat
 |        :                      :
tower    lake (below the wall; no way down but a fall)
```

- **Walking:** gate-quay-causeway-keep, gate-tower. The knight holds the keep (a blocker). The lake
  is next to the quay and the moat next to the keep (a vortex draws from there), but the lake is a
  `door` that never opens and the moat is a chasm, so nobody walks in.
- **Line of sight:** gate to quay and lake; causeway and tower to keep and moat; lake to keep.
- **Push lines:** from the gate, whoever stands on the quay goes into the lake; from the causeway,
  the keep's occupant goes into the moat; a pull from the tower crosses the moat.
- **Zones:** the lake is `deepWater`, the moat is `chasm`.
- **Knight:** `tag(knight, heavy)`, `tag(knight, living)`, blocker. The catalogue's
  `weakness(?e, deepWater, none, fell) :- has(?e, heavy)` sinks it.
  `behavior(knight, taunted, lunge, source)` with the level-local `effect(lunge, target, dash)`:
  taunted, it leaps at its taunter (a dash, which no weight stops).
- Both companions have 2 mana (one tidalWave or fireball).
- **Goal** `win`: `neutralize(knight)` (the catalogue's mist-then-push recipe), or `bait(knight)`:
  a companion is put into water that drowns the knight, then taunts it from there. Either way,
  `standing()`: no companion is lost.

## Hypothesis

Measured by `htn_components combos hazard_drowned_knight` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 16 of 36 assignments win: 8 pairs, whichever companion holds which half:
  - `turnToMist` plus `fireball`, `tidalWave`, `vortex`, `hook` or `taunt`: 5 pairs;
  - `taunt` plus `tidalWave`, `fireball` or `vortex`: 3 pairs.
- 8 methods (distinct skill sets) of two opposite kinds. No solo plans; no dead skills.
- Every loss has a nameable reason: a mover without mist (heavy holds), a taunt without a friend to
  put the taunter in the water (it just leaps over), `hook` with anything but mist (an anchor pulls
  the hooker in), two movers (nothing lightens it).

## Examples

### Example 1: Bait it from the water

**Given:** the player knows `tidalWave`, the mage knows `taunt`.

**When:** `win`

**Then:** the mage walks onto the quay and the player's wave washes them over the wall into the
lake; the mage taunts the knight from the water, it leaps in after them and sinks.

### Example 2: A vortex in the lake

**Given:** the player knows `vortex`, the mage knows `taunt`.

**When:** `win`

**Then:** the player casts a vortex on the lake, which sucks the mage down off the quay; the mage
taunts, the knight leaps in and sinks.

### Example 3: Mist, then push

**Given:** the player knows `turnToMist`, the mage knows `fireball`.

**When:** `win`

**Then:** the player turns the knight to mist from the causeway; with the next cast the mage's
fireball blasts it off the keep into the moat.

### Example 4: Mist, then pull across

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the player mists the knight; the mage hooks it from the tower, and it is dragged across
the moat and falls.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Eight pairs win | Exactly the eight measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | Misted, it does not drown | turnToMist + tidalWave: no winning plan uses the lake. |
| P5 | Heavy, it cannot be moved | hook + tidalWave and hook + taunt: no plan. |
