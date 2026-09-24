# The Powder Gallery

## Purpose

A hazard-terrain level where **the floor is the weapon, and a heavy blow opens it**. A siege golem
holds the nave of a ruined chapel. The gallery floor that led to it has broken away (a gap), and on
what is left of it sits a powder keg. Nobody can hurt the golem; the floor can. The golem is
`heavy` (no knockback moves it, a hook drags you to it) and a `machine`.

- **The keg** (the star): a flame or a spark (`burning`, `electrocuted`) lights its fuse, and the
  catalogue's `caveIn` - a telegraphed physical heavy blow - turns its floor into a chasm that takes
  everyone there.
- **The golem**: taunted, it walks the long way round (by the cloister) after its taunter and slams
  it (`groundSlam`: everyone in that area but the golem is stunned and knocked back). The slam stuns
  the keg too, and a stunned fuse is silenced: a keg slammed is a dud. So the keg has to go up in
  the golem's wind-up.

The player and the mage pick one skill each from a pool of eight catalogue skills.

| Method | First | Then |
|--------|-------|------|
| **Bomb it** (the keg's cave-in) | taunt it onto the keg's floor (`taunt` from the gallery) | in its wind-up, light the keg: `fireball` from the entry, `lightningFlash` into the gallery, or `blindingFlash` from a friend posted by the keg. The floor goes with the golem on it (and whoever stayed: sacrifice is allowed) |
| **Short it** (a machine) | soak it in the nave (`tidalWave`) | jolt it (`lightningFlash` from the gallery or the apse, `blindingFlash` in the nave) |
| **Drop it** (the weight off for a moment) | turn it to mist (`turnToMist`) | knock it into the open crypt or the gap (`fireball`, `vortex` on the crypt, `tidalWave` in the nave), or hook it across the gap from the gallery (`hook`) |

Why no single skill works:
- Heavy wards off every knockback; the golem is moved only by a taunt, and only walks.
- A keg lit on its own caves in an empty floor; a taunt alone brings the golem and its slam, which
  duds the keg.
- A dry jolt only stuns a machine; a wet keg steams instead of lighting.
- The mist lasts one cast.

`lightningFlash` and `blindingFlash` each serve two roles (the spark that lights the keg; the jolt
that shorts the soaked golem), and so do `fireball` and `tidalWave` (a light or a soak; the knock
that drops the misted golem).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
  entry --- gallery (keg) :gap: nave (golem; the open crypt) --- apse
    |                                                             |
    +------------------------ cloister ---------------------------+
```

- **Areas (5):** entry, gallery, nave, apse, cloister.
- **Links:** walkable entry-gallery, nave-apse-cloister-entry; a `gap` gallery-nave (the broken
  floor): dash or blink over it, fall in when knocked or hooked across.
- **Features:** `feature(nave, crypt, chasm)`.
- **Line of sight:** entry to gallery; gallery and apse to nave; cloister to apse.
- **Golem:** `heavy`, `machine`; `behavior(golem, taunted, groundSlam, source)`.
- **Keg:** an object; `behavior(keg, burning, caveIn, here)`, `behavior(keg, electrocuted, caveIn,
  here)`; `immune(keg, taunted)` (a keg does not walk).
- Both companions have 4 mana.
- **Goal** `win`: `bomb(golem, keg)` (`bringTo` the keg's floor - optionally posting a friend there
  first - then light the keg unless it already went up), `combo(wet, electrocuted, golem)`, or
  `dropIt(golem)` (mist, then `sendDown` by someone else).

## Hypothesis

Measured by `htn_components combos hazard_powder_gallery` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 18 of 64 assignments win: 9 pairs, whichever companion holds which half:
  - `taunt` plus `fireball`, `lightningFlash` or `blindingFlash`: 3 pairs (bomb);
  - `tidalWave` plus `lightningFlash` or `blindingFlash`: 2 pairs (short);
  - `turnToMist` plus `fireball`, `tidalWave`, `vortex` or `hook`: 4 pairs (drop).
- 9 methods of three kinds. No solo plans; no dead skills.
- Losses with a reason: `taunt` + `tidalWave` (the wave soaks, nothing jolts), `fireball` +
  `lightningFlash` (the keg goes up alone; the golem is only stunned), `hook` + anything but mist
  (an anchor; a keg hooked across the gap drops in).

## Examples

### Example 1: Light the keg in the wind-up

**Given:** the player knows `taunt`, the mage knows `fireball`.

**When:** `win`

**Then:** the player taunts the golem from the gallery; it walks round by the apse, the cloister and
the entry, and winds up its slam on the player. In that window the mage fireballs the gallery from
the entry: the keg's fuse is lit, the floor caves in, and the golem falls.

### Example 2: A friend by the keg

**Given:** the player knows `taunt`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the mage walks to the keg; the player taunts; in the slam's wind-up the mage flashes,
shocking the keg: the floor goes.

### Example 3: Soak, then jolt

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash` (or the other way round).

**When:** `win`

**Then:** one walks into the nave and raises a wave, soaking the golem; the other strikes the nave
with a lightning flash: the wet machine dies.

### Example 4: Mist, then hook across the gap

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the player mists the golem; the mage hooks it from the gallery, across the broken floor,
and it falls in.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Nine pairs win | Exactly the nine measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | A slammed keg is a dud | In every bomb, the keg goes up in the golem's wind-up: no winning plan has the slam land. |
| P5 | No light, no bomb | tidalWave + fireball, fireball + lightningFlash, taunt + tidalWave: no plan. |
