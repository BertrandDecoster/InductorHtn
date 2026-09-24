# Wet Wood

## Purpose

An elemental-chemistry level about **a reaction that dries its target** and **a reaction that spreads
fire**. A treant, rooted and rain-soaked, blocks the grove. Wood burns (`weakness: burning -> dead`),
but fire on something wet only makes steam (`steam` removes wet). Up on the ramp stands a keg of lamp
oil. The player and the mage pick one skill each from a pool of eight.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Dry, then burn** | `cleanse` strips the soak | fire (`flameWall`, `fireball`) takes the dry wood |
| **Keg, then fire or spark** | bring the keg into the grove: `gust`, `tidalWave` (push it off the ramp from the landing); `magnetize`, `taunt` (drag it in from the grove) | set it off: fire (`flameWall`, `fireball`), or a spark (`zap`). This level's reaction says sparks ignite oil: `reaction(oiled, electrocuted, blaze)` |
| **Fire, then keg** | set the grove alight (`flameWall`, `fireball`). The steam dries the treant, and the grove stays a fire zone | bring the keg in (`gust`, `tidalWave`, `magnetize`). It blazes as it arrives |

The blaze throws `burning` on everyone around the keg, and a reaction's effects apply **raw**: no
further reaction, so the soak does not save the treant. Fire on the treant does nothing lasting. Fire
on the keg does, provided the keg is next to the treant.

Why no single skill works:
- One fire only steams the treant. A second fire on the grove lands on flames already there (a
  spilled zone does not land twice), and the rooted treant never arrives anywhere new.
- Fire or a spark on the keg where it stands burns the oil off on the ramp, wasted. `fireball` does
  this even while it throws the keg into the grove: the spill comes before the push.
- A mover alone brings the keg, and nothing lights it. `cleanse` alone leaves dry wood unburnt.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
ridge ---- glade (player, mage) ---- grove (treant: wooden, heavy, wet) ---- hollow
             |                         |
           landing ---------------- ramp (keg: oiled)
```

- **Walking:** glade–grove, glade–landing, landing–ramp, ramp–grove, glade–ridge, grove–hollow.
- **Line of sight:** glade→grove, ridge→grove, landing→ramp, grove→ramp.
- **Push line:** from the landing, the ramp tips into the grove.
- **Treant:** wooden, heavy (rooted: nothing moves it), wet.
- **Keg:** oiled, light.
- **Level physics:** `reaction(oiled, electrocuted, blaze)`: a spark sets oil off.
- **Level recipes:** `dryAndBurn` (strip the soak, then fire, by two companions) and `blazeBeside`
  (bring the fuel in and set it off, or set the region alight and bring the fuel in, by two
  companions). The generic `neutralize` is tried too. It finds nothing, because fire on the wet
  treant only steams it.
- **Taunt's drag is raw.** `onGrant(taunted, pull)` moves the keg in raw mode, so a taunted keg dragged
  into a grove that is already burning takes the fire without the blaze. With taunt, only the "keg
  first, then fire or spark" order wins. That makes the level harder, never easier.

## Hypothesis

Measured with `htn_components combos chem_wetwood`:

- No single skill wins, even when both companions hold it: 0 of 8.
- **28 of 64** assignments win (14 unordered pairs, in either seat). There are **14 methods** of
  three kinds, and no dead skills:
  - dry, then burn: `cleanse` x {flameWall, fireball}, 2 pairs;
  - keg and fire: {flameWall, fireball} x {gust, magnetize, tidalWave, taunt}, 8 pairs (both orders
    for gust, tidalWave and magnetize);
  - keg and spark: `zap` x {gust, magnetize, tidalWave, taunt}, 4 pairs.
- Skill usage: flameWall 10, fireball 10, zap 8, gust 6, magnetize 6, tidalWave 6, taunt 6,
  cleanse 4.
- Losing pairs, each for a named reason: two fires (steam, then a zone that relights nothing), fire
  and a spark (both waste the keg on the ramp, or steam the treant), two movers or cleanse and a
  mover (nothing lights anything), zap and cleanse (a spark does nothing to dry wood).
- Every winning pair needs something that makes fire, or a spark. A fire-and-keg plan can also be
  played in two orders.

## Examples

### Example 1: Dry, then burn

**Given:** the player knows `cleanse`, the mage knows `flameWall`.

**When:** `win`

**Then:** the player cleanses the soak off the treant. The mage's flame wall sets the grove alight,
and the dry wood burns (`dead`).

### Example 2: Keg, then spark

**Given:** the player knows `gust`, the mage knows `zap`.

**When:** `win`

**Then:** the player walks to the landing and blows the keg off the ramp into the grove. The mage's
jolt sets the oil off (`blaze`). The blaze sets the treant alight through its soak (`dead`).

### Example 3: Fire, then keg

**Given:** the player knows `flameWall`, the mage knows `gust`.

**When:** `win`

**Then:** one plan sets the grove alight first. The steam dries the treant, and the grove stays a fire
zone. The keg is blown in afterwards and blazes as it arrives.

### Example 4: Wet wood only steams

**Given:** the player knows `flameWall`, the mage knows `fireball`.

**When:** `win`

**Then:** no plan. The first fire steams the treant dry, and the second lands on flames already there.
Fireball on the keg burns its oil off before throwing it into the grove.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Fourteen pairs win | Exactly the fourteen measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | The blaze is raw | In the spark method nothing dries the treant, and it still burns: the blaze's fire skips the steam reaction. |
