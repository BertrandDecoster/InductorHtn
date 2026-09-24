# The Powder Gallery

## Purpose

A hazard-terrain level where **the level does the killing and the players deliver**. A siege golem
holds the nave of a ruined chapel. Between the hall and the nave the gallery floor is cracked, and a
powder keg sits on it. Nobody can hurt the golem. The keg can: when it catches fire or a spark it
blows, and the floor it stands on drops into a chasm. The player and the mage pick one skill each
from a pool of eight.

| Method | First | Then |
|--------|-------|------|
| **Open, then drop** | blow the keg where it stands (`flameWall`, `zap`): the gallery becomes a chasm | pull the golem across it from the hall (`magnetize`, `taunt`), or push it in from the apse (`gust`, `shieldBash`, `tidalWave`) |
| **Floor under it** | push the golem onto the powder floor from the apse (`gust`, `shieldBash`, `tidalWave`) | blow the keg: floor, keg and golem go down together |
| **Bomb to it** | push the keg from the hall into the nave (`gust`, `shieldBash`, `tidalWave`) | blow it there: the nave floor goes, and the golem with it |
| **Short it** (not a hazard) | soak the machine (`rainCall`, `tidalWave`) | jolt it (`zap`) |

Why no single skill works:
- A detonator alone opens a pit that nobody delivers the golem to.
- A mover alone shoves the golem or the keg about on a sound floor.
- A jolt on a dry machine only stuns it.
- The golem holds the nave (a blocker), so the apse is reached by the cloister.

Several skills serve two roles: `zap` is a detonator and the jolt; `tidalWave` pushes the golem or
the keg, and soaks the machine; `gust` and `shieldBash` move either the golem or the keg.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
entry --- hall ------ gallery (keg) ------ nave (golem) --- apse
            \______________ cloister _____________________/
```

- **Walking:** entry-hall, hall-gallery, gallery-nave, nave-apse, hall-cloister-apse. Nobody walks
  into the nave while the golem holds it.
- **Line of sight:** the hall sees the gallery and the nave; the apse sees the nave.
- **Push lines:** from the apse, the nave's occupant lands on the gallery; from the hall, the
  gallery's occupant lands in the nave, and a pull from the hall on the nave crosses the gallery.
- **The keg** (level-local): `behavior(keg, burning, blast, here)` and
  `behavior(keg, electrocuted, blast, here)`, with `effect(blast, target, spill(chasm))`. The keg
  falls with its floor. A wet keg does not light (the catalogue's steam reaction).
- **Golem:** machine, blocker. Both companions have 2 mana (one tidalWave).
- **Goal** `win`: `neutralize(golem)`; or `detonate(keg)` then `neutralize(golem)`; or
  `together(golem, keg)` (push one onto the other's floor) then `detonate(keg)`.

## Hypothesis

Measured by `htn_components combos hazard_powder_gallery` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 22 of 64 assignments win: 11 pairs, whichever companion holds which half:
  - `flameWall` plus `gust`, `magnetize`, `taunt`, `shieldBash` or `tidalWave`: 5 pairs;
  - `zap` plus `gust`, `magnetize`, `taunt`, `shieldBash` or `tidalWave`: 5 pairs;
  - `rainCall` plus `zap`: 1 pair (and `tidalWave` + `zap` also wins this way).
- 11 methods (distinct skill sets), of four kinds (above). No solo plans; no dead skills.
- Every loss has a nameable reason: two movers (nothing opens the floor), two detonators or a
  detonator and `rainCall` (nothing delivers the golem), a mover and `rainCall` (nothing lights or
  jolts).

## Examples

### Example 1: Open, then pull across

**Given:** the player knows `zap`, the mage knows `taunt`.

**When:** `win`

**Then:** the player zaps the keg, which blows the gallery into a chasm; the mage taunts the golem
from the hall and it is dragged across the gallery and falls.

### Example 2: The floor under it

**Given:** the player knows `flameWall`, the mage knows `gust`.

**When:** `win`

**Then:** the mage walks round by the cloister and gusts the golem from the apse onto the powder
floor; the player sets the gallery alight, the keg blows, and golem and keg go down together.

### Example 3: The bomb to it

**Given:** the player knows `flameWall`, the mage knows `gust`.

**When:** `win`

**Then:** the mage gusts the keg from the hall into the nave; the player's flameWall lights it
there, and the nave floor drops out from under the golem.

### Example 4: Short it

**Given:** the player knows `rainCall`, the mage knows `zap`.

**When:** `win`

**Then:** the rain soaks the golem; the jolt short-circuits it (`dead`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Eleven pairs win | Exactly the eleven measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | The default kit wins three ways | flameWall + gust: open then drop, the floor under it, the bomb to it. |
