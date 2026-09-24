# The Powder Gallery

## Purpose

A hazard-terrain level where **the floor is the weapon, and a heavy blow opens it**. A siege golem
holds the nave of a ruined chapel; between it and the hall the gallery floor is cracked, and a powder
keg sits on it. Nobody can hurt the golem; the floor can. Twice over the floor gives way through the
catalogue's `caveIn` - a telegraphed physical heavy blow that turns the struck region into a chasm:

- **the keg**: a flame or a spark (`burning`, `electrocuted`) lights the fuse, and its floor caves in;
- **the golem**: taunted, it is dragged to its taunter and stamps where it stands - the floor under
  it, and under whoever stands there, caves in. The taunter must be got out in the one cast the
  wind-up allows.

The player and the mage pick one skill each from a pool of six catalogue skills.

| Method | How |
|--------|-----|
| **Lure it** (heavy attack) | taunt the golem into your own region (`taunt`); it winds up a stamp there. The friend, already standing ready, uses the window to get the taunter out: hook them away (`hook`), or blast them onto the gallery from the entry (`fireball`). The floor caves in under the golem. |
| **Open, then drop** | blow the keg where it stands - light it (`fireball`), or strike through it: a `lightningFlash` from the hall at the nave passes over the keg - then pull the golem across the new chasm from the hall (`hook`, `taunt`). |
| **Bomb to it** | bring golem and keg onto one floor - suck the golem into the gallery or the keg into the nave (`vortex`) - then blow it (`fireball`, or a `lightningFlash` through the gallery). |
| **Short it** | it is a machine: soak it from the apse (`tidalWave`), then jolt it (`lightningFlash`). |

Why no single skill works:
- A taunt alone lures the golem into stamping on the taunter, and nobody gets them out (a taunt
  provokes enemies; it does not drag a friend - `immune(?c, taunted)` for companions).
- A detonator alone opens a pit nobody delivers the golem to; a mover alone shoves it about on a
  sound floor.
- A lightning flash aimed at the keg itself dashes the caster into the pit it opens (`standing()`
  rejects the plan).

Traps: a wave that rolls the keg into the nave also wets it, and a wet keg only steams; a wave or a
vortex that pulls the taunter out of the stamp takes the golem out with it.

`taunt` serves two roles (the lure; the pull across the chasm), and so do `lightningFlash`
(a detonator through the keg; the jolt that shorts the golem) and `fireball` (a detonator; the
rescue that blasts the taunter clear).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
entry --- hall ------ gallery (keg) ------ nave (golem) --- apse
            \______________ cloister ______________________/
```

- **Walking:** entry-hall-gallery-nave-apse, hall-cloister-apse. The golem holds the nave (a
  blocker), so the apse is reached by the cloister.
- **Line of sight:** entry to hall; hall to gallery and nave; apse to nave; cloister to apse.
- **Push lines:** from the hall, the gallery's occupant rolls into the nave, and a pull from the
  hall on the nave crosses the gallery; from the entry, whoever stands in the hall is thrown onto
  the gallery. No line crosses the nave from the apse.
- **Golem:** `tag(golem, machine)`, blocker; `behavior(golem, taunted, caveIn, here)`.
- **Keg** (object): `behavior(keg, burning, caveIn, here)`, `behavior(keg, electrocuted, caveIn,
  here)`.
- Both companions have 2 mana (one fireball, tidalWave or lightningFlash).
- **Goal** `win`, with `standing()` after each: `neutralize(golem)` (the generic recipes);
  `detonate(keg), neutralize(golem)`; `together(golem, keg), detonate(keg)`; or `lure(golem)`.

## Hypothesis

Measured by `htn_components combos hazard_powder_gallery` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 16 of 36 assignments win: 8 pairs, whichever companion holds which half:
  - open, then drop: `fireball` or `lightningFlash`, plus `hook` or `taunt` (4 pairs);
  - bomb to it: `vortex` plus `fireball` or `lightningFlash` (2 pairs);
  - lure: `taunt` + `hook` (and `taunt` + `fireball`, which also opens the gallery);
  - short it: `tidalWave` + `lightningFlash`.
- 8 methods (distinct skill sets). No solo plans; no dead skills.

## Examples

### Example 1: Lure it into stamping

**Given:** the player knows `taunt`, the mage knows `hook`.

**When:** `win`

**Then:** the player taunts the golem from the hall; it is dragged there and winds up a stamp. In
the window the mage hooks the player back to the entry. The hall caves in under the golem.

### Example 2: Strike through the keg

**Given:** the player knows `lightningFlash`, the mage knows `hook`.

**When:** `win`

**Then:** the player's lightning flash from the hall at the nave passes over the keg: it blows, and
the gallery becomes a chasm (the player lands in the nave). The mage hooks the golem from the hall,
across the chasm, and it falls.

### Example 3: Bomb to it

**Given:** the player knows `vortex`, the mage knows `fireball`.

**When:** `win`

**Then:** the player's vortex on the nave draws the keg in; the mage's fireball lights it, and the
nave floor caves in under the golem.

### Example 4: Short it

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player walks round by the cloister and raises a wave from the apse that soaks the
golem; the mage jolts it from the hall and it short-circuits.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Eight pairs win | Exactly the eight measured pairs have a plan. |
| P3 | A rescue that takes the golem too | taunt + tidalWave and taunt + vortex: no plan. |
| P4 | A wet keg does not light | tidalWave + fireball: no plan. |
| P5 | Nobody falls | No winning plan drops a companion into a pit. |
