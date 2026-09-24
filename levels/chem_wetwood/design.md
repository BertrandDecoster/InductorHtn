# Wet Wood

## Purpose

An elemental-chemistry level about **a reaction that dries its target**, **a reaction that spreads
fire**, and **terrain that burns up**. A treant, heavy and rain-soaked, holds the grove. Wood burns
(catalogue: `wooden`, `burning -> dead`), but fire on something wet only makes steam (`steam` removes
wet). Up on the ramp, in a spill of lamp oil (a `slick` zone), stands a keg; at the grove's edge glows
the charcoal-burners' kiln (a feature: what is knocked in burns). An oiled thing set alight blazes
(`blaze`): fire on everyone in its area, applied raw, so the soak does not save the treant. This level
adds one reaction: sparks set oil off (`reaction(oiled, electrocuted, blaze)`). The player and the
mage pick one skill each from a pool of seven.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Keg to the tree** | `hook` the keg down off the ramp into the grove | set it off: `fireball`, a spark (`lightningFlash`, `blindingFlash`), or a `vortex` on the kiln that knocks the keg in. Or the grove alight first (`fireball`), and the keg hooked into the flames |
| **Tree to the oil** | `taunt` from the ramp: the treant walks through the slick and comes out oiled, beside the keg | fire or a spark on the ramp: the keg and the oil on it go up (`fireball`, `lightningFlash`, `blindingFlash`) |
| **Into the kiln** | `turnToMist`: for a moment it is not heavy | `fireball` it: the flames dry it (steam) and the blast knocks it into the kiln, where it burns |

Why no single skill works:
- Fire on the treant alone only steams it; a second fire on the grove lands on flames already there.
- A hook or a taunt only brings the fuel and the wood together; nothing lights it.
- A spark on the keg where it stands, or on the treant alone, burns nothing near it.

Skills in two roles: `fireball` is a match in two methods and a blast into the kiln in the third;
`hook` brings the keg, and `taunt` brings the tree - the two halves of the same meeting; `vortex` is
the one knock that sends the keg into the kiln.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
glade (player, mage) ---- grove (treant; kiln)
  |                         |
landing --------------- ramp (slick; keg)
```

- **Areas:** 4. **Links:** all walkable: glade-grove, grove-ramp, glade-landing, landing-ramp.
- **Line of sight:** glade->grove, landing->ramp, ramp->grove, grove->ramp.
- **Features:** `kiln` in the grove (`flames`: what is knocked in burns).
- **Zones:** ramp `slick` (whoever enters is oiled).
- **Treant:** `wooden`, `heavy`, `wet`. **Keg:** an object, `oiled`, immune to `taunted` (it does not
  walk). Both companions have 4 mana.
- **Level recipes:** `blazeBeside` (bring the fuel into the treant's area with `placeAs`, then set it
  off - fire, a spark, or `knockOn` into the kiln - or set the area alight first and bring the fuel
  into the flames), `lureOntoOil` (taunt it onto the slick, then set it off), and `intoTheKiln`
  (mist, then knock it into the fire).
- **Heavy attack:** none. **Terrain use:** the kiln feature (knock target), the slick zone (a lure
  oils), and a zone reaction (slick + flames = flames: fire on the ramp wastes the oil).

## Hypothesis

Measured with `htn_components combos chem_wetwood`:

- No single skill wins, even when both companions hold it: 0 of 7.
- **16 of 49** assignments win (8 unordered pairs, in either seat). **8 methods** of three kinds, no
  solo plans, no dead skills:
  - keg to the tree: hook x {fireball, lightningFlash, blindingFlash, vortex};
  - tree to the oil: taunt x {fireball, lightningFlash, blindingFlash};
  - into the kiln: turnToMist x fireball.
- Skill usage: hook 8, fireball 6, taunt 6, lightningFlash 4, blindingFlash 4, vortex 2,
  turnToMist 2.
- Losing pairs, each for a named reason: two fires or fire and a spark (steam, then flames already
  there; the keg blown up on the ramp), hook + taunt (nothing lights it), taunt + vortex (no feature
  on the ramp), mist with a vortex (knocked into the kiln wet: steam), mist with a spark or a hook.

## Examples

### Example 1: Hook the keg, then fire

**Given:** the player knows `hook`, the mage knows `fireball`.

**When:** `win`

**Then:** the player walks into the grove and hooks the keg down off the ramp. The mage's fireball
sets the grove alight: the treant only steams, but the keg blazes (`blaze`), and the blaze's raw fire
burns the treant (`dead`).

### Example 2: Fire, then keg

**Given:** the player knows `hook`, the mage knows `fireball`.

**When:** `win` (another plan)

**Then:** the mage sets the grove alight first. The steam dries the treant, and the grove stays a fire
zone. The keg is hooked in afterwards and blazes as it arrives.

### Example 3: Hook, then vortex into the kiln

**Given:** the player knows `hook`, the mage knows `vortex`.

**When:** `win`

**Then:** the player hooks the keg into the grove. The mage's vortex on the kiln knocks everything
movable in the grove into it - the keg (and the player): the keg blazes and the treant burns.

### Example 4: Lure it onto the oil, then spark

**Given:** the player knows `taunt`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player walks onto the ramp and taunts the treant; it walks after the player through the
slick and comes out oiled. The mage's lightning flash strikes the ramp: the keg's oil goes up, and the
blaze burns the treant.

### Example 5: Mist, then into the kiln

**Given:** the player knows `turnToMist`, the mage knows `fireball`.

**When:** `win`

**Then:** the player turns the treant to mist. The mage's fireball dries it (steam) and blows it into
the kiln, where it burns (`dead`).

### Example 6: Wet wood only steams

**Given:** both companions know `fireball`.

**When:** `win`

**Then:** no plan. The first fire steams the treant dry, and the second lands on flames already there.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Eight pairs win, in either hand | Exactly the eight measured pairs have a plan, whichever companion holds which half. |
| P3 | Fire on the ramp wastes the oil | Fireball on the keg where it stands: slick + flames = flames, the keg blazes on the ramp; lured through the flames later, the treant only steams. |
| P4 | The kiln needs a dry treant | Mist with a vortex: knocked into the kiln wet, it only steams. |
| P5 | The keg does not walk | A taunt does nothing to the keg: only a hook brings it. |
