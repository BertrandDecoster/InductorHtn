# Powder Keg

## Purpose

A **resource scarcity** level where the resource is a **reaction that can be spent**. A walled yard
holds one powder keg. A bruiser guards the keg, and a lurker waits on the stair above. Nothing the
team carries can hurt either of them. Only the keg's blast can, and the keg blows once. The player
and the mage pick one skill each from eight.

The keg goes off when it takes fire or a spark (`burning`, `electrocuted`), through a level-local
NPC behaviour. Everyone else in the yard is `blasted`, and a living enemy dies of it (a level-local
weakness). Then the keg is `spent`, which wards off fire and sparks, so nothing sets it off again.

| Method | First | Then |
|--------|-------|------|
| **Gather**: one blast takes both | bring the lurker down into the yard: push it from the landing (`gust`, `tidalWave`), drag it down from the yard (`taunt`, `magnetize`), or trade places with it (`translocate`) | light the keg: `flameWall`, `zap`, `lightningFlash` |
| **The well**: one blast, one fall | push the lurker off the stair into the well, from the yard (`gust`, `tidalWave`) | light the keg for the bruiser |

Why no single skill works:
- A mover alone kills nothing: only the blast and the well stop anyone, and the bruiser stands beside
  the keg, where no push can drop it.
- An igniter alone blasts the bruiser and leaves the lurker on the stair, untouched and out of reach.

The order is the puzzle. Lighting the keg is the obvious first move, and it spends the keg. With a
puller or a swapper, the lurker is then out of reach. Where the lurker lands depends on which side
the push comes from:
- a push from the landing drops it into the yard (gather);
- a push from the yard throws it into the well.

So `gust` and `tidalWave` each serve both methods.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage) --- yard (keg, bruiser) --- stair (lurker) --- landing
  |                                                                  |
  +------------------------------------------------------------------+
well (chasm): a push on the stair from the yard
```

- **Lines:** from the landing, a push on the stair lands in the yard. From the yard, it lands in the
  well.
- **Line of sight:** gate to yard; yard and stair to each other; landing to stair. The gate cannot
  see the stair.
- **Keg:** an object, heavy. `behavior(keg, burning|electrocuted, blast, here)`; `blast` grants
  `blasted` to everyone else in the yard, and `spent` to the keg; `wards(spent, burning|electrocuted)`.
- **Enemies:** bruiser (yard) and lurker (stair), both living: `weakness(?e, blasted, none, dead)`.
- Both companions have 2 mana (`tidalWave` and `lightningFlash` cost 2).
- **Goal:** `win`. Either `herd(lurker, yard)` then `detonate(keg)` (confirm both dead), or
  neutralize the lurker (the well) then `detonate(keg)`.

## Hypothesis

Measured by `htn_components combos scarce_powder_keg` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 30 of 64 assignments win, i.e. 15 of the 28 pairs, whichever companion holds which half. The
  winners are exactly one mover (`gust`, `tidalWave`, `taunt`, `magnetize`, `translocate`) and one
  igniter (`flameWall`, `zap`, `lightningFlash`).
- 15 methods (distinct skill sets), of two kinds: one blast for both, or the well plus the blast.
  No dead skills, and no plan carried by one companion.
- Every winning plan blows the keg exactly once.
- The 13 losing pairs are two movers (nothing lights the keg) or two igniters (nothing moves the
  lurker).

## Examples

### Example 1: Push down, then spark

**Given:** the default kit: the player knows `gust`, the mage knows `zap`.

**When:** `win`

**Then:** the player goes round to the landing and gusts the lurker down the stair into the yard.
The mage zaps the keg, and the blast kills the bruiser and the lurker.

### Example 2: Drag down, then burn

**Given:** the player knows `taunt`, the mage knows `flameWall`.

**When:** `win`

**Then:** the player walks into the yard and taunts the lurker, which is dragged down to them. The
mage sets the yard alight, and the keg blows.

### Example 3: The well

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** from the yard, the wave washes the lurker off the stair into the well (`fell`). The mage's
flash sets the keg off, and the bruiser dies.

### Example 4: Trade places

**Given:** the player knows `translocate`, the mage knows `zap`.

**When:** `win`

**Then:** the player, in the yard, swaps with the lurker: the player is on the stair and the lurker is
in the yard. The mage's zap blows the keg with both enemies beside it.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | A mover and an igniter win | Exactly the fifteen measured pairs have a plan. |
| P3 | One blast | Every winning plan sets the keg off exactly once. |
| P4 | Wrong order loses | With `taunt` and `zap`: lighting the keg first has no plan. A spent keg cannot be set off again. |
| P5 | Each hand matters | A pair wins whichever companion holds which half. |
