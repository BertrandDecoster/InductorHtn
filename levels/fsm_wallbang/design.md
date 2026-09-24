# Wall-Bang

## Purpose

An enemy-state-machine level in the Monster Hunter wall-bang style. The Ram is a boss: heavy, so
nothing moves it, and immune to hard control. It has one telegraphed reaction: **taunted, it charges
its taunter** (it dashes to where the taunter stands). A stone pillar stands at the brink of a
ravine. A charge that ends there crashes into it, and the Ram is **staggered**. Staggered is its
vulnerability window, and it opens two ways to win:

| Method | First (the lure) | Then (the finisher, the other companion) |
|--------|------------------|------------------------------------------|
| **Bang and drop** (staggered, its footing lapses) | `taunt` or `provoke`, cast from the brink | throw it into the ravine from the arena or the gallery: `gust`, `tidalWave`, `concuss` |
| **Bang and shock** (staggered, its heart is open) | `taunt` or `provoke`, cast from the brink | jolt it: `zap`, `chainLightning` |

The state machine is only tags: `taunted` → behaviour `ramCharge` (a dash to the source) → arrival
at the brink meets the pillar, a hazard only the Ram is weak to → `staggered`, which suspends its
immunity to forced movement and makes `electrocuted` lethal.

Why no single skill works:
- A lure alone leaves a staggered Ram standing.
- A push, a pull or a jolt before the crash does nothing: it is heavy, and a jolted living thing
  only seizes up.
- The lure has to be cast from the brink. From anywhere else, the Ram charges to you and nothing
  happens.

Traps: `tidalWave` and `chainLightning` hit everyone at the brink, so the taunter is thrown into the
ravine along with the Ram, or shocked next to it. The plan still wins, at that cost.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
pen (player, mage) --- arena (Ram) --- brink (pillar)
                         |               :
                      gallery          ravine (chasm, below the brink)
                         |
                       crag
```

- **Lines:** a push from the arena or the gallery on the brink lands in the ravine.
- **Line of sight:** pen and arena see each other; the arena and the brink see each other; the
  gallery sees the arena and the brink.
- **The pillar:** `onEnter(brink, pillarCrash)`, a hazard `pillar`. Only the Ram has a weakness to it
  (`weakness(ram, pillar, none, staggered)`), so companions walk the brink safely.
- **Ram:** boss, living, heavy. `behavior(ram, taunted, ramCharge, source)`, `ramCharge` = `dash`.
  `suspends(staggered, forcedMove)`, `weakness(ram, electrocuted, staggered, dead)`.
- **Goal:** `win` is either the standard `neutralize(ram)` (it finds nothing while the Ram stands
  firm), or the level's own stages: a lurer casts from the crash site, the Ram must be staggered, then
  someone else finishes it (`sendInto` the ravine, or the weakness that needs `staggered`).
- Both companions have 4 mana.

## Hypothesis

Measured with `htn_components combos fsm_wallbang` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 20 of 49 assignments win: 10 pairs, each whichever companion holds which half. Every pair is
  one lure (`taunt`, `provoke`) plus one finisher (`gust`, `tidalWave`, `concuss`, `zap`,
  `chainLightning`).
- 10 methods (distinct sets of skills cast), 0 solo plans, no dead skills.
- The other 11 pairs lose, each for a nameable reason: two lures (it staggers, nobody finishes), two
  finishers (it never staggers).

## Examples

### Example 1: Bang, then throw

**Given:** the player knows `taunt`, the mage knows `gust`.

**When:** `win`

**Then:** the player walks to the brink and taunts the Ram; it charges, crashes into the pillar and
is staggered; the mage's gust from the arena throws it into the ravine (`fell`).

### Example 2: Bang, then shock

**Given:** the player knows `zap`, the mage knows `provoke`.

**When:** `win`

**Then:** the mage provokes the Ram from the brink; it charges into the pillar; the player's zap
stops its open heart (`dead`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the ten lure-and-finisher pairs have a plan. |
| P3 | The crash is the key | Every winning plan staggers the Ram at the pillar first. |
| P4 | Each hand matters | A pair wins whichever companion holds which half. |
