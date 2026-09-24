# The Wyvern Roost

## Purpose

A hazard-terrain level where **the enemy flies over every hazard, and the mountain can be
reshaped**. A wyvern roosts on a crag above a sheer cliff. A short chasm cuts the crag off from the
ledge; the only walkable way round is a channel of lava; on the ledge itself bubbles a lava pool.
While it flies (`flying` wards `fell`), neither the lava, the chasm nor the cliff can take it.
Its wings fail it through level-local reactions (each a `remove(flying)` plus the tag that came in):
soaked (`wet`), frosted (`chilled`), or struck (`electrocuted`).

The player and the mage pick one skill each from a pool of eight catalogue skills.

| Method | First | Then |
|--------|-------|------|
| **Fetch it, then wash it into the fire** | bring the flyer to the ledge: `hook` it over the chasm (a flyer is brought, it does not fall), or `taunt` it (it flies after you over the lava) | a wave on the ledge (`tidalWave`) soaks its wings and knocks it into the lava pool or back into the chasm |
| **Ground it, then let the mountain have it** | frost the crag (`blizzard`) or strike it (`lightningFlash`, which leaps the caster onto the crag) | knock it off the cliff or into the chasm (`fireball`, `shieldBash` across the gap, `vortex` on the cliff), or drag it over the chasm from the ledge (`hook`): grounded, it falls in |
| **Cool the lava, then wade out** | a `blizzard` on the lava channel leaves cooled rock (lava meeting an ice sheet leaves no zone) | walk out over it onto the crag, and a wave (`tidalWave`) soaks the wyvern and washes it over the cliff |

Why no single skill works:
- Flying, it is knocked over the cliff or dragged over the chasm and simply hovers.
- Grounding alone leaves it on its crag; grounded, it will not walk over the lava after a taunter.
- The crag is reached only by a leap (`lightningFlash`) or over cooled rock: a wave from the ledge
  never reaches it.

Its heavy move: taunted, it flies after its taunter and breathes fire on it (`meteor`: magic,
telegraphed, interruptible by a hook or a shield bash; the struck area catches fire). The wave
still soaks its wings through the flames.

`blizzard` serves two roles (it grounds the wyvern; it cools the lava into a road), `hook` two
(fetch the flyer; drag the grounded one into the chasm), and `tidalWave` two (the knock that also
grounds, on the ledge or on the crag).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
  camp --- ledge (lava pool) :gap: crag (wyvern; the cliff)
             \                     /
              +--- flow (lava) ---+
```

- **Areas (4):** camp, ledge, flow, crag.
- **Links:** walkable camp-ledge, ledge-flow, flow-crag; a `gap` ledge-crag (the chasm).
- **Terrain:** `onEnter(flow, lava)` - a whole-area hazard nobody walks into (the flyer crosses);
  a blizzard on it erases it (cooled rock). Features `feature(ledge, lavaPool, lava)` and
  `feature(crag, cliff, chasm)`.
- **Line of sight:** camp to ledge; ledge to crag and flow; flow to crag.
- **Wyvern:** `living`, `flying`; the three level-local reactions; `behavior(wyvern, taunted,
  meteor, source)`.
- Both companions have 4 mana.
- **Goal** `win`: `sendDown(wyvern, none)` (a knock that also grounds: the wave, after fetching it
  wherever); `ground(wyvern, ?p)` then `sendDown(wyvern, ?p)`; or `cool(?r, ?c)` then
  `sendDown(wyvern, ?c)`. Every branch ends with `confirmStopped`.

## Hypothesis

Measured by `htn_components combos hazard_wyvern_roost` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 22 of 64 assignments win: 11 pairs, whichever companion holds which half:
  - `hook` or `taunt` plus `tidalWave`: 2 pairs (fetch);
  - `blizzard` or `lightningFlash` plus `fireball`, `shieldBash`, `vortex` or `hook`: 8 pairs
    (ground);
  - `blizzard` plus `tidalWave`: 1 pair (cool).
- 11 methods of three kinds. No solo plans; no dead skills.
- Losses with a reason: two knocks (it hovers), two grounders (it stays up there), `taunt` +
  `blizzard` (grounded, it will not cross the lava), `lightningFlash` + `tidalWave` (the wave cannot
  reach the crag).

## Examples

### Example 1: Fetch it, then wash it into the lava

**Given:** the player knows `hook`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the player hooks the wyvern over the chasm onto the ledge; the mage walks up and raises a
wave: its wings soaked, it is washed into the lava pool (and the player may go in with it).

### Example 2: Cool the lava and wade out

**Given:** the player knows `blizzard`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the player freezes the lava channel into rock; the mage walks over it onto the crag and
waves the wyvern over the cliff.

### Example 3: Strike, then drag

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the mage strikes the crag and lands on it: the wyvern is grounded. The player hooks it
from the ledge; dragged over the chasm, it falls in.

### Example 4: Taunted, it flies over the lava

**Given:** the player knows `taunt`, the mage knows `tidalWave`.

**When:** `win`

**Then:** taunted from the ledge, the wyvern flies over the lava channel and breathes fire on the
player; the mage's wave soaks its wings and washes it into the lava pool.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Eleven pairs win | Exactly the eleven measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | Flying, it hovers | fireball + vortex, hook + fireball, hook + shieldBash: no plan. |
| P5 | Grounded, it stays put | taunt + blizzard and lightningFlash + tidalWave: no plan. |
